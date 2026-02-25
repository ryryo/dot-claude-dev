#!/usr/bin/env bash
set -euo pipefail

# Usage: init-ideation-workspace.sh <slug>
#   Creates docs/ideation/{YYMMDD}-{slug}/ with template files.
#   Outputs the created workspace path to stdout (last line).

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <slug>" >&2
  exit 1
fi

SLUG="$1"
DATE=$(date +%y%m%d)
WORKSPACE="docs/ideation/${DATE}-${SLUG}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES_DIR="$SKILL_DIR/references/templates"

# ディレクトリ作成
mkdir -p "$WORKSPACE"

# テンプレート雛形を配置（既存ファイルがなければ）
for tmpl in PROBLEM_DEFINITION COMPETITOR_ANALYSIS PRODUCT_SPEC; do
  dest="$WORKSPACE/${tmpl}.md"
  if [[ ! -f "$dest" ]]; then
    cp "$TEMPLATES_DIR/${tmpl}.template.md" "$dest"
  fi
done

echo "✓ Ideation workspace initialized: $WORKSPACE"
