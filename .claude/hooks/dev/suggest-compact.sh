#!/bin/bash
# PreToolUse Hook - ツール呼び出し数に基づいて/compact提案を表示

# PID固有のカウンターファイル
COUNTER_FILE="/tmp/claude-tool-count-$$"

# カウンターを初期化または読み込み
if [ -f "$COUNTER_FILE" ]; then
  COUNT=$(cat "$COUNTER_FILE")
else
  COUNT=0
fi

# カウントをインクリメント
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"

# 50回目で初回提案
if [ "$COUNT" -eq 50 ]; then
  echo ""
  echo "💡 ツール呼び出しが50回に達しました - フェーズ移行時には /compact を検討してください"
  echo ""
fi

# 75回以降、25回ごとに再提案
if [ "$COUNT" -ge 75 ] && [ $(( (COUNT - 75) % 25 )) -eq 0 ]; then
  echo ""
  echo "💡 ツール呼び出しが${COUNT}回に達しました - コンテキストが古い場合は /compact を検討してください"
  echo ""
fi
