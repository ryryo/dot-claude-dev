#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_cursor_delegate.sh --workspace PATH --prompt-file FILE [options]
  run_cursor_delegate.sh --transport mac-ide-cdp [--cdp-endpoint URL] [--prompt-file FILE]
  run_cursor_delegate.sh --transport mac-ide-cdp --monitor-registry --task-id ID [options]
  run_cursor_delegate.sh --transport mac-ide-cdp --monitor-all [options]
  run_cursor_delegate.sh --transport mac-ide-applescript
  run_cursor_delegate.sh --transport deeplink --prompt-file FILE

Options:
  --transport VALUE        auto | mac-ide-applescript | mac-ide-cdp | deeplink (default: auto)
  --mode VALUE             ask | plan | edit (default: ask)
  --workspace PATH         Repository workspace path (default: current directory)
  --prompt-file FILE       File containing the worker prompt
  --cdp-endpoint URL       Cursor CDP endpoint (default: http://127.0.0.1:9226)
  --registry-file FILE     JSONL thread registry path (default: WORKSPACE/.agent_runs/cursor/thread-registry.jsonl)
  --no-registry            Do not write a thread registry entry on submit
  --monitor-registry       Read/switch to a registered thread and print DOM status/result JSON
  --monitor-all            Read/switch through all registered task-id threads and print a summary JSON
  --task-id ID             Task id to monitor in the registry
  --wait                   Poll until monitored thread(s) are done or timeout is reached
  --timeout SECONDS        Wait timeout for monitor modes (default: 120)
  --poll-interval SECONDS  Poll interval for monitor modes (default: 2)
  --max-candidates N       Max sidebar candidates to try per registered thread (default: 3)
  --max-records N          Max registry task records for --monitor-all (default: 8)
  --max-cdp-calls N        Max CDP protocol calls per wrapper invocation (default: 120)
  --max-clicks N           Max UI clicks per wrapper invocation (default: 6)
  --max-runtime SECONDS    Max runtime budget inside the CDP helper (default: 180)
  --max-child-processes N  Max descendant processes started by the guarded helper (default: 6)
  --process-report-file F  JSONL process audit report path (default: WORKSPACE/.agent_runs/cursor/process-audit.jsonl)
  --process-poll-interval S Process guard poll interval in seconds (default: 2)
  --no-process-guard       Skip child process monitoring
  --no-lock                Skip the workspace-level CDP lock
  --lock-timeout SECONDS   Seconds to wait for the workspace-level CDP lock (default: 5)
  --new-agent              Click New Agent before prompt insertion (mac-ide-cdp only)
  --expected-project TEXT  Fail submit if New Agent project selector does not contain TEXT
  --model-tier fast|standard Resolve expected model to composer-2.5-fast or composer-2.5
  --expected-model TEXT    Fail submit if New Agent model selector/buttons do not contain TEXT
  --clear-after-insert     Clear the prompt after read-back (mac-ide-cdp smoke tests)
  --submit                 Submit after insertion
  -h, --help               Show this help
USAGE
}

transport="auto"
mode="ask"
workspace="$PWD"
prompt_file=""
cdp_endpoint="http://127.0.0.1:9226"
registry_file=""
write_registry=1
monitor_registry=0
monitor_all=0
task_id=""
wait_for_monitor=0
timeout=120
poll_interval=2
max_candidates=3
max_records=8
max_cdp_calls=120
max_clicks=6
max_runtime=180
max_child_processes=6
process_report_file=""
process_poll_interval=2
use_process_guard=1
use_lock=1
lock_timeout=5
active_lock_dir=""
submit=0
new_agent=0
expected_project=""
expected_model=""
model_tier="${CURSOR_AGENT_MODEL_TIER:-}"
clear_after_insert=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --transport) transport="${2:?}"; shift 2 ;;
    --mode) mode="${2:?}"; shift 2 ;;
    --workspace) workspace="${2:?}"; shift 2 ;;
    --prompt-file) prompt_file="${2:?}"; shift 2 ;;
    --cdp-endpoint) cdp_endpoint="${2:?}"; shift 2 ;;
    --registry-file) registry_file="${2:?}"; shift 2 ;;
    --no-registry) write_registry=0; shift ;;
    --monitor-registry) monitor_registry=1; shift ;;
    --monitor-all) monitor_all=1; shift ;;
    --task-id) task_id="${2:?}"; shift 2 ;;
    --wait) wait_for_monitor=1; shift ;;
    --timeout) timeout="${2:?}"; shift 2 ;;
    --poll-interval) poll_interval="${2:?}"; shift 2 ;;
    --max-candidates) max_candidates="${2:?}"; shift 2 ;;
    --max-records) max_records="${2:?}"; shift 2 ;;
    --max-cdp-calls) max_cdp_calls="${2:?}"; shift 2 ;;
    --max-clicks) max_clicks="${2:?}"; shift 2 ;;
    --max-runtime) max_runtime="${2:?}"; shift 2 ;;
    --max-child-processes) max_child_processes="${2:?}"; shift 2 ;;
    --process-report-file) process_report_file="${2:?}"; shift 2 ;;
    --process-poll-interval) process_poll_interval="${2:?}"; shift 2 ;;
    --no-process-guard) use_process_guard=0; shift ;;
    --no-lock) use_lock=0; shift ;;
    --lock-timeout) lock_timeout="${2:?}"; shift 2 ;;
    --new-agent) new_agent=1; shift ;;
    --expected-project) expected_project="${2:?}"; shift 2 ;;
    --model-tier) model_tier="${2:?}"; shift 2 ;;
    --expected-model) expected_model="${2:?}"; shift 2 ;;
    --clear-after-insert) clear_after_insert=1; shift ;;
    --submit) submit=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

