#!/usr/bin/env bash
set -euo pipefail

# Usage: init-feedback-workspace.sh <feature-slug>
#   Ensures docs/FEATURES/{feature-slug}/ has DESIGN.md and IMPROVEMENTS.md templates.
#   Only creates files that don't already exist (preserves existing content).
#   Outputs the workspace path to stdout (last line).

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <feature-slug>" >&2
  exit 1
fi

FEATURE_SLUG="$1"
WORKSPACE="docs/FEATURES/${FEATURE_SLUG}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES_DIR="$SKILL_DIR/references/templates"

# ディレクトリ作成（既存なら何もしない）
mkdir -p "$WORKSPACE"

# テンプレート雛形を配置（既存ファイルがなければ）
for tmpl in DESIGN IMPROVEMENTS; do
  dest="$WORKSPACE/${tmpl}.md"
  if [[ ! -f "$dest" ]]; then
    cp "$TEMPLATES_DIR/${tmpl}.template.md" "$dest"
  fi
done

echo "✓ Feedback workspace initialized: $WORKSPACE"
