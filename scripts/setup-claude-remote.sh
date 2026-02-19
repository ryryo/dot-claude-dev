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
# opencode連携（オプション）:
#   OPENCODE_AUTH_JSON 環境変数にbase64エンコードしたauth.jsonを設定すると、
#   opencode CLIをインストールし、OpenAI Plus/ProのOAuth認証を引き継ぐ。
#
#   ローカルで準備:
#     cat ~/.local/share/opencode/auth.json | base64 | pbcopy
#   → Claude Code Webのシークレットに OPENCODE_AUTH_JSON として設定

# ローカル環境ではスキップ
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  exit 0
fi

SHARED_REPO="https://github.com/ryryo/dot-claude-dev.git"
SHARED_DIR="$HOME/.dot-claude-dev"

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

# --- opencode CLI セットアップ ---

# OPENCODE_AUTH_JSON 環境変数の存在確認
if [ -n "$OPENCODE_AUTH_JSON" ]; then
  echo "[setup-claude-remote] ✓ OPENCODE_AUTH_JSON is set (OAuth credentials available)"
else
  echo "[setup-claude-remote] ✗ OPENCODE_AUTH_JSON is not set (free models only)"
fi

if [ -n "$OPENCODE_AUTH_JSON" ]; then
  echo "[setup-claude-remote] Setting up opencode CLI..."

  # opencode インストール（未インストールの場合）
  if ! command -v opencode &>/dev/null; then
    echo "[setup-claude-remote] Installing opencode..."
    curl -fsSL https://opencode.ai/install | bash 2>/dev/null

    # PATHに追加（現在のセッション）
    export PATH="$HOME/.local/share/opencode/bin:$HOME/.opencode/bin:$HOME/bin:$PATH"

    # シンボリックリンクを既存PATH内に作成
    # Claude Code の Bash ツールは ~/.profile や ~/.bashrc を読まないため、
    # プロファイル設定ではPATHが反映されない。
    # 代わりに、デフォルトPATHに含まれる ~/.local/bin/ にリンクを置く。
    OPENCODE_BIN=$(command -v opencode 2>/dev/null)
    if [ -n "$OPENCODE_BIN" ] && [ -d "$HOME/.local/bin" ]; then
      ln -sf "$OPENCODE_BIN" "$HOME/.local/bin/opencode"
      echo "[setup-claude-remote] opencode symlinked to ~/.local/bin/opencode"
    fi

    if ! command -v opencode &>/dev/null; then
      echo "[setup-claude-remote] WARNING: opencode installation failed."
    else
      echo "[setup-claude-remote] opencode installed: $(opencode -v 2>/dev/null)"
    fi
  else
    echo "[setup-claude-remote] opencode already installed: $(opencode -v 2>/dev/null)"
  fi

  # auth.json を復元（OAuth refresh token を引き継ぐ）
  OPENCODE_DATA_DIR="$HOME/.local/share/opencode"
  mkdir -p "$OPENCODE_DATA_DIR"

  echo "$OPENCODE_AUTH_JSON" | base64 -d > "$OPENCODE_DATA_DIR/auth.json" 2>/dev/null

  if [ $? -eq 0 ] && [ -s "$OPENCODE_DATA_DIR/auth.json" ]; then
    chmod 600 "$OPENCODE_DATA_DIR/auth.json"
    echo "[setup-claude-remote] opencode auth.json restored."
  else
    echo "[setup-claude-remote] WARNING: Failed to decode OPENCODE_AUTH_JSON."
    rm -f "$OPENCODE_DATA_DIR/auth.json"
  fi
else
  echo "[setup-claude-remote] OPENCODE_AUTH_JSON not set, skipping OAuth setup."
  echo "[setup-claude-remote] Free models (opencode/*) are available without auth."

  # 無料モデル用にopencode本体だけインストール
  if ! command -v opencode &>/dev/null; then
    echo "[setup-claude-remote] Installing opencode (free models only)..."
    curl -fsSL https://opencode.ai/install | bash 2>/dev/null

    # PATHに追加（現在のセッション）
    export PATH="$HOME/.local/share/opencode/bin:$HOME/.opencode/bin:$HOME/bin:$PATH"

    # シンボリックリンクを既存PATH内に作成
    OPENCODE_BIN=$(command -v opencode 2>/dev/null)
    if [ -n "$OPENCODE_BIN" ] && [ -d "$HOME/.local/bin" ]; then
      ln -sf "$OPENCODE_BIN" "$HOME/.local/bin/opencode"
      echo "[setup-claude-remote] opencode symlinked to ~/.local/bin/opencode"
    fi

    if command -v opencode &>/dev/null; then
      echo "[setup-claude-remote] opencode installed: $(opencode -v 2>/dev/null)"
    else
      echo "[setup-claude-remote] WARNING: opencode installation may have failed."
    fi
  fi
