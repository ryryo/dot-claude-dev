#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile


AGENTS = (
    "poteto-agent",
    "comment-sicko",
    "pstack_skeptic",
    "pstack_architect",
    "pstack_minimalist",
    "thermos_correctness",
    "thermos_quality",
)


def default_repo() -> Path:
    return Path(__file__).resolve().parents[2]


def probe_prompt(agent: str) -> str:
    return (
        "Read-only custom-agent terminal test. "
        f"Spawn exactly one native agent_type {agent}. "
        f"Ask that child to return exactly CHILD_OK:{agent}. Wait for it. "
        "Do not inspect files or substitute another agent. "
        f"Return SPAWN_OK:{agent} only if the child returned the exact token; "
        "otherwise return the exact failure."
    )


def probe_command(codex: str, repo: Path, agent: str, final_path: Path) -> list[str]:
    return [
        codex,
        "exec",
        "--sandbox",
        "read-only",
        "--strict-config",
        "-C",
        str(repo),
        "-o",
        str(final_path),
        probe_prompt(agent),
    ]


def probe_succeeded(agent: str, transcript: str, final_message: str) -> bool:
    failure_markers = ("unknown agent_type", "Capability error", "BLOCKED:")
    return (
        not any(marker in transcript or marker in final_message for marker in failure_markers)
        and "collab: Wait" in transcript
        and final_message.strip() == f"SPAWN_OK:{agent}"
    )


def is_retryable_failure(transcript: str) -> bool:
    return "collab spawn failed: no thread with id:" in transcript


def run_probe(
    codex: str, repo: Path, agent: str, timeout: int, attempts: int
) -> dict[str, object]:
    last_result: dict[str, object] = {}
    for attempt in range(1, attempts + 1):
        with tempfile.TemporaryDirectory(prefix=f"pstack-{agent}-") as temp_dir:
            final_path = Path(temp_dir) / "final.md"
            command = probe_command(codex, repo, agent, final_path)
            try:
                completed = subprocess.run(
                    command,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
                transcript = completed.stdout + completed.stderr
                final_message = final_path.read_text() if final_path.exists() else ""
                success = completed.returncode == 0 and probe_succeeded(
                    agent, transcript, final_message
                )
                last_result = {
                    "agent": agent,
                    "attempts": attempt,
                    "exit_code": completed.returncode,
                    "success": success,
                    "final_message": final_message.strip(),
                    "failure": "" if success else transcript[-2000:],
                }
                if success or not is_retryable_failure(transcript + final_message):
                    return last_result
            except subprocess.TimeoutExpired as error:
                return {
                    "agent": agent,
                    "attempts": attempt,
                    "exit_code": None,
                    "success": False,
                    "final_message": "",
                    "failure": f"timeout after {error.timeout}s",
                }
    return last_result


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test pstack Codex custom agents")
    parser.add_argument("--repo", type=Path, default=default_repo())
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--agent", action="append", choices=AGENTS)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    repo = args.repo.resolve()
    agents = tuple(args.agent) if args.agent else AGENTS
    version = subprocess.run(
        [args.codex, "--version"], capture_output=True, text=True, check=False
    ).stdout.strip()
    commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    results = [
        run_probe(args.codex, repo, agent, args.timeout, args.attempts)
        for agent in agents
    ]
    receipt = {
        "schema": "pstack-codex-agent-smoke-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "codex_version": version,
        "commit": commit,
        "agents": results,
        "passed": all(bool(result["success"]) for result in results),
    }

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(receipt, indent=2) + "\n")

    for result in results:
        status = "PASS" if result["success"] else "FAIL"
        print(f"{status} {result['agent']}: {result['final_message'] or result['failure']}")
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
