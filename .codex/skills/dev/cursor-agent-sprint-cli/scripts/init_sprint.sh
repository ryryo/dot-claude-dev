#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
使い方:
  init_sprint.sh --slug SLUG [--workspace PATH]

オプション:
  --workspace PATH   repository workspace path（default: current directory）
  --slug SLUG        .codex/tmp/YYMMDD_slug 用の短い lowercase slug
  -h, --help         この help を表示
USAGE
}

workspace="$PWD"
slug=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) workspace="${2:?}"; shift 2 ;;
    --slug) slug="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "不明な引数です: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$slug" ]]; then
  echo "--slug が必要です" >&2
  usage >&2
  exit 2
fi

if [[ ! "$slug" =~ ^[a-z0-9][a-z0-9_-]{1,48}$ ]]; then
  echo "不正な --slug です: lowercase letters, digits, underscore, hyphen の 2-49 文字にしてください" >&2
  exit 2
fi

workspace="$(cd "$workspace" && pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "$script_dir/.." && pwd)"
template_dir="$skill_dir/templates"

date_prefix="$(date +%y%m%d)"
sprint_dir="$workspace/.codex/tmp/${date_prefix}_${slug}"
registry_file="$sprint_dir/thread-registry.jsonl"
process_file="$sprint_dir/process-audit.jsonl"

if [[ -e "$sprint_dir" ]]; then
  echo "Sprint directory は既に存在します: $sprint_dir" >&2
  exit 1
fi

mkdir -p "$sprint_dir/prompts" "$sprint_dir/reports"
cp "$template_dir/brief.md" "$sprint_dir/brief.md"
cp "$template_dir/tasks.md" "$sprint_dir/tasks.md"
cat > "$sprint_dir/review.md" <<'EOF'
# 検収

## 統合メモ

- <main Codex が worker output と diff を検収した結果>

## 検証

- <実行した検証と結果>

## 後片付け

- <削除した smoke / cache artifacts>
EOF
: > "$registry_file"
: > "$process_file"

cat > "$sprint_dir/sprint-env.sh" <<EOF
export WORKSPACE=$(printf '%q' "$workspace")
export SKILL_DIR=$(printf '%q' "$skill_dir")
export SPRINT_DIR=$(printf '%q' "$sprint_dir")
export REGISTRY_FILE=$(printf '%q' "$registry_file")
export PROCESS_FILE=$(printf '%q' "$process_file")
EOF

printf 'cursor_agent_sprint_cli.workspace=%s\n' "$workspace"
printf 'cursor_agent_sprint_cli.skill_dir=%s\n' "$skill_dir"
printf 'cursor_agent_sprint_cli.sprint_dir=%s\n' "$sprint_dir"
printf 'cursor_agent_sprint_cli.registry_file=%s\n' "$registry_file"
printf 'cursor_agent_sprint_cli.process_file=%s\n' "$process_file"
printf 'cursor_agent_sprint_cli.env_file=%s\n' "$sprint_dir/sprint-env.sh"
