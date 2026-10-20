#!/bin/sh
# X の投稿・プロフィールを r.jina.ai 経由で開き、読めるテキストにする。
#
#   使い方: x-open.sh https://x.com/<user>/status/<id>
#           x-open.sh @<handle>
#           x-open.sh <handle>
#
# 依存: curl, python3。
# 環境変数: JINA_API_KEY があれば認証付きで取得する（匿名枠のブロック回避）。
# 終了コード: 0 成功 / 2 取得失敗（ブロック・空応答） / 64 引数なし / 1 その他
# テスト: X_OPEN_FIXTURE=<保存済み応答> を付けると通信せずその内容を整形する。
set -eu

if [ $# -lt 1 ]; then
  echo "usage: $0 <tweet-url | @handle | handle>" >&2
  exit 64
fi

target=$1
case "$target" in
  http://*|https://*) : ;;
  @*) target="https://x.com/${target#@}" ;;
  *)  target="https://x.com/${target}" ;;
esac
# 追跡パラメータを落とす
target=$(printf '%s' "$target" | sed 's/?.*$//')

if [ -n "${X_OPEN_FIXTURE:-}" ]; then
  [ -f "$X_OPEN_FIXTURE" ] || { echo "fixture が見つからない: $X_OPEN_FIXTURE" >&2; exit 64; }
  raw=$(cat "$X_OPEN_FIXTURE")
elif [ -n "${JINA_API_KEY:-}" ]; then
  # キーはローカルに保持し、出力しない
  raw=$(curl -sS --max-time 45 -A 'Mozilla/5.0' \
    -H "Authorization: Bearer $JINA_API_KEY" "https://r.jina.ai/$target")
else
  raw=$(curl -sS --max-time 45 -A 'Mozilla/5.0' "https://r.jina.ai/$target")
fi

printf '%s' "$raw" | python3 -c '
import re, sys

raw = sys.stdin.read()
if not raw.strip():
    print("空の応答。時間を置くか経路を変える。", file=sys.stderr)
    sys.exit(2)

if "AbuseAlleviationError" in raw or "\"code\":403" in raw:
    until = "不明"
    if "blocked until " in raw:
        until = raw.split("blocked until ", 1)[1].split(" due to", 1)[0]
    print("r.jina.ai が x.com への匿名アクセスを一時ブロック中（403）。解除: %s" % until, file=sys.stderr)
    print("対策: 解除まで待つ / JINA_API_KEY を設定して認証で使う / lite DDG のスニペットで代替し本文未確認と記録する", file=sys.stderr)
    sys.exit(2)

title = re.search(r"^Title:\s*(.+)$", raw, re.M)
pub = re.search(r"^Published Time:\s*(.+)$", raw, re.M)

body = raw.split("Markdown Content:", 1)[-1]
body = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body)                  # 画像
body = re.sub(r"\[([^\]]*)\]\((?:https?://[^)]*)\)", r"\1", body) # リンク→文言
body = re.sub(r"[ \t]+", " ", body)
body = re.sub(r"\n{3,}", "\n\n", body).strip()

# X の全ページ末尾にはログイン導線が入るので、そこを本文の終端として扱い
# 手前の内容量で「本文が取れたか」を判定する
cut = body.find("## Log in or sign up for X")
head = body[:cut] if cut != -1 else body
head = head.strip()

if title:
    print("Title:", title.group(1))
if pub:
    print("Published:", pub.group(1))
print()
if len(re.sub(r"\s", "", head)) >= 40:
    print(head[:6000])
else:
    print("NOTE: 本文が取れていない（ログイン壁のみ）。スニペットで代替し、本文未確認と記録する。")
    if head:
        print()
        print(head[:1000])
'
