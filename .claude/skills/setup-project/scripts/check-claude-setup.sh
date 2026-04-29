#!/bin/bash
# .claude/skills/setup-project/scripts/check-claude-setup.sh
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

# bash 3.2 互換: 連想配列を使わず並列配列で管理
LINK_NAMES=(
  ".claude/rules/workflow"
  ".claude/skills/dev"
  ".claude/commands/dev"
  ".claude/hooks/dev"
  ".agents/commands/dev"
  ".agents/skills/dev"
)
LINK_TARGETS=(
  "$SHARED/.claude/rules/workflow"
  "$SHARED/.claude/skills/dev"
  "$SHARED/.claude/commands/dev"
  "$SHARED/.claude/hooks/dev"
  "$SHARED/.agents/commands/dev"
  "$SHARED/.agents/skills/dev"
)

ALL_OK=true
SHOWED_HINT=false

echo "## Claude セットアップ確認: $PROJECT"
echo "共有ディレクトリ: $SHARED"
echo ""
printf "%-35s %-10s %s\n" "リンク" "状態" "参照先"
printf "%-35s %-10s %s\n" "---" "---" "---"

for i in "${!LINK_NAMES[@]}"; do
  LINK="${LINK_NAMES[$i]}"
  TARGET="${LINK_TARGETS[$i]}"
  ACTUAL=$(readlink "$PROJECT/$LINK" 2>/dev/null)

  if [ -z "$ACTUAL" ]; then
    printf "%-35s %-10s %s\n" "$LINK" "未リンク" "-"
    ALL_OK=false
  elif [ "$ACTUAL" = "$TARGET" ]; then
    printf "%-35s %-10s %s\n" "$LINK" "OK" "$ACTUAL"
  else
    printf "%-35s %-10s %s\n" "$LINK" "別パス" "$ACTUAL"
    ALL_OK=false
    case "$ACTUAL" in
      */dot-claude-dev/*|*/.dot-claude-dev/*)
        if [ "$SHOWED_HINT" != "true" ]; then
          echo ""
          echo "  ⚠️  リンク先の dot-claude-dev が想定と異なります。"
          ACTUAL_BASE=$(echo "$ACTUAL" | sed -E 's|/.claude/.*||')
          echo "      実際の配置: $ACTUAL_BASE"
          echo "      想定の配置: $SHARED"
          echo ""
          echo "      [修正方法] CLAUDE_SHARED_DIR を実際の配置に合わせて永続化:"
          echo "        echo 'export CLAUDE_SHARED_DIR=\"$ACTUAL_BASE\"' >> ~/.zshrc"
          echo "        source ~/.zshrc"
          echo "        bash \"\$CLAUDE_SHARED_DIR/scripts/setup-claude.sh\""
          SHOWED_HINT=true
        fi
        ;;
    esac
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
