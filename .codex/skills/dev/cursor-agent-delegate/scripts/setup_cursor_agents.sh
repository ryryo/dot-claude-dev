#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  setup_cursor_agents.sh --workspace PATH [options]

Options:
  --workspace PATH              Repository workspace path (default: current directory)
  --port PORT                   Cursor CDP port (default: 9226)
  --expected-project TEXT       Expected project label in Cursor Agents (default: workspace basename)
  --model-tier fast|standard    Composer 2.5 tier to verify (default: $CURSOR_AGENT_MODEL_TIER or fast)
  --expected-model TEXT         Explicit expected model label/id. Overrides --model-tier.
  --skip-context-check          Allow setup without project/model verification
  --restart-cursor-approved     Quit/reopen Cursor if Cursor is running without the CDP port
  --no-smoke                    Skip read-only New Agent smoke submit/monitor
  --timeout SECONDS             Wait timeout for Cursor Agents target and smoke monitor (default: 120)
  -h, --help                    Show this help
USAGE
}

workspace="$PWD"
port="9226"
expected_project=""
model_tier="${CURSOR_AGENT_MODEL_TIER:-fast}"
expected_model="${CURSOR_AGENT_MODEL:-}"
skip_context_check=0
restart_cursor_approved=0
run_smoke=1
timeout=120

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) workspace="${2:?}"; shift 2 ;;
    --port) port="${2:?}"; shift 2 ;;
    --expected-project) expected_project="${2:?}"; shift 2 ;;
    --model-tier) model_tier="${2:?}"; shift 2 ;;
    --expected-model) expected_model="${2:?}"; shift 2 ;;
    --skip-context-check) skip_context_check=1; shift ;;
    --restart-cursor-approved) restart_cursor_approved=1; shift ;;
    --no-smoke) run_smoke=0; shift ;;
    --timeout) timeout="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Preflight failed: Cursor Agents setup is macOS-only" >&2
  exit 1
fi

if [[ ! -d /Applications/Cursor.app ]]; then
  echo "Preflight failed: /Applications/Cursor.app not found" >&2
  exit 1
fi

workspace="$(cd "$workspace" && pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
endpoint="http://127.0.0.1:${port}"

if [[ -z "$expected_project" ]]; then
  expected_project="$(basename "$workspace")"
fi
case "$model_tier" in
  fast) resolved_model="composer-2.5-fast" ;;
  standard) resolved_model="composer-2.5" ;;
  *) echo "Preflight failed: --model-tier must be 'fast' or 'standard'." >&2; exit 2 ;;
esac
if [[ -z "$expected_model" ]]; then
  expected_model="$resolved_model"
fi
echo "cursor_agents_setup.model_tier=$model_tier"
echo "cursor_agents_setup.expected_model=$expected_model"

if [[ "$skip_context_check" -ne 1 ]]; then
  if [[ -z "$expected_project" || -z "$expected_model" ]]; then
    echo "Preflight failed: --expected-project and --expected-model are required unless --skip-context-check is set." >&2
    exit 2
  fi
fi

cursor_running() {
  pgrep -x Cursor >/dev/null 2>&1
}

cdp_listening() {
  lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | grep -q 'Cursor'
}

open_cursor_with_cdp() {
  open -na /Applications/Cursor.app --args \
    --remote-debugging-port="$port" \
    --remote-allow-origins="$endpoint" \
    "$workspace"
}

wait_for_cdp() {
  local deadline
  deadline=$((SECONDS + timeout))
  until curl -fsS "$endpoint/json/version" >/dev/null 2>&1; do
    if [[ "$SECONDS" -ge "$deadline" ]]; then
      echo "Preflight failed: Cursor CDP did not become available at $endpoint" >&2
      exit 1
    fi
    sleep 1
  done
}

has_agents_target() {
  python3 - "$endpoint" <<'PY'
import json
import sys
import urllib.request

endpoint = sys.argv[1].rstrip("/")
try:
    with urllib.request.urlopen(endpoint + "/json", timeout=3) as response:
        targets = json.loads(response.read().decode("utf-8"))
except Exception:
    sys.exit(1)
for target in targets:
    if target.get("type") == "page" and target.get("title") == "Cursor Agents":
        sys.exit(0)
sys.exit(1)
PY
}

open_agents_window() {
  osascript <<'APPLESCRIPT'
tell application "Cursor" to activate
delay 0.5
tell application "System Events"
  tell process "Cursor"
    set frontmost to true
    try
      click menu item "New Agent" of menu "File" of menu bar item "File" of menu bar 1
      return
    end try
    try
      click menu item "New Agent" of menu "ファイル" of menu bar item "ファイル" of menu bar 1
      return
    end try
    error "New Agent menu item was not found"
  end tell
end tell
APPLESCRIPT
}

