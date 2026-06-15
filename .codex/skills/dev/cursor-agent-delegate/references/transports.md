# Transports

This skill is macOS-only for Cursor IDE orchestration.

Default transport:

- `mac-ide-cdp`: default for no-clipboard prompt insertion and multi-thread/worktree orchestration.
- `mac-ide-applescript`: helper transport for activating/focusing Cursor Agents and small UI operations.
- `deeplink`: manual fallback when the user wants to review the prompt in Cursor before running it.

Non-macOS Cursor IDE workflows are out of scope for this skill.

## mac-ide-applescript

Supported only on macOS. This is UI automation, not a stable Cursor API.

Current role:

- Bring Cursor / `Cursor Agents` to the foreground.
- Confirm the Agents window exists.
- Perform bounded UI helper operations when they are separately smoke-tested.
- Do not use it as the standard no-clipboard prompt insertion path.

Preflight:

- `/Applications/Cursor.app` exists.
- `osascript` exists.
- Cursor has an open Agents window for the target workspace, or the user can open one from an existing Cursor workspace window.
- macOS Accessibility permission allows System Events to inspect and control Cursor.
- For edit delegation, the Agent input is in an edit-capable mode, not `Ask` mode.

Verified behavior:

- Activate Cursor.
- Prefer the `Cursor Agents` window.
- Focus the `Cursor Agents` window.
- Do not infer completion from UI state.

Rejected or unverified for the standard path:

- `AXTextArea` direct-set prompt insertion: failed on Cursor 3.7.36 because the Agent prompt editor is exposed to CDP as a Tiptap/ProseMirror `contenteditable` element, but not as a stable writable `AXTextArea`.
- Keyboard/clipboard prompt insertion: possible in many AppleScript examples, but not accepted as the standard path because this project avoids `Cmd+V` / pasteboard mutation.
- Long prompt typing through `System Events keystroke`: not accepted as the standard path because it is slow and focus-sensitive.

Non-goals:

- Do not use `pbcopy`, pasteboard, or `Cmd+V` as a standard prompt-insertion path.
- Do not switch model or mode programmatically.
- Do not auto-remove the `Ask` chip.
- Do not auto-approve tool permissions.

After Cursor completes, main Codex validates with result file, `git status`, `git diff`, and verification commands.

## mac-ide-cdp

macOS transport for no-clipboard prompt insertion and project-level multi-thread orchestration. Submit is supported for Cursor 3.7.36 with the verified Agent Window selector below.

Purpose:

- Attach to Cursor's Electron/Chromium UI through Chrome DevTools Protocol.
- Identify Cursor page targets and Agent threads.
- Insert text without clipboard using CDP `Input.insertText`.
- Click the DOM send button.
- Track target id, title, workspace hints, active chat/thread hints, running/approval advisory state.

Preflight:

```bash
curl http://127.0.0.1:9226/json/version
curl http://127.0.0.1:9226/json
```

Cursor must be launched with a remote debugging port, for example:

```bash
/Applications/Cursor.app/Contents/MacOS/Cursor \
  --remote-debugging-port=9226 \
  --remote-allow-origins=http://127.0.0.1:9226
```

If Cursor is already running without CDP, assume the existing process cannot be retrofitted. Use a deliberate test launch or restart flow.

Implementation outline:

1. Read `/json/version` for the browser-level WebSocket URL.
2. Read `/json` for page targets.
3. Filter `type == "page"` and exclude devtools targets.
4. Pick the target by project/workspace title and URL hints.
5. Use `Page.bringToFront` or `Target.activateTarget` as a foreground hint.
6. Use `Runtime.evaluate` to find and focus a Lexical/contenteditable input.
7. Use `Input.insertText` to insert the prompt.
8. Read back DOM text.
9. Click the send button only when submit is explicit.
10. For research-only tasks without a result file, treat DOM completion as provisional and validate with `git status --short`.

Selector candidates:

