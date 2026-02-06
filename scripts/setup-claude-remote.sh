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

# 既にクローン済みならスキップ
if [ -d "$SHARED_DIR" ]; then
  echo "[setup-claude-remote] ~/.dot-claude-dev already exists, skipping clone."
else
  echo "[setup-claude-remote] Cloning shared config..."
  git clone --depth 1 "$SHARED_REPO" "$SHARED_DIR"

  if [ $? -ne 0 ]; then
    echo "[setup-claude-remote] WARNING: Failed to clone shared config. Continuing without shared settings."
  fi

  if [ -f "$SHARED_DIR/setup-claude.sh" ]; then
    echo "[setup-claude-remote] Running setup-claude.sh..."
    CLAUDE_SHARED_DIR="$SHARED_DIR" bash "$SHARED_DIR/setup-claude.sh"
  else
    echo "[setup-claude-remote] WARNING: setup-claude.sh not found in shared repo."
  fi
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

    # ~/.profile と ~/.bashrc にPATHを永続化（重複チェック付き）
    OPENCODE_PATH_LINE='export PATH="$HOME/.local/share/opencode/bin:$HOME/.opencode/bin:$PATH"'

    # ~/.profile に追加（ログインシェル用）
    if ! grep -q "\.opencode/bin" "$HOME/.profile" 2>/dev/null; then
      echo "" >> "$HOME/.profile"
      echo "# opencode CLI path (added by setup-claude-remote.sh)" >> "$HOME/.profile"
      echo "$OPENCODE_PATH_LINE" >> "$HOME/.profile"
      echo "[setup-claude-remote] opencode PATH added to ~/.profile"
    fi

    # ~/.bashrc に追加（非ログインシェル・新規Bash起動時用）
    if ! grep -q "\.opencode/bin" "$HOME/.bashrc" 2>/dev/null; then
      echo "" >> "$HOME/.bashrc"
      echo "# opencode CLI path (added by setup-claude-remote.sh)" >> "$HOME/.bashrc"
      echo "$OPENCODE_PATH_LINE" >> "$HOME/.bashrc"
      echo "[setup-claude-remote] opencode PATH added to ~/.bashrc"
    fi

    if ! command -v opencode &>/dev/null; then
      echo "[setup-claude-remote] WARNING: opencode installation failed."
    else
      echo "[setup-claude-remote] opencode installed: $(opencode -v 2>/dev/null)"
    fi
  else
    echo "[setup-claude-remote] opencode already installed: $(opencode -v 2>/dev/null)"
  fi

  # シンボリックリンクを作成（$HOME/.local/bin は常にPATHに含まれる）
  # これにより、PATH設定に依存せず確実に opencode コマンドが使える
  if [ -f "$HOME/.opencode/bin/opencode" ]; then
    mkdir -p "$HOME/.local/bin"
    ln -sf "$HOME/.opencode/bin/opencode" "$HOME/.local/bin/opencode"
    echo "[setup-claude-remote] Created symlink: ~/.local/bin/opencode -> ~/.opencode/bin/opencode"
  elif [ -f "$HOME/.local/share/opencode/bin/opencode" ]; then
    mkdir -p "$HOME/.local/bin"
    ln -sf "$HOME/.local/share/opencode/bin/opencode" "$HOME/.local/bin/opencode"
    echo "[setup-claude-remote] Created symlink: ~/.local/bin/opencode -> ~/.local/share/opencode/bin/opencode"
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

    # ~/.profile と ~/.bashrc にPATHを永続化（重複チェック付き）
    OPENCODE_PATH_LINE='export PATH="$HOME/.local/share/opencode/bin:$HOME/.opencode/bin:$PATH"'

    # ~/.profile に追加（ログインシェル用）
    if ! grep -q "\.opencode/bin" "$HOME/.profile" 2>/dev/null; then
      echo "" >> "$HOME/.profile"
      echo "# opencode CLI path (added by setup-claude-remote.sh)" >> "$HOME/.profile"
      echo "$OPENCODE_PATH_LINE" >> "$HOME/.profile"
      echo "[setup-claude-remote] opencode PATH added to ~/.profile"
    fi

    # ~/.bashrc に追加（非ログインシェル・新規Bash起動時用）
    if ! grep -q "\.opencode/bin" "$HOME/.bashrc" 2>/dev/null; then
      echo "" >> "$HOME/.bashrc"
      echo "# opencode CLI path (added by setup-claude-remote.sh)" >> "$HOME/.bashrc"
      echo "$OPENCODE_PATH_LINE" >> "$HOME/.bashrc"
      echo "[setup-claude-remote] opencode PATH added to ~/.bashrc"
    fi

    if command -v opencode &>/dev/null; then
      echo "[setup-claude-remote] opencode installed: $(opencode -v 2>/dev/null)"
    else
      echo "[setup-claude-remote] WARNING: opencode installation may have failed."
    fi

    # シンボリックリンクを作成（$HOME/.local/bin は常にPATHに含まれる）
    # これにより、PATH設定に依存せず確実に opencode コマンドが使える
    if [ -f "$HOME/.opencode/bin/opencode" ]; then
      mkdir -p "$HOME/.local/bin"
      ln -sf "$HOME/.opencode/bin/opencode" "$HOME/.local/bin/opencode"
      echo "[setup-claude-remote] Created symlink: ~/.local/bin/opencode -> ~/.opencode/bin/opencode"
    elif [ -f "$HOME/.local/share/opencode/bin/opencode" ]; then
      mkdir -p "$HOME/.local/bin"
      ln -sf "$HOME/.local/share/opencode/bin/opencode" "$HOME/.local/bin/opencode"
      echo "[setup-claude-remote] Created symlink: ~/.local/bin/opencode -> ~/.local/share/opencode/bin/opencode"
    fi
  fi
fi

# セットアップ完了メッセージ
echo ""
echo "[setup-claude-remote] ✓ Setup completed"
if command -v opencode &>/dev/null; then
  echo "[setup-claude-remote] ✓ opencode is ready to use"
  echo "[setup-claude-remote] ✓ Command available: opencode"
else
  echo "[setup-claude-remote] ⚠ opencode not found in current PATH"
  echo "[setup-claude-remote] Note: Symlink created at ~/.local/bin/opencode"
  echo "[setup-claude-remote] Note: PATH settings added to ~/.profile and ~/.bashrc"
  echo "[setup-claude-remote] Tip: Next Bash command will have opencode available"
fi

exit 0
