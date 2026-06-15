#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_cursor_delegate.sh --mode ask|plan|edit --workspace PATH --prompt-file FILE [options]
  run_cursor_delegate.sh --transport auto --mode ask|plan|edit --workspace PATH --prompt-file FILE [options]
  run_cursor_delegate.sh --transport cli --mode ask|plan|edit --workspace PATH --prompt-file FILE [options]
  run_cursor_delegate.sh --transport mac-ide-applescript --workspace PATH --prompt-file FILE [options]
  run_cursor_delegate.sh --transport deeplink --prompt-file FILE

Options:
  --transport VALUE        auto | cli | mac-ide-applescript | deeplink (default: auto)
  --mode VALUE             ask | plan | edit (default: ask)
  --workspace PATH         Repository workspace path (default: current directory)
  --prompt-file FILE       File containing the worker prompt (required)
  --model VALUE            Cursor model (default: composer-2.5)
  --log FILE               Log path for CLI edit mode
  --allow-wsl-mnt          Allow WSL workspaces under /mnt/*
  --submit                 Submit the prompt in Cursor IDE after pasting (mac-ide-applescript only)
  -h, --help               Show this help
USAGE
}

transport="auto"
mode="ask"
workspace="$PWD"
prompt_file=""
model="composer-2.5"
log_file=""
allow_wsl_mnt=0
submit=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --transport) transport="${2:?}"; shift 2 ;;
    --mode) mode="${2:?}"; shift 2 ;;
    --workspace) workspace="${2:?}"; shift 2 ;;
    --prompt-file) prompt_file="${2:?}"; shift 2 ;;
    --model) model="${2:?}"; shift 2 ;;
    --log) log_file="${2:?}"; shift 2 ;;
    --allow-wsl-mnt) allow_wsl_mnt=1; shift ;;
    --submit) submit=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$prompt_file" || ! -f "$prompt_file" ]]; then
  echo "Missing or unreadable --prompt-file" >&2
  exit 2
fi

workspace="$(cd "$workspace" && pwd)"
prompt="$(< "$prompt_file")"

is_wsl() {
  [[ "$(uname -s)" == "Linux" ]] && grep -qi microsoft /proc/version 2>/dev/null
}

print_metadata_from_log() {
  local file="$1"
  command -v python3 >/dev/null 2>&1 || return 0
  python3 - "$file" <<'PY' || true
import json
import sys

path = sys.argv[1]
system = None
result = None
try:
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                event = json.loads(line)
            except Exception:
                continue
            if event.get("type") == "system" and event.get("subtype") == "init":
                system = event
            elif event.get("type") == "result":
                result = event
except FileNotFoundError:
    sys.exit(0)

if system:
    print("cursor_delegate.system_model=" + str(system.get("model", "")))
    print("cursor_delegate.session_id=" + str(system.get("session_id", "")))
if result:
    print("cursor_delegate.result_subtype=" + str(result.get("subtype", "")))
    print("cursor_delegate.duration_ms=" + str(result.get("duration_ms", "")))
PY
}

run_cli() {
  if ! command -v agent >/dev/null 2>&1; then
    echo "Preflight failed: agent command not found" >&2
    exit 1
  fi

  if is_wsl && [[ "$workspace" == /mnt/* && "$allow_wsl_mnt" -ne 1 ]]; then
    echo "Preflight warning: WSL workspace is under /mnt/*. Prefer Linux filesystem paths or pass --allow-wsl-mnt." >&2
  fi

  echo "cursor_delegate.transport=cli"
  echo "cursor_delegate.workspace=$workspace"
  echo "cursor_delegate.model_requested=$model"

  agent status >/dev/null
  if ! agent models | awk '{print $1}' | grep -Fxq "$model"; then
    echo "Preflight failed: model not available: $model" >&2
    exit 1
  fi

  git -C "$workspace" status --short

  case "$mode" in
    ask|plan)
      agent -p \
        --mode "$mode" \
        --workspace "$workspace" \
        --model "$model" \
        --output-format text \
        "$prompt"
      ;;
    edit)
      if [[ -z "$log_file" ]]; then
        log_file="${TMPDIR:-/tmp}/cursor-delegate-$(date +%Y%m%d-%H%M%S).ndjson"
      fi
      agent -p \
        --force \
        --trust \
        --workspace "$workspace" \
        --model "$model" \
        --output-format stream-json \
        --stream-partial-output \
        "$prompt" | tee "$log_file"
      echo "cursor_delegate.log=$log_file"
      print_metadata_from_log "$log_file"
      ;;
    *)
      echo "Invalid --mode for cli: $mode" >&2
      exit 2
      ;;
  esac
}

run_mac_ide_applescript() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "mac-ide-applescript transport is macOS only" >&2
    return 1
  fi
  if [[ ! -d /Applications/Cursor.app ]]; then
    echo "Preflight failed: /Applications/Cursor.app not found" >&2
    return 1
  fi
  if ! command -v osascript >/dev/null 2>&1; then
    echo "Preflight failed: osascript not found" >&2
    return 1
  fi

  local script_dir
  local submit_arg="no-submit"
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ "$submit" -eq 1 ]]; then
    submit_arg="submit"
  fi
  if ! osascript "$script_dir/cursor_ide_prompt.scpt" "$prompt_file" "$submit_arg"; then
    echo "Preflight failed: Cursor IDE AppleScript prompt insertion failed" >&2
    return 1
  fi
  echo "cursor_delegate.transport=mac-ide-applescript"
  echo "cursor_delegate.submitted=$submit_arg"
  echo "cursor_delegate.model=Cursor IDE selected model; not programmatically verified"
}

run_auto() {
  if [[ "$(uname -s)" == "Darwin" ]]; then
    if run_mac_ide_applescript; then
      return 0
    fi
    echo "cursor_delegate.fallback=cli" >&2
    run_cli
    return
  fi

  run_cli
}

run_deeplink() {
  command -v python3 >/dev/null 2>&1 || {
    echo "Preflight failed: python3 required for deeplink encoding" >&2
    exit 1
  }
  python3 - "$prompt_file" <<'PY'
import pathlib
import sys
import urllib.parse

text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
print("cursor://anysphere.cursor-deeplink/prompt?text=" + urllib.parse.quote(text))
PY
}

case "$transport" in
  auto) run_auto ;;
  cli) run_cli ;;
  mac-ide-applescript) run_mac_ide_applescript ;;
  deeplink) run_deeplink ;;
  *) echo "Invalid --transport: $transport" >&2; exit 2 ;;
esac
