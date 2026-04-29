#!/bin/bash
# scripts/update-gitignore.sh
# プロジェクトの .gitignore に Claude Code / Agent runtime シンボリックリンク除外エントリを追加する
#
# 使い方:
#   bash update-gitignore.sh /path/to/project
#
# 既に存在するエントリはスキップする

PROJECT="${1:?Usage: $0 /path/to/project}"
GITIGNORE="$PROJECT/.gitignore"

CLAUDE_ENTRIES=(
  ".claude/rules/workflow"
  ".claude/skills/dev"
  ".claude/commands/dev"
  ".claude/hooks/dev"
)

CODEX_ENTRIES=(
  ".codex/commands/dev"
  ".codex/skills/dev"
)

LOCAL_ENTRIES=(
  ".claude/settings.local.json"
)

ADDED=0

check_entry() {
  local ENTRY="$1"
  if grep -qxF "$ENTRY" "$GITIGNORE" 2>/dev/null; then
    echo "  skip: $ENTRY (既存)"
  else
    echo "  add:  $ENTRY"
    ADDED=$((ADDED + 1))
  fi
}

for ENTRY in "${CLAUDE_ENTRIES[@]}"; do check_entry "$ENTRY"; done
for ENTRY in "${CODEX_ENTRIES[@]}"; do check_entry "$ENTRY"; done
for ENTRY in "${LOCAL_ENTRIES[@]}"; do check_entry "$ENTRY"; done

if [ "$ADDED" -eq 0 ]; then
  echo "✓ .gitignore は既に最新です"
  exit 0
fi

# 不足エントリをまとめて追記
append_block() {
  local HEADER="$1"
  shift
  local MISSING=()
  for ENTRY in "$@"; do
    if ! grep -qxF "$ENTRY" "$GITIGNORE" 2>/dev/null; then
      MISSING+=("$ENTRY")
    fi
  done
  if [ "${#MISSING[@]}" -gt 0 ]; then
    echo ""
    echo "$HEADER"
    for ENTRY in "${MISSING[@]}"; do
      echo "$ENTRY"
    done
  fi
}

{
  append_block "# Claude Code - shared configuration (symlinks)" "${CLAUDE_ENTRIES[@]}"
  append_block "# Codex CLI - shared configuration (symlinks)" "${CODEX_ENTRIES[@]}"
  append_block "# Claude Code - local settings" "${LOCAL_ENTRIES[@]}"
} >> "$GITIGNORE"

echo "✓ .gitignore を更新しました（$ADDED 件追加）"
