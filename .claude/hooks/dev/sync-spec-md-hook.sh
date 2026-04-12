#!/bin/bash
# PostToolUse hook: tasks.json の Edit/Write を検知して sync-spec-md.mjs を起動
# 発火条件を満たさない場合は silently exit 0
#
# stdin JSON payload:
#   { "tool_name": "Edit"|"Write"|"MultiEdit"|..., "tool_input": { "file_path": "..." }, ... }

set -e

INPUT=$(cat)

# tool_name フィルタ
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')
case "$TOOL_NAME" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

# file_path を取得
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')
[ -z "$FILE_PATH" ] && exit 0

# tasks.json で終わらなければスキップ
case "$FILE_PATH" in
  */tasks.json) ;;
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

# sync-spec-md.mjs を起動（エラーも exit 0 で吸収）
node "$SYNC_SCRIPT" "$FILE_PATH" >&2 || {
  echo "sync-spec-md-hook: sync-spec-md.mjs failed (non-fatal), continuing" >&2
}

exit 0
