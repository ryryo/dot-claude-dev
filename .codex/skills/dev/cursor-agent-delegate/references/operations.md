# Operations

This reference is the operational entrypoint for routine Cursor Agent delegation.

## Preconditions

- Use macOS Cursor IDE only.
- Cursor must run with a loopback CDP port.
- Use the normal Cursor profile. Do not use a temporary `--user-data-dir`.
- Keep `--no-lock` and `--no-process-guard` off in routine use.
- Delegate only one bounded task per prompt.
- Main Codex remains responsible for diff review, tests, commits, push, PR, and final acceptance.

## Start Cursor With CDP

If CDP is not already listening:

```bash
open -na /Applications/Cursor.app --args \
  --remote-debugging-port=9226 \
  --remote-allow-origins=http://127.0.0.1:9226 \
  "$WORKSPACE"
```

Verify:

```bash
curl http://127.0.0.1:9226/json/version
curl http://127.0.0.1:9226/json
```

There must be a page target titled `Cursor Agents`.

## Submit One Cursor Agent Task

Prepare a prompt file with:

- `Workspace`
- `Task ID`
- one concrete `Goal`
- write scope
- forbidden paths/actions
- verification command or explicit read-only contract
- final report format

Run:

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --transport mac-ide-cdp \
  --workspace "$WORKSPACE" \
  --prompt-file "$PROMPT_FILE" \
  --new-agent \
  --submit
```

Default outputs:

- `$WORKSPACE/.agent_runs/cursor/thread-registry.jsonl`
- `$WORKSPACE/.agent_runs/cursor/process-audit.jsonl`

For test runs, use explicit `.tmp/...` registry and process report files.

## Monitor One Task

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --transport mac-ide-cdp \
  --workspace "$WORKSPACE" \
  --monitor-registry \
  --task-id "$TASK_ID" \
  --wait
```

Accept the DOM result only after `matched: true`, `running: false`, and the expected task id appears in the final report.

## Monitor Several Fresh Tasks

Use only for recent registry records created in the current session.

```bash
.codex/skills/dev/cursor-agent-delegate/scripts/run_cursor_delegate.sh \
  --transport mac-ide-cdp \
  --workspace "$WORKSPACE" \
  --monitor-all \
  --wait \
  --max-records 4 \
  --max-candidates 2
```

`--monitor-all` is a fresh-session dashboard. It is not a durable historical thread resolver.

## Inspect Guard Logs

```bash
tail -n 20 "$WORKSPACE/.agent_runs/cursor/process-audit.jsonl"
tail -n 20 "$WORKSPACE/.agent_runs/cursor/thread-registry.jsonl"
```

Important process audit fields:

- `budget_exceeded`
- `exit_code`
- `max_processes`
- `max_descendant_processes`
- `command`
- `samples`

Important monitor fields:

- `matched`
- `done`
- `running`
- `final_report`
- `guard.cdp_calls`
- `guard.clicks`

## Review After Cursor Completes

Main Codex must run:

```bash
git status --short
git diff --name-only
git diff --stat
```

For edit tasks, also inspect the allowed files and rerun verification commands. Cursor's final report is evidence, not authority.