resolve_model_from_tier() {
  case "$1" in
    fast) printf '%s\n' "composer-2.5-fast" ;;
    standard) printf '%s\n' "composer-2.5" ;;
    *) echo "Preflight failed: --model-tier must be 'fast' or 'standard'." >&2; exit 2 ;;
  esac
}

if [[ -z "$expected_model" ]]; then
  if [[ -n "${CURSOR_AGENT_MODEL:-}" ]]; then
    expected_model="$CURSOR_AGENT_MODEL"
  elif [[ -n "$model_tier" ]]; then
    expected_model="$(resolve_model_from_tier "$model_tier")"
  fi
fi

require_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "Preflight failed: this skill's Cursor IDE transports are macOS-only" >&2
    exit 1
  fi
}

require_prompt_file() {
  if [[ -z "$prompt_file" || ! -f "$prompt_file" ]]; then
    echo "Missing or unreadable --prompt-file" >&2
    exit 2
  fi
}

acquire_lock() {
  [[ "$use_lock" -eq 1 ]] || return 0
  local lock_root lock_dir waited
  lock_root="$workspace/.agent_runs/cursor/locks"
  lock_dir="$lock_root/cdp.lock"
  mkdir -p "$lock_root"
  waited=0
  while ! mkdir "$lock_dir" 2>/dev/null; do
    if [[ -f "$lock_dir/pid" ]]; then
      local existing_pid
      existing_pid="$(cat "$lock_dir/pid" 2>/dev/null || true)"
      if [[ -n "$existing_pid" ]] && ! kill -0 "$existing_pid" 2>/dev/null; then
        rm -rf "$lock_dir"
        continue
      fi
    fi
    if [[ "$waited" -ge "$lock_timeout" ]]; then
      echo "Preflight failed: another Cursor CDP operation is already running for this workspace ($lock_dir)" >&2
      echo "Use --no-lock only for deliberate manual debugging." >&2
      exit 1
    fi
    sleep 1
    waited=$((waited + 1))
  done
  printf '%s\n' "$$" > "$lock_dir/pid"
  active_lock_dir="$lock_dir"
  trap 'if [[ -n "${active_lock_dir:-}" ]]; then rm -rf "$active_lock_dir"; fi' EXIT INT TERM
}

run_guarded() {
  local label="$1"
  shift
  if [[ "$use_process_guard" -eq 0 ]]; then
    "$@"
    return
  fi
  if [[ -z "$process_report_file" ]]; then
    process_report_file="$workspace/.agent_runs/cursor/process-audit.jsonl"
  fi
  python3 "$script_dir/process_guard.py" \
    --label "$label" \
    --max-child-processes "$max_child_processes" \
    --poll-interval "$process_poll_interval" \
    --report-file "$process_report_file" \
    -- "$@"
}

run_mac_ide_applescript() {
  require_macos

  if [[ ! -d /Applications/Cursor.app ]]; then
    echo "Preflight failed: /Applications/Cursor.app not found" >&2
    return 1
  fi
  if ! command -v osascript >/dev/null 2>&1; then
    echo "Preflight failed: osascript not found" >&2
    return 1
  fi

  workspace="$(cd "$workspace" && pwd)"

  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if ! osascript "$script_dir/cursor_ide_prompt.scpt" "focus-only"; then
    echo "Preflight failed: Cursor IDE AppleScript focus failed" >&2
    return 1
  fi
  echo "cursor_delegate.transport=mac-ide-applescript"
  echo "cursor_delegate.workspace=$workspace"
  echo "cursor_delegate.prompt_insertion=axtextarea-direct-set-not-available-on-current-cursor-agents-build"
  echo "cursor_delegate.mode=$mode"
  echo "cursor_delegate.model=Cursor IDE selected model; not programmatically verified"
  if [[ -n "$prompt_file" ]]; then
    echo "Preflight failed: mac-ide-applescript AXTextArea direct-set prompt insertion is not available on this Cursor Agents build; use --transport mac-ide-cdp for no-clipboard insertion" >&2
    return 1
  fi
}

