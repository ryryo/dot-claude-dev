#!/usr/bin/env bash
set -euo pipefail

# Usage: init-feature-workspace.sh <feature-slug>
#   Creates docs/FEATURES/{feature-slug}/ with template files.
#   Outputs the created workspace path to stdout (last line).

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <feature-slug>" >&2
  exit 1
fi

FEATURE_SLUG="$1"
WORKSPACE="docs/FEATURES/${FEATURE_SLUG}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES_DIR="$SKILL_DIR/references/templates"

# ディレクトリ作成
mkdir -p "$WORKSPACE"

# テンプレート雛形を配置（既存ファイルがなければ）
for tmpl in plan.template.json PLAN.template.md; do
  # plan.template.json → plan.json, PLAN.template.md → PLAN.md
  dest="$WORKSPACE/${tmpl//.template/}"
  if [[ ! -f "$dest" ]]; then
    cp "$TEMPLATES_DIR/$tmpl" "$dest"
  fi
done

echo "✓ Feature workspace initialized: $WORKSPACE"