```text
[data-lexical-editor="true"]
.aislash-editor-input
.composer-bar [data-lexical-editor="true"]
[id*="composer"] [contenteditable="true"]
.composite.auxiliarybar[data-composer-id]
.composer-bar[data-composer-id]
textarea
[role="textbox"]
```

Send button candidates:

```text
button.ui-prompt-input-submit-button[aria-label="Send message"]
.send-with-mode .anysphere-icon-button
button[aria-label="Send"]
.send-with-mode button
button[aria-label="Send message"]
```

Verified Agent Window selectors on Cursor 3.7.36:

```text
input: .tiptap.ProseMirror.ui-prompt-input-editor__input[contenteditable="true"]
submit: button.ui-prompt-input-submit-button[aria-label="Send message"]
thread item: .glass-sidebar-agent-menu-btn
project selector: button.project-selector__trigger
```

Completion signals:

- Do not treat final-format text inside the submitted prompt as completion.
- `Stop generation` / cancel controls disappearing is a running-state signal.
- A visible assistant response bubble such as `.composer-rendered-message` containing the delegated task id and final report is a provisional completion signal.
- The final authority remains result file, `git status`, `git diff`, and verification commands.

Parallel monitoring caveat:

- Active thread running state can be read with CDP while generation is in progress.
- Sidebar title is not a stable thread id. Cursor may generate duplicate titles or show the prompt opening line.
- Record a thread registry at creation time: sidebar index/order, visible title, expected task id, workspace, and prompt file.
- After switching threads, confirm the body contains the expected task id before trusting any running/done signal.

Registry behavior:

- `run_cursor_delegate.sh --submit` writes JSONL by default to `$WORKSPACE/.agent_runs/cursor/thread-registry.jsonl`.
- Override with `--registry-file FILE`.
- Disable with `--no-registry`.
- Each record includes `task_id`, `prompt_sha256`, `prompt_file`, `workspace`, CDP page target metadata, `thread_snapshot`, `sidebar_before`, and `sidebar_after`.
- Treat the registry as a navigation aid, not final authority. The body task id and diff/test checks still decide correctness.

Monitor behavior:

- `run_cursor_delegate.sh --monitor-registry --task-id ID` opens the registered thread candidate, verifies the body contains `ID`, and prints JSON with `running`, `done`, `final_report`, title text, running hints, and registry metadata.
- `run_cursor_delegate.sh --monitor-all` deduplicates the registry by task id, opens each registered thread candidate, verifies the body task id, and prints aggregate counts plus per-thread DOM results.
- Add `--wait` to poll until the assistant final report is visible or timeout is reached.
- Candidate switching is bounded by `--max-candidates` (default 3) per registered thread, and `--monitor-all` reads at most `--max-records` task records by default (default 8). Stale records should become `unmatched` instead of causing unbounded sidebar traversal.
- CDP operations are protected by a workspace-level lock by default. A second wrapper invocation fails instead of opening another concurrent CDP control loop. Use `--no-lock` only for deliberate manual debugging.
- The Python CDP helper enforces operation budgets: `--max-cdp-calls`, `--max-clicks`, and `--max-runtime`. Exceeding any budget is a hard failure, not a warning.
- The wrapper launches CDP helper commands through `scripts/process_guard.py` by default. The process guard writes JSONL audit records to `$WORKSPACE/.agent_runs/cursor/process-audit.jsonl`, including `root_pid`, `max_processes`, `max_descendant_processes`, sampled counts, command, and exit code. If `--max-child-processes` is exceeded, it terminates the helper process group and exits non-zero.
- Direct DOM result is appropriate for research/review tasks that do not need repository artifacts.
- Result files remain useful for edit tasks because they give Cursor a structured write contract, but they are not required for every delegated task on the same machine.

Security:

- Bind to loopback only.
- Do not expose the CDP port to LAN.
- Treat CDP as a powerful local control port.
- Keep this transport opt-in until smoke tests are reliable.

## deeplink

Use only when the user wants to review the prompt in Cursor before running it.

Generate:

```text
cursor://anysphere.cursor-deeplink/prompt?text=<urlencoded prompt>
```

Deeplinks prefill prompts. They do not automatically execute them.
