#!/usr/bin/env bash
set -euo pipefail

# 引数チェック
if [ $# -lt 1 ]; then
  echo "Usage: $0 <slug>" >&2
  echo "Example: $0 login-feature" >&2
  exit 1
fi

SLUG="$1"
DATE=$(date +%y%m%d)
WORKSPACE="docs/FEATURES/team/${DATE}_${SLUG}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES_DIR="$SKILL_DIR/references/templates"

# 既存チェック（同名ディレクトリがあれば警告）
if [ -d "$WORKSPACE" ]; then
  echo "WARNING: $WORKSPACE already exists. Files will be overwritten." >&2
fi

# ディレクトリ作成
mkdir -p "$WORKSPACE"

# テンプレート雛形を配置
cp "$TEMPLATES_DIR/story-analysis.template.json" "$WORKSPACE/story-analysis.json"
cp "$TEMPLATES_DIR/task-list.template.json"      "$WORKSPACE/task-list.json"

echo "$WORKSPACE"
