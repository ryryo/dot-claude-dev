#!/usr/bin/env bash
set -euo pipefail

# Usage: init-story-workspace.sh <feature-slug> <story-slug>
#   Creates docs/FEATURES/{feature-slug}/{YYMMDD}_{story-slug}/ with template files.
#   Outputs the created workspace path to stdout (last line).

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <feature-slug> <story-slug>" >&2
  exit 1
fi

FEATURE_SLUG="$1"
STORY_SLUG="$2"
DATE=$(date +%y%m%d)
WORKSPACE="docs/FEATURES/${FEATURE_SLUG}/${DATE}_${STORY_SLUG}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES_DIR="$SKILL_DIR/references/templates"

# ディレクトリ作成
mkdir -p "$WORKSPACE"

# テンプレート雛形を配置（既存ファイルがなければ）
for tmpl in story-analysis task-list; do
  dest="$WORKSPACE/${tmpl}.json"
  if [[ ! -f "$dest" ]]; then
    cp "$TEMPLATES_DIR/${tmpl}.template.json" "$dest"
  fi
done

echo "✓ Story workspace initialized: $WORKSPACE"
