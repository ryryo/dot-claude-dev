#!/bin/sh
# X(Twitter) 投稿の検索。DuckDuckGo lite 経由で検索し、実投稿 URL とタイトル・本文スニペットを取り出す。
#
#   使い方: x-search.sh 'site:x.com "model-id" 1017'
#           x-search.sh 'site:x.com @product いつ 対応'
#
# 依存: curl, python3。
# 終了コード: 0 成功 / 2 captcha・レート制限（時間を置くか経路を変える） / 64 引数なし / 1 その他
# テスト: X_SEARCH_FIXTURE=<保存済みHTML> を付けると通信せずその HTML を解析する。
set -eu

if [ $# -lt 1 ]; then
  echo "usage: $0 '<query>'" >&2
  exit 64
fi

if [ -n "${X_SEARCH_FIXTURE:-}" ]; then
  [ -f "$X_SEARCH_FIXTURE" ] || { echo "fixture が見つからない: $X_SEARCH_FIXTURE" >&2; exit 64; }
  body=$(cat "$X_SEARCH_FIXTURE")
  code=200
else
  q=$(python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$1")
  resp=$(curl -sS --max-time 30 -A 'Mozilla/5.0' -w '\n%{http_code}' \
    "https://lite.duckduckgo.com/lite/?q=$q")
  code=$(printf '%s' "$resp" | tail -n 1)
  body=$(printf '%s' "$resp" | sed '$d')
fi

case "$code" in
  200) : ;;
  202|403|429)
    echo "captcha/rate-limit: HTTP $code。時間を置くか経路を変える。" >&2
    exit 2 ;;
  *)
    echo "unexpected HTTP $code" >&2
    exit 1 ;;
esac

printf '%s' "$body" | python3 -c '
import html, re, sys, urllib.parse

raw = sys.stdin.read()
if "Select all squares" in raw or "/challenge/" in raw or "tqadb" in raw:
    print("captcha: この HTML は challenge ページ。時間を置くか経路を変える。", file=sys.stderr)
    sys.exit(2)

def clean(fragment):
    text = html.unescape(re.sub(r"<[^>]+>", " ", fragment))
    return re.sub(r"\s+", " ", text).strip()

# <tr で分割すると各断片の先頭に開始タグの残り（">" まで）が残るので取り除く
rows = [r if i == 0 else re.sub(r"^[^>]*>", "", r) for i, r in enumerate(re.split(r"<tr", raw))]
seen, items = set(), []
for i, row in enumerate(rows):
    m = re.search(r"uddg=([^&\"]+)", row)
    if not m:
        continue
    url = urllib.parse.unquote(html.unescape(m.group(1)))
    if not re.match(r"^https?://(www\.)?x\.com/[^/]+/status/\d+", url):
        continue
    url = re.sub(r"\?.*$", "", url)
    if url in seen:
        continue
    seen.add(url)

    parts = [clean(row)]
    if i + 1 < len(rows) and "uddg=" not in rows[i + 1]:
        parts.append(clean(rows[i + 1]))
    text = " ".join(p for p in parts if p)
    text = re.sub(r"^[>\s]*\d+[.)]\s*", "", text)
    text = re.sub(r"\s*(https?://)?x\.com/\S+\s*$", "", text)
    if len(text) > 500:
        text = text[:500] + "…"
    items.append((url, text))

for url, text in items:
    print(url)
    print("    " + text)
print("[%d 件] lite.duckduckgo.com" % len(items), file=sys.stderr)
'
