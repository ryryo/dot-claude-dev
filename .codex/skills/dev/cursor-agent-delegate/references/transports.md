# Transports

Default transport:

- macOS: use `mac-ide-applescript` first.
- macOS fallback: use `cli` when AppleScript preflight or prompt insertion fails, or when the user explicitly asks for CLI/headless execution.
- WSL/Linux: use `cli`.
- Use `deeplink` only when the user wants manual confirmation in Cursor IDE.

The wrapper default transport is `auto`, which follows the rules above.

## mac-ide-applescript

Supported only on macOS. This is the default macOS path. It is UI automation, not a stable Cursor API.

Preflight:

- `/Applications/Cursor.app` exists.
- `osascript` exists.
- Cursor has an open Agent window for the target workspace, or an existing Cursor workspace window from which the Agent window can be opened by the user.
- macOS Accessibility permission allows System Events to drive Cursor.
- For edit delegation, the Agent window input is in an edit-capable mode, not `Ask` mode. If the `Ask` chip is present, remove it before submitting.

Behavior:

- Activate Cursor.
- Prefer the `Cursor Agents` window and set its first accessible `AXTextArea` value directly.
- Keep the prompt in the clipboard as a fallback for the legacy keyboard path.
- If the `Cursor Agents` window text area cannot be set directly, focus the front Cursor window, open/toggle the Agent/Composer input by keyboard shortcut, select existing input, and paste the prompt.
- Submit only when `--submit` is explicitly passed.
- `--mode edit` does not programmatically switch Cursor out of `Ask` mode. Cursor has to already be in an edit-capable mode, or the run will complete as a read-only Ask response.
- Do not infer completion from UI state.

After Cursor completes, main Codex validates with `git status`, `git diff`, and verification commands.

Fallback:

- If app activation, focus, Agent window detection, direct text-area setting, or fallback prompt insertion fails, use `cli`.
- Report that the model is controlled by Cursor IDE state and cannot be programmatically verified.

## cli

Supported on macOS and WSL. Requires `agent` on PATH.

Use on macOS only when AppleScript transport is unavailable or the user explicitly requests CLI/headless execution.

Preflight:

```bash
command -v agent
agent status
agent models | rg '^composer-2\.5\b'
git status --short
```

Default model is `composer-2.5`. Use `composer-2.5-fast` only when the user explicitly chooses speed over cost/quality predictability.

Read-only:

```bash
agent -p --mode ask --workspace "$WORKSPACE" --model "$MODEL" --output-format text "$PROMPT"
```

Edit:

```bash
agent -p --force --trust --workspace "$WORKSPACE" --model "$MODEL" --output-format stream-json --stream-partial-output "$PROMPT" | tee "$LOG"
```

WSL:

- Detect WSL with `uname -s` = `Linux` and `/proc/version` containing `microsoft`.
- Prefer repositories under the Linux filesystem, such as `/home/<user>/src/project`.
- Warn for `/mnt/c/...` unless the user explicitly accepts Windows-mounted filesystem tradeoffs.
- Do not control Windows-side Cursor IDE from WSL.

## deeplink

Use only when the user wants to review the prompt in Cursor before running it.

Generate:

```text
cursor://anysphere.cursor-deeplink/prompt?text=<urlencoded prompt>
```

Deeplinks prefill prompts. They do not automatically execute them.
