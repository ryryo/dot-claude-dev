#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path


MODEL_ID = "composer-2.5-fast"


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_jsonl(path):
    records = []
    if not path or not Path(path).exists():
        return records
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def append_jsonl(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def extract_task_summary(prompt):
    match = re.search(r"(?ims)^\s*Task Summary:\s*\n(?P<summary>.+?)(?:\n\s*\n|$)", prompt)
    if not match:
        return None
    lines = [re.sub(r"\s+", " ", line).strip() for line in match.group("summary").splitlines()]
    summary = " ".join(line for line in lines if line)
    return summary or None


def extract_task_id(prompt):
    patterns = [
        r"(?im)^\s*Task ID:\s*([A-Za-z0-9_.:-]+)\s*$",
        r"(?im)^\s*TASK_ID:\s*([A-Za-z0-9_.:-]+)\s*$",
        r"(?im)^\s*タスク ID:\s*([A-Za-z0-9_.:-]+)\s*$",
        r"(?im)^\s*タスクID:\s*([A-Za-z0-9_.:-]+)\s*$",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt)
        if match:
            return match.group(1)
    return None


def read_prompt(prompt_file):
    prompt = Path(prompt_file).read_text(encoding="utf-8")
    summary = extract_task_summary(prompt)
    if not summary:
        raise RuntimeError("Cursor CLI worker prompts must start with a unique 'Task Summary:' block")
    if len(summary) > 180:
        raise RuntimeError("Task Summary must be concise enough for registry labels (180 chars or fewer)")
    task_id = extract_task_id(prompt)
    if not task_id:
        raise RuntimeError("Cursor CLI worker prompts must include 'Task ID:'")
    return {"prompt": prompt, "task_summary": summary, "task_id": task_id}


def latest_records_by_task(records):
    latest = {}
    anonymous = []
    for record in records:
        task_id = record.get("task_id")
        if task_id:
            latest[task_id] = record
        else:
            anonymous.append(record)
    return anonymous + list(latest.values())


def choose_record(records, task_id=None):
    if task_id:
        matches = [record for record in records if record.get("task_id") == task_id]
        if not matches:
            raise RuntimeError(f"task id was not found in registry: {task_id}")
        return matches[-1]
    if not records:
        raise RuntimeError("registry is empty")
    return records[-1]


def process_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def read_output_json(path):
    try:
        text = Path(path).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None, "output file does not exist"
    if not text:
        return None, "output file is empty"
    try:
        return json.loads(text), None
    except json.JSONDecodeError as error:
        return None, f"output JSON parse failed: {error}"


def task_state(record):
    stdout_file = record.get("stdout_file")
    stderr_file = record.get("stderr_file")
    exit_code_file = record.get("exit_code_file")
    ended_at_file = record.get("ended_at_file")
    exit_code = None
    if exit_code_file and Path(exit_code_file).exists():
        raw = Path(exit_code_file).read_text(encoding="utf-8").strip()
        if raw:
            try:
                exit_code = int(raw)
            except ValueError:
                exit_code = raw

    running = exit_code is None and process_alive(record.get("pid", -1))
    output, output_error = read_output_json(stdout_file) if stdout_file else (None, "stdout file missing")
    stderr_tail = ""
    if stderr_file and Path(stderr_file).exists():
        stderr_text = Path(stderr_file).read_text(encoding="utf-8", errors="replace")
        stderr_tail = stderr_text[-1200:]

    done = (
        exit_code == 0
        and isinstance(output, dict)
        and output.get("type") == "result"
        and output.get("subtype") == "success"
        and output.get("is_error") is False
    )
    failed = bool(exit_code not in (None, 0) or (exit_code is not None and not done))
    ended_at = None
    if ended_at_file and Path(ended_at_file).exists():
        ended_at = Path(ended_at_file).read_text(encoding="utf-8").strip() or None

    return {
        "task_id": record.get("task_id"),
        "task_summary": record.get("task_summary"),
        "pid": record.get("pid"),
        "running": running,
        "done": done,
        "failed": failed,
        "exit_code": exit_code,
        "started_at": record.get("started_at"),
        "ended_at": ended_at,
        "stdout_file": stdout_file,
        "stderr_file": stderr_file,
        "output_error": output_error,
        "result": output,
        "stderr_tail": stderr_tail,
    }


def require_cursor():
    cursor = shutil.which("cursor")
    if not cursor:
        raise RuntimeError("cursor command was not found")
    return cursor


def run_command(args, cwd, timeout=60):
    completed = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    return {
        "args": args,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def preflight(workspace):
    cursor = require_cursor()
    version = run_command([cursor, "agent", "--version"], workspace)
    status = run_command([cursor, "agent", "status"], workspace)
    models = run_command([cursor, "agent", "models"], workspace, timeout=120)
    if version["returncode"] != 0:
        raise RuntimeError("cursor agent --version failed: " + version["stderr"])
    if status["returncode"] != 0:
        raise RuntimeError("cursor agent status failed: " + status["stderr"])
    if models["returncode"] != 0:
        raise RuntimeError("cursor agent models failed: " + models["stderr"])
    if MODEL_ID not in models["stdout"]:
        raise RuntimeError(f"required model was not listed by cursor agent models: {MODEL_ID}")

    smoke_prompt = "Reply exactly: CURSOR_CLI_PREFLIGHT_OK. Do not read or write files."
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
            smoke_prompt,
        ],
        workspace,
        timeout=180,
    )
    if smoke["returncode"] != 0:
        raise RuntimeError("cursor agent read-only smoke failed: " + smoke["stderr"])
    try:
        smoke_json = json.loads(smoke["stdout"])
    except json.JSONDecodeError as error:
        raise RuntimeError(f"cursor agent read-only smoke did not return JSON: {error}") from error
    if smoke_json.get("result") != "CURSOR_CLI_PREFLIGHT_OK":
        raise RuntimeError(f"cursor agent read-only smoke returned unexpected result: {smoke_json!r}")

    return {
        "schema_version": 1,
        "ok": True,
        "cursor": cursor,
        "model": MODEL_ID,
        "version": version["stdout"].strip(),
        "status": status["stdout"].strip(),
        "smoke": smoke_json,
    }


