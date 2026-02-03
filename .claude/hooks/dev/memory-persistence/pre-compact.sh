#!/bin/bash
# PreCompact Hook - TODO.mdのLast Updatedとin-progress-stories.tmpを更新

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# TODO.mdが存在する場合、Last Updatedを更新
if [ -f "TODO.md" ]; then
  if grep -q "^\*\*Last Updated\*\*:" TODO.md; then
    # 既存のLast Updated行を更新
    sed -i '' "s/^\*\*Last Updated\*\*: .*$/\*\*Last Updated\*\*: $TIMESTAMP/" TODO.md
    echo "[PreCompact] Updated TODO.md Last Updated: $TIMESTAMP"
  else
    # Last Updated行が存在しない場合、1行目の後に追加
    sed -i '' "1a\\
\\
\*\*Last Updated\*\*: $TIMESTAMP\\
" TODO.md
    echo "[PreCompact] Added Last Updated to TODO.md: $TIMESTAMP"
  fi
fi

# プロジェクトルートを検出（CLAUDE.mdがあるディレクトリ）
if [ -f "CLAUDE.md" ]; then
  PROJECT_ROOT=$(pwd)
elif git rev-parse --show-toplevel > /dev/null 2>&1; then
  PROJECT_ROOT=$(git rev-parse --show-toplevel)
else
  PROJECT_ROOT=$(pwd)
fi

# 進行中のストーリー一覧を生成
# TODO.mdがあり、未完了タスクが存在するディレクトリを検索
STORIES_LIST="$HOME/.claude/sessions/in-progress-stories.tmp"
: > "$STORIES_LIST"  # ファイルを空にする

find "$PROJECT_ROOT" -name "TODO.md" -type f | while read -r todo_file; do
  # 未完了タスクが存在するかチェック
  if grep -q "^- \[ \]" "$todo_file" || grep -q "^- \[~\]" "$todo_file"; then
    STORY_DIR=$(dirname "$todo_file")
    REL_PATH=${STORY_DIR#$PROJECT_ROOT/}

    # 進捗情報を取得
    TOTAL=$(grep -c "^- \[" "$todo_file")
    COMPLETED=$(grep -c "^- \[x\]" "$todo_file")
    PROGRESS="$COMPLETED/$TOTAL"

    # Last Updatedを取得
    LAST_UPDATED=$(grep -m 1 "^\*\*Last Updated\*\*:" "$todo_file" | sed 's/^\*\*Last Updated\*\*: //')
    if [ -z "$LAST_UPDATED" ]; then
      LAST_UPDATED="unknown"
    fi

    echo "- $REL_PATH ($PROGRESS completed, updated: $LAST_UPDATED)" >> "$STORIES_LIST"
  fi
done

if [ -s "$STORIES_LIST" ]; then
  echo "[PreCompact] Updated in-progress stories list: $(wc -l < "$STORIES_LIST" | tr -d ' ') stories"
fi
