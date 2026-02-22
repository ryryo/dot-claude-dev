#!/bin/bash
# Claude共通設定をシンボリックリンク

set -e

SHARED_DIR="${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}"

if [ ! -d "$SHARED_DIR" ]; then
  echo "Error: Shared directory not found: $SHARED_DIR"
  echo "Please clone/create the shared directory first:"
  echo "  git clone <your-repo> $SHARED_DIR"
  exit 1
fi

# デフォルトパスと異なる場合、CLAUDE_SHARED_DIR を shell config に自動永続化
DEFAULT_DIR="$HOME/dot-claude-dev"
if [ "$SHARED_DIR" != "$DEFAULT_DIR" ]; then
  if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
  elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
  else
    SHELL_RC="$HOME/.profile"
  fi

  if ! grep -q "CLAUDE_SHARED_DIR" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# Claude Code - shared configuration directory" >> "$SHELL_RC"
    echo "export CLAUDE_SHARED_DIR=\"$SHARED_DIR\"" >> "$SHELL_RC"
    echo "✓ Persisted CLAUDE_SHARED_DIR to $SHELL_RC (run: source $SHELL_RC)"
  else
    echo "✓ CLAUDE_SHARED_DIR already set in $SHELL_RC"
  fi
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

# 共通フックをリンク
if [ -d "$SHARED_DIR/.claude/hooks/dev" ]; then
  mkdir -p .claude/hooks
  ln -sf "$SHARED_DIR/.claude/hooks/dev" .claude/hooks/dev
  echo "✓ Linked hooks/dev"
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
echo ".claude/hooks/dev"
echo ""
echo "# Claude Code - local settings only"
echo ".claude/settings.local.json"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "❌ DO NOT add '.claude/' (this would ignore project-specific configs)"
echo "✅ Only ignore the symlinks and local settings listed above"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
