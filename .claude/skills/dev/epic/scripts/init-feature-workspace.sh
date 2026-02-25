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
if [[ ! -f "$WORKSPACE/plan.json" ]]; then
  cp "$TEMPLATES_DIR/plan.template.json" "$WORKSPACE/plan.json"
fi

echo "✓ Feature workspace initialized: $WORKSPACE"
