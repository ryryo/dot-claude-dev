#!/bin/bash
# Claude共通設定をシンボリックリンク

set -e

# CLAUDE_SHARED_DIR の解決
# 1. env var 明示があればそれを採用
# 2. 未設定なら 3 候補を探索（先頭優先）
# 3. いずれも見つからなければエラー
if [ -n "$CLAUDE_SHARED_DIR" ]; then
  SHARED_DIR="$CLAUDE_SHARED_DIR"
  SHARED_DIR_SOURCE="env"
else
  SHARED_DIR_SOURCE="discovered"
  for CANDIDATE in "$HOME/dot-claude-dev" "$HOME/dev/dot-claude-dev" "$HOME/.dot-claude-dev"; do
    if [ -d "$CANDIDATE" ]; then
      SHARED_DIR="$CANDIDATE"
      echo "✓ Discovered dot-claude-dev at: $SHARED_DIR"
      break
    fi
  done
fi

if [ -z "$SHARED_DIR" ]; then
  echo "Error: dot-claude-dev not found in any of:"
  echo "  - \$HOME/dot-claude-dev"
  echo "  - \$HOME/dev/dot-claude-dev"
  echo "  - \$HOME/.dot-claude-dev"
  echo ""
  echo "Please clone the repo or set CLAUDE_SHARED_DIR:"
  echo "  git clone <your-repo> \$HOME/dot-claude-dev"
  echo "  # or"
  echo "  export CLAUDE_SHARED_DIR=/path/to/your/dot-claude-dev"
  exit 1
fi

# デフォルトパスと異なる場合 OR 探索で見つけた場合、CLAUDE_SHARED_DIR を shell config に自動永続化
DEFAULT_DIR="$HOME/dot-claude-dev"
should_persist=false
if [ "$SHARED_DIR_SOURCE" = "discovered" ] && [ "$SHARED_DIR" != "$DEFAULT_DIR" ]; then
  should_persist=true
elif [ "$SHARED_DIR_SOURCE" = "env" ] && [ "$SHARED_DIR" != "$DEFAULT_DIR" ]; then
  should_persist=true
fi

if [ "$should_persist" = "true" ]; then
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
# if [ -d "$SHARED_DIR/.claude/rules/languages" ]; then
#   ln -sf "$SHARED_DIR/.claude/rules/languages" .claude/rules/languages
#   echo "✓ Linked rules/languages"
# fi

if [ -d "$SHARED_DIR/.claude/rules/workflow" ]; then
  ln -sfn "$SHARED_DIR/.claude/rules/workflow" .claude/rules/workflow
  echo "✓ Linked rules/workflow"
fi

# 共通スキルをリンク
if [ -d "$SHARED_DIR/.claude/skills/dev" ]; then
  ln -sfn "$SHARED_DIR/.claude/skills/dev" .claude/skills/dev
  echo "✓ Linked skills/dev"
fi

# 共通フックをリンク
if [ -d "$SHARED_DIR/.claude/hooks/dev" ]; then
  mkdir -p .claude/hooks
  ln -sfn "$SHARED_DIR/.claude/hooks/dev" .claude/hooks/dev
  echo "✓ Linked hooks/dev"
fi

# 共通コマンドをリンク
if [ -d "$SHARED_DIR/.claude/commands/dev" ]; then
  ln -sfn "$SHARED_DIR/.claude/commands/dev" .claude/commands/dev
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
# echo ".claude/rules/languages"
echo ".claude/rules/workflow"
echo ".claude/skills/dev"
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