fi

# --- agent-browser + Xvfb セットアップ ---

# agent-browser CLI インストール
if ! command -v agent-browser &>/dev/null; then
  echo "[setup-claude-remote] Installing agent-browser..."
  npm install -g agent-browser 2>&1 | tail -1
  if command -v agent-browser &>/dev/null; then
    echo "[setup-claude-remote] ✓ agent-browser installed"
  else
    echo "[setup-claude-remote] WARNING: agent-browser installation failed"
  fi
else
  echo "[setup-claude-remote] ✓ agent-browser already installed"
fi

# Xvfb 仮想ディスプレイ起動
if command -v Xvfb &>/dev/null; then
  if ! pgrep -x Xvfb > /dev/null 2>&1; then
    Xvfb :99 -screen 0 1280x720x24 &>/dev/null &
    echo "[setup-claude-remote] ✓ Xvfb started on :99"
  else
    echo "[setup-claude-remote] ✓ Xvfb already running"
  fi
  # DISPLAY を .bashrc に永続化
  grep -q 'export DISPLAY=:99' ~/.bashrc 2>/dev/null || echo 'export DISPLAY=:99' >> ~/.bashrc
else
  echo "[setup-claude-remote] WARNING: Xvfb not available (apt install xvfb)"
fi

# Playwright Chromium バイナリ互換性
# agent-browser が要求するリビジョンが存在しない場合、既存バイナリからシンボリックリンクを作成
if command -v agent-browser &>/dev/null; then
  node -e "
    const fs = require('fs'), path = require('path'), os = require('os');
    const abRoot = path.join('$(npm root -g)', 'agent-browser');
    const browsersJson = require(path.join(abRoot, 'node_modules/playwright-core/browsers.json'));
    const cacheDir = path.join(os.homedir(), '.cache/ms-playwright');
    if (!fs.existsSync(cacheDir)) process.exit(0);
    const dirs = fs.readdirSync(cacheDir);
    for (const b of browsersJson.browsers) {
      if (!['chromium','chromium-headless-shell'].includes(b.name)) continue;
      const prefix = b.name === 'chromium' ? 'chromium-' : 'chromium_headless_shell-';
      const req = prefix + b.revision;
      if (dirs.includes(req)) continue;
      const existing = dirs.find(d => d.startsWith(prefix) && d !== req && !d.startsWith('.'));
      if (existing) console.log([req, existing, b.name].join('|'));
    }
  " 2>/dev/null | while IFS='|' read -r REQUIRED EXISTING BNAME; do
    CACHE="$HOME/.cache/ms-playwright"
    if [ "$BNAME" = "chromium-headless-shell" ] && [ -d "$CACHE/$EXISTING/chrome-linux" ] && [ ! -d "$CACHE/$EXISTING/chrome-headless-shell-linux64" ]; then
      # ディレクトリ構造が変わった場合のマッピング（chrome-linux/ → chrome-headless-shell-linux64/）
      mkdir -p "$CACHE/$REQUIRED/chrome-headless-shell-linux64"
      ln -sf "$CACHE/$EXISTING/chrome-linux/headless_shell" "$CACHE/$REQUIRED/chrome-headless-shell-linux64/chrome-headless-shell"
      for f in "$CACHE/$EXISTING/chrome-linux/"*; do
        [ "$(basename "$f")" = "headless_shell" ] && continue
        ln -sf "$f" "$CACHE/$REQUIRED/chrome-headless-shell-linux64/$(basename "$f")" 2>/dev/null
      done
      echo "[setup-claude-remote] ✓ Chromium headless shell: $EXISTING → $REQUIRED (mapped)"
    else
      ln -sfn "$CACHE/$EXISTING" "$CACHE/$REQUIRED"
      echo "[setup-claude-remote] ✓ Chromium: $EXISTING → $REQUIRED (linked)"
    fi
  done
fi

# セットアップ完了メッセージ
echo ""
echo "[setup-claude-remote] ✓ Setup completed"
if command -v opencode &>/dev/null; then
  echo "[setup-claude-remote] opencode is ready to use"
fi
if command -v agent-browser &>/dev/null; then
  echo "[setup-claude-remote] agent-browser is ready to use (DISPLAY=:99)"
fi

exit 0
