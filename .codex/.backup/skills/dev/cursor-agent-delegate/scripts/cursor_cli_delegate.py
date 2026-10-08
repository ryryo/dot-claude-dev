#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


MODEL_ID = "composer-2.5-fast"


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def append_jsonl(path, record):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path):
    target = Path(path)
    if not target.exists():
        return []
    records = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def extract_prompt_context(prompt):
    summary_match = re.search(
        r"(?ims)^\s*Task Summary:\s*\n(?P<summary>.+?)(?:\n\s*\n|$)", prompt
    )
    if not summary_match:
        raise RuntimeError("Cursor CLI prompt must start with a unique 'Task Summary:' block")
    summary = " ".join(
        re.sub(r"\s+", " ", line).strip()
        for line in summary_match.group("summary").splitlines()
        if line.strip()
    )
    if len(summary) > 180:
        raise RuntimeError("Task Summary must be 180 characters or fewer")

    task_match = re.search(
        r"(?im)^\s*(?:Task ID|TASK_ID|タスク ID|タスクID):\s*([A-Za-z0-9_.:-]+)\s*$",
        prompt,
    )
    if not task_match:
        raise RuntimeError("Cursor CLI prompt must include 'Task ID:'")
    return {"task_id": task_match.group(1), "task_summary": summary, "prompt": prompt}


def read_prompt(path):
    return extract_prompt_context(Path(path).read_text(encoding="utf-8"))


def require_cursor():
    cursor = shutil.which("cursor")
    if not cursor:
        raise RuntimeError("cursor command was not found")
    return cursor


