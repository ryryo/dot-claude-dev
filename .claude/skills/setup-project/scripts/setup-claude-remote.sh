#!/bin/bash
# setup-claude-remote.sh
# リモート環境（ウェブ上のClaude Code）で ~/.dot-claude-dev を再現する
# テンプレート: setup-project スキルで各プロジェクトの scripts/ にコピーされる
#
# 使い方:
#   1. setup-project スキルで自動コピー、または手動で各プロジェクトの scripts/ にコピー
#   2. SHARED_REPO を自分のdot-claude-devリポジトリURLに変更
#   3. .claude/settings.json の SessionStart フックに登録

# ローカル環境ではスキップ
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  exit 0
fi

# セッション起動を妨げない
set +e
trap 'echo "[setup-claude-remote] WARNING: error occurred, continuing"; exit 0' ERR

SHARED_REPO="https://github.com/ryryo/dot-claude-dev.git"
SHARED_DIR="$HOME/.dot-claude-dev"

# --- dot-claude-dev セットアップ ---

# クローン or アップデート（cd せず git -C を使い CWD を変えない）
if [ -d "$SHARED_DIR" ]; then
  echo "[setup-claude-remote] ~/.dot-claude-dev already exists, updating..."
  git -C "$SHARED_DIR" pull origin master 2>&1 | grep -v "Already up to date" || echo "[setup-claude-remote] Updated to latest"
else
  echo "[setup-claude-remote] Cloning shared config..."
  git clone --depth 1 "$SHARED_REPO" "$SHARED_DIR"

  if [ $? -ne 0 ]; then
    echo "[setup-claude-remote] WARNING: Failed to clone shared config. Continuing without shared settings."
  fi
fi

# setup-claude.sh を実行（初回 or アップデート後）
if [ -f "$SHARED_DIR/scripts/setup-claude.sh" ]; then
  echo "[setup-claude-remote] Running setup-claude.sh..."
  CLAUDE_SHARED_DIR="$SHARED_DIR" bash "$SHARED_DIR/scripts/setup-claude.sh"
else
  echo "[setup-claude-remote] WARNING: setup-claude.sh not found in shared repo."
fi

echo "[setup-claude-remote] ✓ Setup completed"

exit 0
