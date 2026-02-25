#!/bin/bash
# agent本文 + 追加コンテキスト + LEARNINGS_FOOTER を一括構築する
# 使い方: build-prompt.sh <agent-name> <learnings-path> [extra-context...]
#
# 例:
#   bash scripts/build-prompt.sh tdd-cycle /path/to/LEARNINGS.md "タスク: validateEmail"
#   bash scripts/build-prompt.sh spot-review /path/to/LEARNINGS.md

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

AGENT_NAME="$1"
LEARNINGS_PATH="$2"
shift 2

# 1. agent本文
cat "$SKILL_DIR/agents/$AGENT_NAME.md"

# 2. 追加コンテキスト（引数で渡された分だけ付与）
for ctx in "$@"; do
  echo ""
  echo "---"
  echo "$ctx"
done

# 3. LEARNINGS_FOOTER（LEARNINGS_PATH を置換して付与）
echo ""
sed "s|{LEARNINGS_PATH}|$LEARNINGS_PATH|g" "$SKILL_DIR/references/learnings-footer.md"