def shell_quote(value):
    return "'" + value.replace("'", "'\\''") + "'"


def submit(args):
    context = read_prompt(args.prompt_file)
    workspace = str(Path(args.workspace).resolve())
    registry_file = str(Path(args.registry_file).resolve())
    sprint_dir = str(Path(registry_file).parent)
    reports_dir = Path(sprint_dir) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    task_id = context["task_id"]
    safe_task = re.sub(r"[^A-Za-z0-9_.:-]+", "_", task_id)
    stdout_file = reports_dir / f"{safe_task}.json"
    stderr_file = reports_dir / f"{safe_task}.stderr.log"
    exit_code_file = reports_dir / f"{safe_task}.exit-code"
    ended_at_file = reports_dir / f"{safe_task}.ended-at"
    runner_file = reports_dir / f"{safe_task}.runner.sh"

    prompt_file = str(Path(args.prompt_file).resolve())
    cursor = require_cursor()
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

    started_at = utc_now()
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
        "prompt_sha256": sha256_text(context["prompt"]),
        "pid": process.pid,
        "started_at": started_at,
        "stdout_file": str(stdout_file),
        "stderr_file": str(stderr_file),
        "exit_code_file": str(exit_code_file),
        "ended_at_file": str(ended_at_file),
        "runner_file": str(runner_file),
        "command": [
            "cursor",
            "agent",
            "--print",
            "--yolo",
            "--trust",
            "--workspace",
            workspace,
            "--model",
            MODEL_ID,
            "--output-format",
            "json",
            "<prompt omitted; see prompt_file>",
        ],
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


def monitor_registry(args):
    records = read_jsonl(args.registry_file)
    record = choose_record(records, args.task_id)
    deadline = time.time() + args.timeout
    while True:
        state = task_state(record)
        result = {
            "schema_version": 1,
            "mode": "monitor-registry",
            "registry_file": str(Path(args.registry_file).resolve()),
            "record": record,
            "thread": state,
            "matched": True,
            "task_id": record.get("task_id"),
        }
        if not args.wait or state["done"] or state["failed"] or time.time() >= deadline:
            return result
        time.sleep(args.poll_interval)


def monitor_all(args):
    records = latest_records_by_task(read_jsonl(args.registry_file))
    task_records = [record for record in records if record.get("task_id")]
    if args.max_records > 0:
        task_records = task_records[-args.max_records:]
    deadline = time.time() + args.timeout
    while True:
        results = []
        for record in task_records:
            state = task_state(record)
            results.append({
                "task_id": record.get("task_id"),
                "record": record,
                "thread": state,
                "matched": True,
            })
        done_count = sum(1 for result in results if result["thread"].get("done"))
        running_count = sum(1 for result in results if result["thread"].get("running"))
        failed_count = sum(1 for result in results if result["thread"].get("failed"))
        all_done = bool(task_records) and done_count == len(task_records)
        summary = {
            "schema_version": 1,
            "mode": "monitor-all",
            "registry_file": str(Path(args.registry_file).resolve()),
            "count": len(task_records),
            "done_count": done_count,
            "running_count": running_count,
            "failed_count": failed_count,
            "all_done": all_done,
            "results": results,
        }
        if not args.wait or all_done or failed_count or time.time() >= deadline:
            return summary
        time.sleep(args.poll_interval)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=os.getcwd())
    parser.add_argument("--registry-file", default="")
    parser.add_argument("--prompt-file")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--validate-prompt", action="store_true")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--monitor-registry", action="store_true")
    parser.add_argument("--monitor-all", action="store_true")
    parser.add_argument("--task-id")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--poll-interval", type=float, default=2)
    parser.add_argument("--max-records", type=int, default=8)
    args = parser.parse_args()
    args.workspace = str(Path(args.workspace).resolve())
    if not args.registry_file:
        args.registry_file = str(Path(args.workspace) / ".agent_runs/cursor-cli/thread-registry.jsonl")
    return args


def main():
    args = parse_args()
    try:
        if args.preflight:
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
                "summary_length": len(context["task_summary"]),
            }
        elif args.submit:
            if not args.prompt_file:
                raise RuntimeError("--prompt-file is required with --submit")
            result = submit(args)
        elif args.monitor_registry:
            result = monitor_registry(args)
        elif args.monitor_all:
            result = monitor_all(args)
        else:
            raise RuntimeError(
                "choose one of --preflight, --validate-prompt, --submit, --monitor-registry, or --monitor-all"
            )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    except Exception as error:
        print(json.dumps({"schema_version": 1, "ok": False, "error": str(error)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
