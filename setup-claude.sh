#!/bin/bash
# Claude共通設定をシンボリックリンク

set -e

SHARED_DIR="${CLAUDE_SHARED_DIR:-$HOME/.claude-shared}"

if [ ! -d "$SHARED_DIR" ]; then
  echo "Error: Shared directory not found: $SHARED_DIR"
  echo "Please clone/create the shared directory first:"
  echo "  git clone <your-repo> $SHARED_DIR"
  exit 1
fi

# .claude ディレクトリを作成
mkdir -p .claude/rules
mkdir -p .claude/skills
mkdir -p .claude/commands

# 共通ルールをリンク
if [ -d "$SHARED_DIR/.claude/rules/languages" ]; then
  ln -sf "$SHARED_DIR/.claude/rules/languages" .claude/rules/languages
  echo "✓ Linked rules/languages"
fi

if [ -d "$SHARED_DIR/.claude/rules/workflow" ]; then
  ln -sf "$SHARED_DIR/.claude/rules/workflow" .claude/rules/workflow
  echo "✓ Linked rules/workflow"
fi

# 共通スキルをリンク
if [ -d "$SHARED_DIR/.claude/skills/dev" ]; then
  ln -sf "$SHARED_DIR/.claude/skills/dev" .claude/skills/dev
  echo "✓ Linked skills/dev"
fi

if [ -d "$SHARED_DIR/.claude/skills/meta-skill-creator" ]; then
  ln -sf "$SHARED_DIR/.claude/skills/meta-skill-creator" .claude/skills/meta-skill-creator
  echo "✓ Linked skills/meta-skill-creator"
fi

if [ -d "$SHARED_DIR/.claude/skills/agent-browser" ]; then
  ln -sf "$SHARED_DIR/.claude/skills/agent-browser" .claude/skills/agent-browser
  echo "✓ Linked skills/agent-browser"
fi

# 共通コマンドをリンク
if [ -d "$SHARED_DIR/.claude/commands/dev" ]; then
  ln -sf "$SHARED_DIR/.claude/commands/dev" .claude/commands/dev
  echo "✓ Linked commands/dev"
fi

echo ""
echo "✓ Claude configuration linked successfully"
echo ""
echo "Shared directory: $SHARED_DIR"
echo "Project directory: $(pwd)/.claude"
