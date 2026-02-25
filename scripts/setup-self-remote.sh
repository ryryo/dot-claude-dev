#!/bin/bash
# scripts/setup-self-remote.sh
# dot-claude-dev プロジェクト自身のリモート環境セットアップ
#
# setup-claude-remote.sh との違い:
#   - dot-claude-dev のクローン・シンボリックリンク作成をスキップ
#     （このプロジェクト自体が dot-claude-dev なので不要）
#   - opencode CLI セットアップは setup-opencode.sh に委譲

# ローカル環境ではスキップ
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  exit 0
fi

echo "[setup-self-remote] This is dot-claude-dev itself, skipping shared config clone."
echo "[setup-self-remote] ✓ Setup completed"

exit 0
