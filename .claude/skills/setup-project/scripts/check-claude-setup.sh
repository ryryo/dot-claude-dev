#!/bin/bash
# scripts/check-claude-setup.sh
# プロジェクトの .claude/ シンボリックリンクが dot-claude-dev を正しく指しているか確認する
#
# 使い方:
#   bash check-claude-setup.sh /path/to/project
#
# 終了コード:
#   0 = 全リンク正常
#   1 = 未リンクまたは別パスを指しているリンクあり

PROJECT="${1:?Usage: $0 /path/to/project}"
SHARED="${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}"

declare -A LINKS=(
  [".claude/rules/workflow"]="$SHARED/.claude/rules/workflow"
  [".claude/skills/dev"]="$SHARED/.claude/skills/dev"
  [".claude/commands/dev"]="$SHARED/.claude/commands/dev"
  [".claude/hooks/dev"]="$SHARED/.claude/hooks/dev"
)

ALL_OK=true

echo "## Claude セットアップ確認: $PROJECT"
echo "共有ディレクトリ: $SHARED"
echo ""
printf "%-35s %-10s %s\n" "リンク" "状態" "参照先"
printf "%-35s %-10s %s\n" "---" "---" "---"

for LINK in "${!LINKS[@]}"; do
  TARGET="${LINKS[$LINK]}"
  ACTUAL=$(readlink "$PROJECT/$LINK" 2>/dev/null)

  if [ -z "$ACTUAL" ]; then
    printf "%-35s %-10s %s\n" "$LINK" "未リンク" "-"
    ALL_OK=false
  elif [ "$ACTUAL" = "$TARGET" ]; then
    printf "%-35s %-10s %s\n" "$LINK" "OK" "$ACTUAL"
  else
    printf "%-35s %-10s %s\n" "$LINK" "別パス" "$ACTUAL"
    ALL_OK=false
  fi
done

echo ""
if $ALL_OK; then
  echo "✓ 全リンク正常"
  exit 0
else
  echo "⚠️  未設定または別パスのリンクがあります"
  exit 1
fi