def run_command(command, workspace, timeout=60):
    completed = subprocess.run(
        command,
        cwd=workspace,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def preflight(workspace):
    cursor = require_cursor()
    checks = {
        "version": run_command([cursor, "agent", "--version"], workspace),
        "status": run_command([cursor, "agent", "status"], workspace),
        "models": run_command([cursor, "agent", "models"], workspace, timeout=120),
    }
    for name, result in checks.items():
        if result["returncode"] != 0:
            raise RuntimeError(f"cursor agent {name} failed: {result['stderr'].strip()}")
    if MODEL_ID not in checks["models"]["stdout"]:
        raise RuntimeError(f"required model was not listed: {MODEL_ID}")

    smoke = run_command(
        [
            cursor,
            "agent",
            "--print",
            "--mode",
            "ask",
            "--trust",
            "--workspace",
            workspace,
            "--model",
            MODEL_ID,
            "--output-format",
            "json",
            "Reply exactly: CURSOR_CLI_PREFLIGHT_OK. Do not read or write files.",
        ],
        workspace,
        timeout=180,
    )
    if smoke["returncode"] != 0:
        raise RuntimeError(f"read-only smoke failed: {smoke['stderr'].strip()}")
    try:
        smoke_json = json.loads(smoke["stdout"])
    except json.JSONDecodeError as error:
        raise RuntimeError(f"read-only smoke did not return JSON: {error}") from error
    if smoke_json.get("result") != "CURSOR_CLI_PREFLIGHT_OK":
        raise RuntimeError(f"read-only smoke returned an unexpected result: {smoke_json!r}")

    return {
        "schema_version": 1,
        "ok": True,
        "model": MODEL_ID,
        "cursor": cursor,
        "version": checks["version"]["stdout"].strip(),
        "status": checks["status"]["stdout"].strip(),
        "smoke": smoke_json,
    }


def shell_quote(value):
    return "'" + value.replace("'", "'\\''") + "'"


def submit(args):
    context = read_prompt(args.prompt_file)
    workspace = str(Path(args.workspace).resolve())
    registry_file = str(Path(args.registry_file).resolve())
    reports_dir = Path(registry_file).parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    task_id = context["task_id"]
    safe_id = re.sub(r"[^A-Za-z0-9_.:-]+", "_", task_id)
    stdout_file = reports_dir / f"{safe_id}.json"
    stderr_file = reports_dir / f"{safe_id}.stderr.log"
    exit_code_file = reports_dir / f"{safe_id}.exit-code"
    ended_at_file = reports_dir / f"{safe_id}.ended-at"
    runner_file = reports_dir / f"{safe_id}.runner.sh"
    prompt_file = str(Path(args.prompt_file).resolve())
    cursor = require_cursor()

    for stale_file in (stdout_file, stderr_file, exit_code_file, ended_at_file):
        stale_file.unlink(missing_ok=True)

    runner = f"""#!/usr/bin/env bash
set +e
prompt="$(cat {shell_quote(prompt_file)})"
{shell_quote(cursor)} agent --print --yolo --trust --workspace {shell_quote(workspace)} --model {shell_quote(MODEL_ID)} --output-format json "$prompt" > {shell_quote(str(stdout_file))} 2> {shell_quote(str(stderr_file))}
rc=$?
printf '%s\\n' "$rc" > {shell_quote(str(exit_code_file))}
date -u '+%Y-%m-%dT%H:%M:%SZ' > {shell_quote(str(ended_at_file))}
exit "$rc"
"""
    runner_file.write_text(runner, encoding="utf-8")
    runner_file.chmod(0o755)

    process = subprocess.Popen(
        [str(runner_file)],
        cwd=workspace,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    record = {
        "schema_version": 1,
        "transport": "cursor-agent-cli",
        "workspace": workspace,
        "model": MODEL_ID,
        "approval": "yolo",
        "task_id": task_id,
        "task_summary": context["task_summary"],
        "prompt_file": prompt_file,
        "prompt_sha256": hashlib.sha256(context["prompt"].encode("utf-8")).hexdigest(),
        "pid": process.pid,
        "started_at": utc_now(),
        "stdout_file": str(stdout_file),
        "stderr_file": str(stderr_file),
        "exit_code_file": str(exit_code_file),
        "ended_at_file": str(ended_at_file),
        "runner_file": str(runner_file),
    }
    append_jsonl(registry_file, record)
    return {
        "schema_version": 1,
        "submitted": True,
        "task_id": task_id,
        "task_summary": context["task_summary"],
        "pid": process.pid,
        "registry_file": registry_file,
        "stdout_file": str(stdout_file),
        "stderr_file": str(stderr_file),
        "model": MODEL_ID,
        "approval": "yolo",
    }


def process_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except (TypeError, ValueError):
        return False


def read_result(path):
    target = Path(path)
    if not target.exists():
        return None, "output file does not exist"
    text = target.read_text(encoding="utf-8").strip()
    if not text:
        return None, "output file is empty"
    try:
        return json.loads(text), None
    except json.JSONDecodeError as error:
        return None, f"output JSON parse failed: {error}"


def task_state(record):
    exit_path = Path(record["exit_code_file"])
    exit_code = None
    if exit_path.exists():
        raw = exit_path.read_text(encoding="utf-8").strip()
    else:
        raw = ""
    if raw:
        try:
            exit_code = int(raw)
        except ValueError:
            exit_code = raw

    result, output_error = read_result(record["stdout_file"])
    stderr_path = Path(record["stderr_file"])
    stderr_tail = ""
    if stderr_path.exists():
        stderr_tail = stderr_path.read_text(encoding="utf-8", errors="replace")[-1200:]
    done = (
        exit_code == 0
        and isinstance(result, dict)
        and result.get("type") == "result"
        and result.get("subtype") == "success"
        and result.get("is_error") is False
    )
    failed = exit_code is not None and not done
    ended_at = None
    ended_path = Path(record["ended_at_file"])
    if ended_path.exists():
        ended_at = ended_path.read_text(encoding="utf-8").strip() or None
    return {
        "task_id": record.get("task_id"),
        "task_summary": record.get("task_summary"),
        "pid": record.get("pid"),
        "running": exit_code is None and process_alive(record.get("pid")),
        "done": done,
        "failed": failed,
        "exit_code": exit_code,
        "started_at": record.get("started_at"),
        "ended_at": ended_at,
        "result": result,
        "output_error": output_error,
        "stderr_tail": stderr_tail,
        "stdout_file": record["stdout_file"],
        "stderr_file": record["stderr_file"],
    }


def choose_record(records, task_id):
    matches = [record for record in records if record.get("task_id") == task_id]
    if not matches:
        raise RuntimeError(f"task id was not found in registry: {task_id}")
    return matches[-1]


def monitor_registry(args):
    if not args.task_id:
        raise RuntimeError("--task-id is required with --monitor-registry")
    record = choose_record(read_jsonl(args.registry_file), args.task_id)
    deadline = time.time() + args.timeout
    while True:
        state = task_state(record)
        output = {
            "schema_version": 1,
            "mode": "monitor-registry",
            "registry_file": str(Path(args.registry_file).resolve()),
            "matched": True,
            "record": record,
            "thread": state,
        }
        if not args.wait or state["done"] or state["failed"] or time.time() >= deadline:
            return output
        time.sleep(args.poll_interval)


def latest_records_by_task(records):
    latest = {}
    for record in records:
        if record.get("task_id"):
            latest[record["task_id"]] = record
    return list(latest.values())


def monitor_all(args):
    records = latest_records_by_task(read_jsonl(args.registry_file))
    if args.max_records > 0:
        records = records[-args.max_records :]
    deadline = time.time() + args.timeout
    while True:
        results = [
            {"task_id": record["task_id"], "record": record, "thread": task_state(record)}
            for record in records
        ]
        done_count = sum(item["thread"]["done"] for item in results)
        failed_count = sum(item["thread"]["failed"] for item in results)
        running_count = sum(item["thread"]["running"] for item in results)
        output = {
            "schema_version": 1,
            "mode": "monitor-all",
            "registry_file": str(Path(args.registry_file).resolve()),
            "count": len(records),
            "done_count": done_count,
            "failed_count": failed_count,
            "running_count": running_count,
            "all_done": bool(records) and done_count == len(records),
            "results": results,
        }
        if (
            not args.wait
            or not records
            or output["all_done"]
            or failed_count
            or time.time() >= deadline
        ):
            return output
        time.sleep(args.poll_interval)


def parse_args():
    parser = argparse.ArgumentParser(description="Run and monitor headless Cursor CLI workers")
    parser.add_argument("--workspace", default=os.getcwd())
    parser.add_argument("--registry-file", default="")
    parser.add_argument("--prompt-file")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--submit", action="store_true")
    action.add_argument("--monitor-registry", action="store_true")
    action.add_argument("--monitor-all", action="store_true")
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--validate-prompt", action="store_true")
    parser.add_argument("--task-id")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--poll-interval", type=float, default=2)
    parser.add_argument("--max-records", type=int, default=8)
    args = parser.parse_args()
    args.workspace = str(Path(args.workspace).resolve())
    if not args.registry_file:
        args.registry_file = str(
            Path(args.workspace) / ".agent_runs/cursor-delegate/thread-registry.jsonl"
        )
    return args


def main():
    args = parse_args()
    try:
        if args.submit:
            if not args.prompt_file:
                raise RuntimeError("--prompt-file is required with --submit")
            result = submit(args)
        elif args.monitor_registry:
            result = monitor_registry(args)
        elif args.monitor_all:
            result = monitor_all(args)
        elif args.preflight:
            result = preflight(args.workspace)
        elif args.validate_prompt:
            if not args.prompt_file:
                raise RuntimeError("--prompt-file is required with --validate-prompt")
            context = read_prompt(args.prompt_file)
            result = {
                "schema_version": 1,
                "ok": True,
                "task_id": context["task_id"],
                "task_summary": context["task_summary"],
            }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    except Exception as error:
        print(
            json.dumps(
                {"schema_version": 1, "ok": False, "error": str(error)},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
