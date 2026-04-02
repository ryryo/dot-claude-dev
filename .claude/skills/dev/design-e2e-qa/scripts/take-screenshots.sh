#!/usr/bin/env bash
# design-e2e-qa: 全代表ページ × 3VP のフルページ SS + セクション分割を撮影する
#
# Usage:
#   bash .claude/skills/design-e2e-qa/scripts/take-screenshots.sh [--before-script <path>] <base_url> <page:path> [<page:path> ...]
#
# Example:
#   bash .claude/skills/design-e2e-qa/scripts/take-screenshots.sh http://localhost:4321 \
#     top:/ post-detail:/posts/example category-list:/category/tech about:/about 404:/404
#
# Output:
#   .tmp/design-e2e-qa/screenshots/{page}-{viewport}-full.jpg  (フルページ)
#   .tmp/design-e2e-qa/screenshots/{page}-{viewport}-section-*.jpg (セクション分割)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCREENSHOT_JS="$SCRIPT_DIR/screenshot.js"
OUTPUT_DIR=".tmp/design-e2e-qa/screenshots"

BEFORE_SCRIPT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --before-script)
      if [ $# -lt 2 ]; then
        echo "Usage: $0 [--before-script <path>] <base_url> <page:path> [<page:path> ...]"
        echo "Example: $0 --before-script ./before.js http://localhost:4321 top:/ post-detail:/posts/example"
        exit 1
      fi
      BEFORE_SCRIPT="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "Usage: $0 [--before-script <path>] <base_url> <page:path> [<page:path> ...]"
      echo "Example: $0 --before-script ./before.js http://localhost:4321 top:/ post-detail:/posts/example"
      exit 1
      ;;
    *)
      break
      ;;
  esac
done

if [ $# -lt 2 ]; then
  echo "Usage: $0 [--before-script <path>] <base_url> <page:path> [<page:path> ...]"
  echo "Example: $0 --before-script ./before.js http://localhost:4321 top:/ post-detail:/posts/example"
  exit 1
fi

BASE_URL="$1"
shift

# 前回のデータをクリーンアップ
if [ -d "$OUTPUT_DIR" ]; then
  echo "🧹 Cleaning up previous screenshots..."
  rm -rf "$OUTPUT_DIR"
fi
mkdir -p "$OUTPUT_DIR"

for page_path in "$@"; do
  page="${page_path%%:*}"
  path="${page_path#*:}"
  url="${BASE_URL}${path}"
  before_script_args=()

  if [ -n "$BEFORE_SCRIPT" ]; then
    before_script_args=(--before-script "$BEFORE_SCRIPT")
  fi

  echo "📸 ${page}"
  node "$SCREENSHOT_JS" "$url" \
    "${before_script_args[@]}" \
    --split-sections \
    -o "$OUTPUT_DIR/${page}-full.jpg"
done

echo ""
echo "✅ Done. Screenshots saved to $OUTPUT_DIR/"
ls -1 "$OUTPUT_DIR/"
