#!/usr/bin/env bash
# design-e2e-qa: 全代表ページ × 3VP のフルページ SS + セクション分割を撮影する
#
# Usage:
#   bash .claude/skills/design-e2e-qa/scripts/take-screenshots.sh <base_url> <page:path> [<page:path> ...]
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

# ビューポート定義: name:width:height
VIEWPORTS=(
  "desktop:1440:2560"
  "tablet:768:1024"
  "mobile:390:844"
)

if [ $# -lt 2 ]; then
  echo "Usage: $0 <base_url> <page:path> [<page:path> ...]"
  echo "Example: $0 http://localhost:4321 top:/ post-detail:/posts/example"
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

  for vp in "${VIEWPORTS[@]}"; do
    vp_name="${vp%%:*}"
    rest="${vp#*:}"
    width="${rest%%:*}"
    height="${rest#*:}"
    output="$OUTPUT_DIR/${page}-${vp_name}-full.jpg"

    echo "📸 ${page} (${vp_name}: ${width}x${height})"
    node "$SCREENSHOT_JS" "$url" \
      --width "$width" --height "$height" \
      --split-sections \
      -o "$output"
  done
done

echo ""
echo "✅ Done. Screenshots saved to $OUTPUT_DIR/"
ls -1 "$OUTPUT_DIR/"
