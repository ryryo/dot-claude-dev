#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import signal
import subprocess
import sys
import time


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read_process_table():
    result = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,command="],
        check=False,
        capture_output=True,
        text=True,
    )
    processes = {}
    children = {}
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 2:
            continue
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except ValueError:
            continue
        command = parts[2] if len(parts) > 2 else ""
        processes[pid] = {"pid": pid, "ppid": ppid, "command": command}
        children.setdefault(ppid, []).append(pid)
    return processes, children


def descendants(root_pid):
    processes, children = read_process_table()
    seen = set()
    stack = list(children.get(root_pid, []))
    items = []
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        process = processes.get(pid)
        if process:
            items.append(process)
        stack.extend(children.get(pid, []))
    return items


def write_report(path, report):
    if not path:
        return
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(report, ensure_ascii=False, sort_keys=True) + "\n")


def terminate_process_group(pid):
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except PermissionError:
        return
    time.sleep(1)
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except PermissionError:
        return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-child-processes", type=int, default=6)
    parser.add_argument("--poll-interval", type=float, default=2)
    parser.add_argument("--report-file")
    parser.add_argument("--label", default="cursor-delegate")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise RuntimeError("process_guard.py requires a command after --")

    started_at = utc_now()
    process = subprocess.Popen(command, preexec_fn=os.setsid)
    max_count = 1
    max_descendant_count = 0
    max_sample = []
    samples = [{"at": utc_now(), "count": 1}]
    exceeded = False
    exit_code = None

    try:
        while True:
            current = descendants(process.pid)
            descendant_count = len(current)
            count = 1 + descendant_count if process.poll() is None else descendant_count
            if count > max_count:
                max_count = count
                max_descendant_count = descendant_count
                max_sample = current[:20]
            samples.append({"at": utc_now(), "count": count})
            samples = samples[-20:]
            if args.max_child_processes > 0 and count > args.max_child_processes:
                exceeded = True
                terminate_process_group(process.pid)
                exit_code = 99
                break
            exit_code = process.poll()
            if exit_code is not None:
                break
            time.sleep(args.poll_interval)
    finally:
        if exit_code is None:
            exit_code = process.poll()
        if exit_code is None:
            terminate_process_group(process.pid)
            exit_code = 99
        report = {
            "schema_version": 1,
            "label": args.label,
            "started_at": started_at,
            "ended_at": utc_now(),
            "root_pid": process.pid,
            "command": command,
            "exit_code": exit_code,
            "max_processes": max_count,
            "max_descendant_processes": max_descendant_count,
            "max_process_budget": args.max_child_processes,
            "budget_exceeded": exceeded,
            "max_sample": max_sample,
            "samples": samples,
        }
        write_report(args.report_file, report)

    if exceeded:
        print(
            "process_guard: process budget exceeded "
            f"({max_count}>{args.max_child_processes}); report={args.report_file}",
            file=sys.stderr,
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
