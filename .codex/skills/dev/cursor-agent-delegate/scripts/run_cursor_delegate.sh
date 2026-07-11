#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

usage() {
  cat <<'USAGE'
Usage:
  run_cursor_delegate.sh --workspace PATH --prompt-file FILE --submit [options]
  run_cursor_delegate.sh --workspace PATH --monitor-registry --task-id ID [options]
  run_cursor_delegate.sh --workspace PATH --monitor-all [options]
  run_cursor_delegate.sh --workspace PATH --preflight [options]

Options:
  --workspace PATH          Repository workspace (default: current directory)
  --prompt-file FILE        Cursor CLI worker prompt
  --registry-file FILE      JSONL registry path
  --submit                  Start one Cursor CLI worker in the background
  --monitor-registry        Monitor one task selected by --task-id
  --monitor-all             Monitor latest task records
  --preflight               Check CLI connectivity; use only after a CLI-level failure
  --validate-prompt         Validate Task Summary and Task ID without submitting
  --task-id ID              Task selected by --monitor-registry
  --wait                    Poll until completion, failure, or timeout
  --timeout SECONDS         Wait timeout (default: 120)
  --poll-interval SECONDS   Poll interval (default: 2)
  --max-records N           Maximum tasks for --monitor-all (default: 8)
  -h, --help                Show this help
USAGE
}

workspace="$PWD"
prompt_file=""
registry_file=""
action=""
task_id=""
wait_for_monitor=0
timeout=120
poll_interval=2
max_records=8

set_action() {
  if [[ -n "$action" ]]; then
    echo "Choose exactly one action" >&2
    exit 2
  fi
  action="$1"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) workspace="${2:?}"; shift 2 ;;
    --prompt-file) prompt_file="${2:?}"; shift 2 ;;
    --registry-file) registry_file="${2:?}"; shift 2 ;;
    --submit) set_action submit; shift ;;
    --monitor-registry) set_action monitor-registry; shift ;;
    --monitor-all) set_action monitor-all; shift ;;
    --preflight) set_action preflight; shift ;;
    --validate-prompt) set_action validate-prompt; shift ;;
    --task-id) task_id="${2:?}"; shift 2 ;;
    --wait) wait_for_monitor=1; shift ;;
    --timeout) timeout="${2:?}"; shift 2 ;;
    --poll-interval) poll_interval="${2:?}"; shift 2 ;;
    --max-records) max_records="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$action" ]]; then
  echo "Choose one action" >&2
  usage >&2
  exit 2
fi

workspace="$(cd "$workspace" && pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "$registry_file" ]]; then
  registry_file="$workspace/.agent_runs/cursor-delegate/thread-registry.jsonl"
fi

args=(
  --workspace "$workspace"
  --registry-file "$registry_file"
  --timeout "$timeout"
  --poll-interval "$poll_interval"
  --max-records "$max_records"
  "--$action"
)

if [[ -n "$prompt_file" ]]; then
  if [[ ! -f "$prompt_file" ]]; then
    echo "Prompt file does not exist: $prompt_file" >&2
    exit 2
  fi
  args+=(--prompt-file "$prompt_file")
fi
if [[ -n "$task_id" ]]; then
  args+=(--task-id "$task_id")
fi
if [[ "$wait_for_monitor" -eq 1 ]]; then
  args+=(--wait)
fi

python3 "$script_dir/cursor_cli_delegate.py" "${args[@]}"
