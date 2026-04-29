#!/usr/bin/env bash
# X (Twitter) 文字数カウント — twitter-text v3 準拠
# Usage:
#   echo "ツイート本文" | ./count-chars.sh
#   ./count-chars.sh "ツイート本文"
#
# ルール (twitter-text v3.json):
#   maxWeightedTweetLength: 280 / scale: 100 / defaultWeight: 200
#   weight=100 (1カウント): U+0000–U+10FF, U+2000–U+200D, U+2010–U+201F, U+2032–U+2037
#   weight=200 (2カウント): それ以外（日本語・CJK・絵文字など）
#   URL (https?://...): 23カウント固定

if [ $# -gt 0 ]; then
    text="$*"
else
    text=$(cat)
fi

python3 -c "
import re, sys

text = sys.argv[1].rstrip('\n')

# URL を 23文字プレースホルダーに置換
text = re.sub(r'https?://\S+', 'U' * 23, text)

total = 0
for ch in text:
    cp = ord(ch)
    if (0x0000 <= cp <= 0x10FF or
        0x2000 <= cp <= 0x200D or
        0x2010 <= cp <= 0x201F or
        0x2032 <= cp <= 0x2037):
        total += 1   # weight 100 / scale 100
    else:
        total += 2   # weight 200 / scale 100

print(total)
" "$text"
