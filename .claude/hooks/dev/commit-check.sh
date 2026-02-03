#!/bin/bash
# Stop hook: 未コミットの変更がある場合、コミットするか確認を促す
# stop_hook_active=true の場合はスキップ（無限ループ防止）

INPUT=$(cat)
ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active')

if [ "$ACTIVE" = "true" ]; then
  exit 0
fi

CHANGES=$(git status --porcelain 2>/dev/null)

if [ -n "$CHANGES" ]; then
  echo "未コミットの変更があります。コミットしますか？" >&2
  exit 2
fi

exit 0
