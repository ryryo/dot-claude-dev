#!/bin/bash
# PostToolUse hook: tasks.json の Edit/Write を検知して sync-spec-md.mjs を起動
# 発火条件を満たさない場合は silently exit 0
#
# stdin JSON payload:
#   { "tool_name": "Edit"|"Write"|"MultiEdit"|..., "tool_input": { "file_path": "..." }, ... }

set -e

# [diagnostic] Gate A1 — 一時的な debug log。Gate C4 で除去。
DEBUG_LOG="/tmp/sync-spec-md-hook-debug.log"
{
  echo "=== $(date -Iseconds) | PID $$ ==="
  echo "CLAUDE_PROJECT_DIR=${CLAUDE_PROJECT_DIR:-<unset>}"
  echo "PWD=$(pwd)"
  echo "script=$0"
} >> "$DEBUG_LOG"

INPUT=$(cat)
echo "INPUT_LEN=${#INPUT}" >> "$DEBUG_LOG"

# tool_name フィルタ
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')
case "$TOOL_NAME" in
  Edit|Write|MultiEdit)
    echo "tool_name ok ($TOOL_NAME)" >> "$DEBUG_LOG"
    ;;
  *) exit 0 ;;
esac

# file_path を取得
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')
echo "file_path=$FILE_PATH" >> "$DEBUG_LOG"
[ -z "$FILE_PATH" ] && exit 0

# tasks.json で終わらなければスキップ
case "$FILE_PATH" in
  */tasks.json)
    echo "tasks.json filter ok" >> "$DEBUG_LOG"
    ;;
  *) exit 0 ;;
esac

# 絶対パスでなければ $CLAUDE_PROJECT_DIR 経由で解決
if [[ "$FILE_PATH" != /* ]]; then
  FILE_PATH="${CLAUDE_PROJECT_DIR:-$(pwd)}/$FILE_PATH"
fi

# ファイルが存在しなければスキップ（Edit 直後は存在するはずだが保険）
[ ! -f "$FILE_PATH" ] && exit 0

# 同階層に spec.md がなければスキップ
SPEC_DIR=$(dirname "$FILE_PATH")
echo "spec_dir=$SPEC_DIR" >> "$DEBUG_LOG"
[ ! -f "$SPEC_DIR/spec.md" ] && exit 0

# sync-spec-md.mjs のパスを解決
# 1. プロジェクトの .claude/skills/dev/spec-run/scripts/ （symlink 経由）
# 2. フォールバック: $CLAUDE_SHARED_DIR または ~/dot-claude-dev
SYNC_SCRIPT="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs"
if [ ! -f "$SYNC_SCRIPT" ]; then
  SYNC_SCRIPT="${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs"
fi

if [ ! -f "$SYNC_SCRIPT" ]; then
  echo "sync-spec-md-hook: sync-spec-md.mjs not found, skipping" >&2
  exit 0
fi

# node が利用できない環境はスキップ
if ! command -v node >/dev/null 2>&1; then
  echo "sync-spec-md-hook: node not found, skipping" >&2
  exit 0
fi

# sync-spec-md.mjs を起動
# - 成功時: stderr 出力を破棄、終了コード 0
# - 失敗時: stderr を /tmp/sync-spec-md-hook.log に記録（タイムスタンプ + FILE_PATH + エラー内容）
ERR_LOG="/tmp/sync-spec-md-hook.log"
ERR_TMP=$(mktemp -t sync-spec-md-hook.XXXXXX)
if ! node "$SYNC_SCRIPT" "$FILE_PATH" 2> "$ERR_TMP"; then
  {
    echo "=== $(date -Iseconds) | PID $$ ==="
    echo "FILE_PATH=$FILE_PATH"
    cat "$ERR_TMP"
    echo ""
  } >> "$ERR_LOG"
fi
rm -f "$ERR_TMP"

exit 0
