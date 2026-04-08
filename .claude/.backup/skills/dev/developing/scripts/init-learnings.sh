#!/bin/bash
# LEARNINGS.md をストーリーディレクトリに作成する
# 使い方: init-learnings.sh <story-dir> [story-slug]
# 既存の場合はスキップ

STORY_DIR="$1"
STORY_SLUG="${2:-$(basename "$STORY_DIR")}"

if [ -z "$STORY_DIR" ]; then
  echo "Usage: init-learnings.sh <story-dir> [story-slug]" >&2
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

DATE=$(date +%Y-%m-%d)

cat > "$LEARNINGS" << EOF
# 実装メモ — ${STORY_SLUG}

> 作成日: ${DATE}
> dev:developing 実行中に自動記録

---

## 🔍 発見・技術的な学び

<!-- 想定外の挙動、フレームワーク・ライブラリの罠 -->

---

## 🔄 計画からの変更・妥協

<!-- 当初計画からの逸脱とその理由 -->

---

## 💡 再利用できるパターン

<!-- 次回以降に使えるノウハウ・実装パターン -->

---

## ⚠️ 注意・落とし穴

<!-- 将来ハマりそうな点 -->

---

## 🔧 環境・セットアップメモ

<!-- 環境固有の設定、ワークアラウンド -->

---

## 📋 ルール・ドキュメント更新の提案

<!-- 実装中に気づいた .claude/rules/ や CLAUDE.md への追加・変更提案 -->
<!-- dev:feedback の IMPROVEMENTS.md 生成時にここを参照する -->
<!-- 例:
### .claude/rules/ への追加
- \`frameworks/xxx.md\`: ○○の落とし穴ルール（「発見」セクションの△△を元に）

### CLAUDE.md への反映
- 環境変数テーブルに □□ を追加
-->
EOF

echo "作成: $LEARNINGS"
