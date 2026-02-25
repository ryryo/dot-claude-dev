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
#
# opencode連携は scripts/setup-opencode.sh に分離済み

# ローカル環境ではスキップ
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  exit 0
fi

SHARED_REPO="https://github.com/ryryo/dot-claude-dev.git"
SHARED_DIR="$HOME/.dot-claude-dev"

# === DOT-CLAUDE-DEV MANAGED BEGIN ===
# このセクションは sync-setup-remote スキルで自動更新されます
# 手動で編集した場合、次回の同期で上書きされます

# --- dot-claude-dev セットアップ ---

# クローン or アップデート
if [ -d "$SHARED_DIR" ]; then
  echo "[setup-claude-remote] ~/.dot-claude-dev already exists, updating..."
  cd "$SHARED_DIR" && git pull origin master 2>&1 | grep -v "Already up to date" || echo "[setup-claude-remote] Updated to latest"
  cd - > /dev/null
else
  echo "[setup-claude-remote] Cloning shared config..."
  git clone --depth 1 "$SHARED_REPO" "$SHARED_DIR"

  if [ $? -ne 0 ]; then
    echo "[setup-claude-remote] WARNING: Failed to clone shared config. Continuing without shared settings."
  fi
fi

# setup-claude.sh を実行（初回 or アップデート後）
if [ -f "$SHARED_DIR/setup-claude.sh" ]; then
  echo "[setup-claude-remote] Running setup-claude.sh..."
  CLAUDE_SHARED_DIR="$SHARED_DIR" bash "$SHARED_DIR/setup-claude.sh"
else
  echo "[setup-claude-remote] WARNING: setup-claude.sh not found in shared repo."
fi

# セットアップ完了メッセージ
echo ""
echo "[setup-claude-remote] ✓ Setup completed"

# === DOT-CLAUDE-DEV MANAGED END ===

# --- プロジェクト固有セットアップ ---
# プロジェクト固有の処理をここに追加してください
# 例: npm install, docker setup, 環境変数の設定など

exit 0