run_mac_ide_cdp() {
  require_macos
  if ! command -v python3 >/dev/null 2>&1; then
    echo "Preflight failed: python3 required for CDP transport" >&2
    exit 1
  fi

  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  workspace="$(cd "$workspace" && pwd)"
  acquire_lock
  if [[ -z "$registry_file" ]]; then
    registry_file="$workspace/.agent_runs/cursor/thread-registry.jsonl"
  fi

  if [[ "$monitor_registry" -eq 1 || "$monitor_all" -eq 1 ]]; then
    local args=("--endpoint" "$cdp_endpoint" "--registry-file" "$registry_file" "--timeout" "$timeout" "--poll-interval" "$poll_interval" "--max-candidates" "$max_candidates" "--max-records" "$max_records" "--max-cdp-calls" "$max_cdp_calls" "--max-clicks" "$max_clicks" "--max-runtime" "$max_runtime")
    if [[ "$monitor_all" -eq 1 ]]; then
      args+=("--monitor-all")
    else
      args+=("--monitor-registry")
    fi
    if [[ -n "$task_id" ]]; then
      args+=("--task-id" "$task_id")
    fi
    if [[ "$wait_for_monitor" -eq 1 ]]; then
      args+=("--wait")
    fi
    run_guarded "cursor-cdp-monitor" python3 "$script_dir/cursor_cdp_prompt.py" "${args[@]}"
    return
  fi

  if [[ -n "$prompt_file" ]]; then
    local args=("--endpoint" "$cdp_endpoint" "--prompt-file" "$prompt_file" "--workspace" "$workspace" "--max-cdp-calls" "$max_cdp_calls" "--max-clicks" "$max_clicks" "--max-runtime" "$max_runtime")
    if [[ "$new_agent" -eq 1 ]]; then
      args+=("--new-agent")
    fi
    if [[ -n "$expected_project" ]]; then
      args+=("--expected-project" "$expected_project")
    fi
    if [[ -n "$expected_model" ]]; then
      args+=("--expected-model" "$expected_model")
    fi
    if [[ "$clear_after_insert" -eq 1 ]]; then
      args+=("--clear-after-insert")
    fi
    if [[ "$submit" -eq 1 ]]; then
      args+=("--submit")
    fi
    if [[ "$submit" -eq 1 && "$write_registry" -eq 1 ]]; then
      args+=("--registry-file" "$registry_file")
    fi
    run_guarded "cursor-cdp-submit" python3 "$script_dir/cursor_cdp_prompt.py" "${args[@]}"
    return
  fi

  if [[ -n "$expected_project" || -n "$expected_model" ]]; then
    local args=("--endpoint" "$cdp_endpoint" "--max-cdp-calls" "$max_cdp_calls" "--max-clicks" "$max_clicks" "--max-runtime" "$max_runtime")
    if [[ "$new_agent" -eq 1 ]]; then
      args+=("--new-agent")
    fi
    if [[ -n "$expected_project" ]]; then
      args+=("--expected-project" "$expected_project")
    fi
    if [[ -n "$expected_model" ]]; then
      args+=("--expected-model" "$expected_model")
    fi
    run_guarded "cursor-cdp-preflight" python3 "$script_dir/cursor_cdp_prompt.py" "${args[@]}"
    return
  fi

  python3 - "$cdp_endpoint" <<'PY'
import json
import sys
import urllib.request

endpoint = sys.argv[1].rstrip("/")

def get_json(path):
    with urllib.request.urlopen(endpoint + path, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))

version = get_json("/json/version")
targets = get_json("/json")
pages = [
    target for target in targets
    if target.get("type") == "page"
    and "devtools://" not in target.get("url", "")
    and "devtools://" not in target.get("title", "")
]

print("cursor_delegate.transport=mac-ide-cdp")
print("cursor_delegate.cdp_endpoint=" + endpoint)
print("cursor_delegate.browser_ws=" + str(version.get("webSocketDebuggerUrl", "")))
print("cursor_delegate.page_target_count=" + str(len(pages)))
for index, target in enumerate(pages):
    print(
        "cursor_delegate.page_target[{i}].id={id} title={title!r} url={url!r} ws={ws}".format(
            i=index,
            id=target.get("id", ""),
            title=target.get("title", ""),
            url=target.get("url", ""),
            ws=target.get("webSocketDebuggerUrl", ""),
        )
    )
PY
}

run_auto() {
  run_mac_ide_cdp
}

run_deeplink() {
  require_prompt_file
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
  mac-ide-applescript) run_mac_ide_applescript ;;
  mac-ide-cdp) run_mac_ide_cdp ;;
  deeplink) run_deeplink ;;
  *) echo "Invalid --transport: $transport" >&2; exit 2 ;;
esac
