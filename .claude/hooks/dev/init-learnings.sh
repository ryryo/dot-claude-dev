#!/bin/bash
# LEARNINGS.md をストーリーディレクトリに作成する
# 使い方: init-learnings.sh <story-dir>
# 既存の場合はスキップ

STORY_DIR="$1"

if [ -z "$STORY_DIR" ]; then
  echo "Usage: init-learnings.sh <story-dir>" >&2
  exit 1
fi

if [ ! -d "$STORY_DIR" ]; then
  echo "ディレクトリが存在しません: $STORY_DIR" >&2
  exit 1
fi

LEARNINGS="$STORY_DIR/LEARNINGS.md"

if [ -f "$LEARNINGS" ]; then
  echo "既存: $LEARNINGS（スキップ）"
  exit 0
fi

cat > "$LEARNINGS" << 'EOF'
# 実装メモ（LEARNINGS.md）

> 自動生成: dev:developing 実行中に記録

---
EOF

echo "作成: $LEARNINGS"
