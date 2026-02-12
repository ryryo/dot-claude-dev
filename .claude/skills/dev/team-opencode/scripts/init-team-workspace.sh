#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="docs/features/team-opencode"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES_DIR="$SKILL_DIR/references/templates"

# クリーンアップ
rm -rf "$WORKSPACE"
mkdir -p "$WORKSPACE/prompts"

# テンプレート雛形を配置
cp "$TEMPLATES_DIR/story-analysis.template.json" "$WORKSPACE/story-analysis.json"
cp "$TEMPLATES_DIR/task-list.template.json"      "$WORKSPACE/task-list.json"

echo "✓ Team workspace initialized: $WORKSPACE"
