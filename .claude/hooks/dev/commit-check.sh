#!/bin/bash
# Stop hook: 一定以上の変更がある場合、コミットを促す
# stop_hook_active=true の場合はスキップ（無限ループ防止）

INPUT=$(cat)
ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active')

if [ "$ACTIVE" = "true" ]; then
  exit 0
fi

# 変更行数を取得（追加+削除）
LINES=$(git diff --numstat 2>/dev/null | awk '{s+=$1+$2} END {print s+0}')
STAGED=$(git diff --cached --numstat 2>/dev/null | awk '{s+=$1+$2} END {print s+0}')
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1+0}')
TOTAL=$((LINES + STAGED + UNTRACKED))

if [ "$TOTAL" -ge 100 ]; then
  echo "未コミットの変更があります（${TOTAL}行）。/dev:simple-add でコミットしてください。" >&2
  exit 2
fi

exit 0
