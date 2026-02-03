#!/bin/bash
# SessionStart Hook - TODO.mdまたは最近の進行中ストーリーの進捗を表示

# カレントディレクトリにTODO.mdが存在するかチェック
if [ -f "TODO.md" ]; then
  echo "📝 ストーリーセッションを検出しました"
  echo ""

  # Last Updatedを抽出して表示
  LAST_UPDATED=$(grep -m 1 "^\*\*Last Updated\*\*:" TODO.md | sed 's/^\*\*Last Updated\*\*: //')
  if [ -n "$LAST_UPDATED" ]; then
    echo "**最終更新**: $LAST_UPDATED"
  else
    echo "**最終更新**: unknown"
  fi
  echo ""

  # 進捗サマリーを表示
  TOTAL=$(grep -c "^- \[" TODO.md)
  COMPLETED=$(grep -c "^- \[x\]" TODO.md)
  IN_PROGRESS=$(grep -c "^- \[~\]" TODO.md)
  PENDING=$((TOTAL - COMPLETED - IN_PROGRESS))

  echo "**進捗**: $COMPLETED/$TOTAL 完了, $IN_PROGRESS 進行中, $PENDING 未着手"
  echo ""

  # Blockersセクションをチェック
  if grep -q "^## Blockers" TODO.md; then
    echo "⚠️  **ブロッカーが検出されました** - 継続前にBlockersセクションを確認してください"
    echo ""
    # Blockersセクションを表示
    sed -n '/^## Blockers/,/^##/p' TODO.md | sed '$d'
    echo ""
  fi

# プロジェクトルートでin-progress-stories.tmpが存在するかチェック
elif [ -f "$HOME/.claude/sessions/in-progress-stories.tmp" ]; then
  # プロジェクトルートにいる可能性が高い場合のみ表示（CLAUDE.mdで判定）
  if [ -f "CLAUDE.md" ]; then
    echo "📋 最近の進行中ストーリー"
    echo ""
    cat "$HOME/.claude/sessions/in-progress-stories.tmp"
    echo ""
    echo "💡 ヒント: ストーリーディレクトリに移動して作業を再開するか、/dev:storyで新しいストーリーを開始してください"
    echo ""
  fi
fi
