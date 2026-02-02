#!/bin/bash
# scripts/setup-claude-remote.sh
# リモート環境（ウェブ上のClaude Code）で ~/.dot-claude-dev を再現する
#
# 使い方:
#   1. このファイルを各プロジェクトの scripts/ にコピー
#   2. SHARED_REPO を自分のdot-claude-devリポジトリURLに変更
#   3. .claude/settings.json の SessionStart フックに登録:
#      {
#        "hooks": {
#          "SessionStart": [{
#            "matcher": "startup",
#            "hooks": [{
#              "type": "command",
#              "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-claude-remote.sh"
#            }]
#          }]
#        }
#      }

# ローカル環境ではスキップ
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  exit 0
fi

SHARED_REPO="https://github.com/ryryo/dot-claude-dev.git"
SHARED_DIR="$HOME/.dot-claude-dev"

# 既にクローン済みならスキップ
if [ -d "$SHARED_DIR" ]; then
  echo "[setup-claude-remote] ~/.dot-claude-dev already exists, skipping clone."
  exit 0
fi

# 共有リポジトリをクローン
echo "[setup-claude-remote] Cloning shared config..."
git clone --depth 1 "$SHARED_REPO" "$SHARED_DIR"

if [ $? -ne 0 ]; then
  echo "[setup-claude-remote] WARNING: Failed to clone shared config. Continuing without shared settings."
  exit 0
fi

# setup-claude.sh を実行してシンボリックリンクを張る
if [ -f "$SHARED_DIR/setup-claude.sh" ]; then
  echo "[setup-claude-remote] Running setup-claude.sh..."
  CLAUDE_SHARED_DIR="$SHARED_DIR" bash "$SHARED_DIR/setup-claude.sh"
else
  echo "[setup-claude-remote] WARNING: setup-claude.sh not found in shared repo."
fi

exit 0