wait_for_agents_target() {
  local deadline
  deadline=$((SECONDS + timeout))
  until has_agents_target; do
    if [[ "$SECONDS" -ge "$deadline" ]]; then
      echo "Preflight failed: Cursor Agents target did not appear in $endpoint/json" >&2
      exit 1
    fi
    sleep 1
  done
}

if ! cdp_listening; then
  if cursor_running; then
    if [[ "$restart_cursor_approved" -ne 1 ]]; then
      echo "Preflight failed: Cursor is running but CDP port $port is not listening." >&2
      echo "Ask the user before restarting Cursor, then rerun with --restart-cursor-approved." >&2
      exit 1
    fi
    osascript -e 'tell application "Cursor" to quit'
    sleep 3
  fi
  open_cursor_with_cdp
fi

wait_for_cdp

if ! has_agents_target; then
  open_agents_window
fi

wait_for_agents_target

tmp_dir="$workspace/.codex/tmp"
mkdir -p "$tmp_dir"

preflight_args=(
  --transport mac-ide-cdp
  --workspace "$workspace"
  --cdp-endpoint "$endpoint"
  --process-report-file "$tmp_dir/cursor-agents-setup-process.jsonl"
  --new-agent
)
if [[ -n "$expected_project" ]]; then
  preflight_args+=(--expected-project "$expected_project")
fi
if [[ -n "$expected_model" ]]; then
  preflight_args+=(--expected-model "$expected_model")
fi

preflight_log="$tmp_dir/cursor-agents-setup-preflight.log"
if ! "$script_dir/run_cursor_delegate.sh" "${preflight_args[@]}" 2>&1 | tee "$preflight_log"; then
  if grep -Eq 'project selector was not found|project mismatch' "$preflight_log"; then
    echo "cursor_agents_setup.new_agent_menu=retry"
    open_agents_window
    wait_for_agents_target
    "$script_dir/run_cursor_delegate.sh" "${preflight_args[@]}"
  else
    exit 1
  fi
fi

if [[ "$run_smoke" -eq 1 ]]; then
  task_id="cursor-setup-smoke-$(date +%y%m%d%H%M%S)"
  prompt_file="$tmp_dir/${task_id}.md"
  registry_file="$tmp_dir/${task_id}-registry.jsonl"
  process_file="$tmp_dir/${task_id}-process.jsonl"
  read_first_items=()
  for candidate in AGENTS.md README.md package.json; do
    if [[ -e "$workspace/$candidate" ]]; then
      read_first_items+=("- $workspace/$candidate")
    fi
  done
  if [[ "${#read_first_items[@]}" -eq 0 ]]; then
    read_first_items+=("- $workspace")
  fi
  read_first_block="$(printf '%s\n' "${read_first_items[@]}")"
  cat > "$prompt_file" <<EOF
You are a worker agent running inside this repository.

Worker:
cursor-agent

Workspace:
$workspace

Task ID:
$task_id

Goal:
Read-only smoke test for Cursor Agents setup. Confirm the agent can run in this repository.

Read first:
$read_first_block

Write scope:
- none

Forbidden:
- Do not edit files.
- Do not stage, commit, push, or create PRs.
- Do not change settings.

Verification:
- pwd
- git status --short

Final report:
- TASK_ID: $task_id
- Workspace path
- git status --short summary
- Files changed: none
EOF

  submit_args=(
    --transport mac-ide-cdp
    --workspace "$workspace"
    --cdp-endpoint "$endpoint"
    --prompt-file "$prompt_file"
    --registry-file "$registry_file"
    --process-report-file "$process_file"
    --new-agent
    --submit
  )
  if [[ -n "$expected_project" ]]; then
    submit_args+=(--expected-project "$expected_project")
  fi
  if [[ -n "$expected_model" ]]; then
    submit_args+=(--expected-model "$expected_model")
  fi
  "$script_dir/run_cursor_delegate.sh" "${submit_args[@]}"

  "$script_dir/run_cursor_delegate.sh" \
    --transport mac-ide-cdp \
    --workspace "$workspace" \
    --cdp-endpoint "$endpoint" \
    --registry-file "$registry_file" \
    --process-report-file "$process_file" \
    --monitor-registry \
    --task-id "$task_id" \
    --wait \
    --timeout "$timeout" \
    --poll-interval 3

  git -C "$workspace" status --short
fi

echo "cursor_agents_setup=ok"
