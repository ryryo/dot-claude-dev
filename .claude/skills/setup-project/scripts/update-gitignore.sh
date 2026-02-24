#!/bin/bash
# scripts/update-gitignore.sh
# プロジェクトの .gitignore に Claude Code シンボリックリンク除外エントリを追加する
#
# 使い方:
#   bash update-gitignore.sh /path/to/project
#
# 既に存在するエントリはスキップする

PROJECT="${1:?Usage: $0 /path/to/project}"
GITIGNORE="$PROJECT/.gitignore"

ENTRIES=(
  "# Claude Code - shared configuration (symlinks)"
  ".claude/rules/workflow"
  ".claude/skills/dev"
  ".claude/commands/dev"
  ".claude/hooks/dev"
  ""
  "# Claude Code - local settings"
  ".claude/settings.local.json"
)

ADDED=0

for ENTRY in "${ENTRIES[@]}"; do
  # コメント行・空行は重複チェックせず末尾に追加（ただし既にブロックごと存在する場合はスキップ）
  if [[ "$ENTRY" == "#"* ]] || [[ -z "$ENTRY" ]]; then
    continue
  fi
  if grep -qxF "$ENTRY" "$GITIGNORE" 2>/dev/null; then
    echo "  skip: $ENTRY (既存)"
  else
    echo "  add:  $ENTRY"
    ADDED=$((ADDED + 1))
  fi
done

if [ "$ADDED" -eq 0 ]; then
  echo "✓ .gitignore は既に最新です"
  exit 0
fi

# 不足エントリをまとめて追記
{
  echo ""
  echo "# Claude Code - shared configuration (symlinks)"
  for ENTRY in "${ENTRIES[@]:1:4}"; do
    grep -qxF "$ENTRY" "$GITIGNORE" 2>/dev/null || echo "$ENTRY"
  done
  echo ""
  echo "# Claude Code - local settings"
  grep -qxF ".claude/settings.local.json" "$GITIGNORE" 2>/dev/null || echo ".claude/settings.local.json"
} >> "$GITIGNORE"

echo "✓ .gitignore を更新しました（$ADDED 件追加）"
