# Troubleshooting

Use this reference when Cursor delegation is slow, blocked, or returns unexpected state.

## First Response

Stop adding more Cursor/CDP runs. Gather state with bounded local commands:

```bash
git status --short
lsof -nP -iTCP:9226 -sTCP:LISTEN 2>/dev/null || true
tail -n 20 "$WORKSPACE/.agent_runs/cursor/process-audit.jsonl" 2>/dev/null || true
tail -n 20 "$WORKSPACE/.agent_runs/cursor/thread-registry.jsonl" 2>/dev/null || true
```

Do not run broad process scans repeatedly. If a process scan is needed, run it once and summarize it.

## CDP Refuses Connection

Symptom:

- `Connection refused`
- `/json/version` fails

Likely cause:

- Cursor is running without `--remote-debugging-port`.
- The previous launch delegated to an existing non-CDP Cursor process.

Fix:

1. Quit Cursor normally.
2. Start Cursor with the normal profile and CDP args:

```bash
open -na /Applications/Cursor.app --args \
  --remote-debugging-port=9226 \
  --remote-allow-origins=http://127.0.0.1:9226 \
  "$WORKSPACE"
```

3. Verify `/json/version`.

Do not use a temporary `--user-data-dir`; it can create a separate logged-out Cursor profile.

## Cursor Agents Target Missing

Symptom:

- CDP works, but no target titled `Cursor Agents`.

Actions:

- Bring Cursor Agents window to the foreground manually or with the AppleScript focus helper.
- Recheck `/json`.
- Do not submit prompts until the `Cursor Agents` target exists.

## Workspace Lock Failure

Symptom:

- `another Cursor CDP operation is already running`

Actions:

1. Wait briefly if another run is genuinely active.
2. Inspect the lock pid:

```bash
cat "$WORKSPACE/.agent_runs/cursor/locks/cdp.lock/pid"
```

3. If the pid is dead, remove only that lock directory:

```bash
rm -rf "$WORKSPACE/.agent_runs/cursor/locks/cdp.lock"
```

Do not use `--no-lock` except for deliberate manual debugging.

## Process Budget Exceeded

Symptom:

- process guard exits with code `99`
- process audit has `budget_exceeded: true`

Inspect:

```bash
tail -n 1 "$WORKSPACE/.agent_runs/cursor/process-audit.jsonl"
```

Check:

- `max_processes`
- `max_descendant_processes`
- `max_sample`
- `command`

Response:

- Do not immediately raise limits.
- Identify whether the delegated task asked Cursor to run shell commands or create subprocesses.
- For normal CDP prompt/monitor operations, expected `max_processes` is usually `1`.

## CDP Operation Budget Exceeded

Symptom:

- `operation guard stopped ... CDP call budget exceeded`
- `operation guard stopped ... click budget exceeded`
- `operation guard stopped ... runtime budget exceeded`

Response:

- Treat it as a hard failure.
- Inspect the latest monitor JSON and process audit.
- Reduce registry scope with `--task-id`, `--max-records`, or `--max-candidates`.
- Avoid stale registries for `--monitor-all`.

## Monitor Returns Unmatched

Likely causes:

- Registry is stale.
- Cursor generated a duplicate or changed title.
- Sidebar virtualization changed indexes.
- The target thread is not visible in the current Cursor Agents project.

Response:

- For active work, prefer `--monitor-registry --task-id`.
- For multiple tasks, use only fresh registry records from the current session.
- Do not increase `--max-candidates` beyond a small number unless debugging manually.

## Ask Mode Or Read-Only Completion

Symptom:

- Cursor answers but does not edit files.
- Final report claims completion without expected diff.

Response:

- Treat Cursor report as non-authoritative.
- Check `git status --short`, `git diff --name-only`, and the expected file path.
- Ensure the Agent input is edit-capable before delegating edit tasks.

## Scope Drift

Symptom:

- Files outside write scope changed.

Response:

1. Inspect the diff.
2. If the out-of-scope change is clearly worker-created and safe, main Codex may correct it.
3. If it may be user or unrelated agent work, ask before changing it.
4. Do not use broad destructive commands.

## Heavy Or Unresponsive System

Immediate actions:

- Stop launching new Cursor/CDP commands.
- Do not run repeated `pgrep`/`ps` loops.
- Inspect the latest process audit once.
- Check whether `budget_exceeded` or stale lock exists.
- Prefer a normal Cursor restart with the normal profile if CDP state is confused.
