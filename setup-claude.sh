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
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  IMPORTANT: Add the following to your .gitignore"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "# Claude Code - shared configuration (symlinks only)"
echo ".claude/rules/languages"
echo ".claude/rules/workflow"
echo ".claude/skills/dev"
echo ".claude/skills/meta-skill-creator"
echo ".claude/skills/agent-browser"
echo ".claude/commands/dev"
echo ""
echo "# Claude Code - local settings only"
echo ".claude/settings.local.json"
echo ".claude/hooks/"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "❌ DO NOT add '.claude/' (this would ignore project-specific configs)"
echo "✅ Only ignore the symlinks and local settings listed above"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
