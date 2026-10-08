#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

usage() {
  cat <<'USAGE'
使い方:
  run_cursor_cli_delegate.sh --workspace PATH --preflight [options]
  run_cursor_cli_delegate.sh --workspace PATH --prompt-file FILE --submit [options]
  run_cursor_cli_delegate.sh --workspace PATH --monitor-registry --task-id ID [options]
  run_cursor_cli_delegate.sh --workspace PATH --monitor-all [options]

オプション:
  --workspace PATH          repository workspace path（default: current directory）
  --prompt-file FILE        worker prompt file
  --registry-file FILE      JSONL registry path
  --preflight               cursor agent CLI、model、login、read-only smoke を確認
  --submit                  Cursor CLI worker を background 起動
  --monitor-registry        --task-id で 1 task を監視
  --monitor-all             最新 registry task records をまとめて監視
  --task-id ID              --monitor-registry の対象 task id
  --wait                    監視対象が完了または timeout するまで poll
  --timeout SECONDS         wait timeout（default: 120）
  --poll-interval SECONDS   poll interval（default: 2）
  --max-records N           --monitor-all の最大 registry task 数（default: 8）
  -h, --help                この help を表示
USAGE
}

workspace="$PWD"
prompt_file=""
registry_file=""
preflight=0
submit=0
monitor_registry=0
monitor_all=0
task_id=""
wait_for_monitor=0
timeout=120
poll_interval=2
max_records=8

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) workspace="${2:?}"; shift 2 ;;
    --prompt-file) prompt_file="${2:?}"; shift 2 ;;
    --registry-file) registry_file="${2:?}"; shift 2 ;;
    --preflight) preflight=1; shift ;;
    --submit) submit=1; shift ;;
    --monitor-registry) monitor_registry=1; shift ;;
    --monitor-all) monitor_all=1; shift ;;
    --task-id) task_id="${2:?}"; shift 2 ;;
    --wait) wait_for_monitor=1; shift ;;
    --timeout) timeout="${2:?}"; shift 2 ;;
    --poll-interval) poll_interval="${2:?}"; shift 2 ;;
    --max-records) max_records="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "不明な引数です: $1" >&2; usage >&2; exit 2 ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace="$(cd "$workspace" && pwd)"

if [[ -z "$registry_file" ]]; then
  registry_file="$workspace/.agent_runs/cursor-cli/thread-registry.jsonl"
fi

args=(
  --workspace "$workspace"
  --registry-file "$registry_file"
  --timeout "$timeout"
  --poll-interval "$poll_interval"
  --max-records "$max_records"
)

if [[ "$preflight" -eq 1 ]]; then
  args+=(--preflight)
fi
if [[ "$submit" -eq 1 ]]; then
  if [[ -z "$prompt_file" || ! -f "$prompt_file" ]]; then
    echo "--prompt-file がないか読めません" >&2
    exit 2
  fi
  args+=(--prompt-file "$prompt_file" --submit)
fi
if [[ "$monitor_registry" -eq 1 ]]; then
  args+=(--monitor-registry)
fi
if [[ "$monitor_all" -eq 1 ]]; then
  args+=(--monitor-all)
fi
if [[ -n "$task_id" ]]; then
  args+=(--task-id "$task_id")
fi
if [[ "$wait_for_monitor" -eq 1 ]]; then
  args+=(--wait)
fi

python3 "$script_dir/cursor_cli_delegate.py" "${args[@]}"
