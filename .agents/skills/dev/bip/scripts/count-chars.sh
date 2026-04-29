#!/usr/bin/env bash
# X (Twitter) 文字数カウント
# Usage:
#   echo "ツイート本文" | ./count-chars.sh
#   ./count-chars.sh "ツイート本文"
#
# ルール:
#   - 通常文字（日本語・ASCII）: 1文字 = 1カウント
#   - URL (https?://...): t.co 短縮により 23カウント固定
#   - 改行: 1カウント

if [ $# -gt 0 ]; then
    text="$*"
else
    text=$(cat)
fi

python3 -c "
import re, sys
text = sys.argv[1].rstrip('\n')
text = re.sub(r'https?://\S+', 'x' * 23, text)
print(len(text))
" "$text"
