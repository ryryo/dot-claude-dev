#!/bin/bash
# scripts/setup-opencode.sh
# opencode CLI のインストールと OAuth 認証セットアップ
#
# Cloud Code Web 環境でのみ実行される。
# OPENCODE_AUTH_JSON 環境変数が設定されていれば OAuth 認証を復元し、
# 未設定でも無料モデル用に opencode 本体をインストールする。

# ローカル環境ではスキップ
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  exit 0
fi

log() { echo "[setup-opencode] $*"; }

# ============================================================
# 1. opencode CLI インストール
# ============================================================
install_opencode() {
  if command -v opencode &>/dev/null; then
    log "✓ opencode already installed: $(opencode -v 2>/dev/null)"
    return 0
  fi

  log "Installing opencode..."
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
    log "opencode symlinked to ~/.local/bin/opencode"
  fi

  if command -v opencode &>/dev/null; then
    log "✓ opencode installed: $(opencode -v 2>/dev/null)"
    return 0
  else
    log "WARNING: opencode installation failed"
    return 1
  fi
}

# ============================================================
# 2. OAuth 認証復元（OPENCODE_AUTH_JSON 設定時のみ）
# ============================================================
restore_auth() {
  if [ -z "$OPENCODE_AUTH_JSON" ]; then
    return 0
  fi

  OPENCODE_DATA_DIR="$HOME/.local/share/opencode"
  mkdir -p "$OPENCODE_DATA_DIR"

  echo "$OPENCODE_AUTH_JSON" | base64 -d > "$OPENCODE_DATA_DIR/auth.json" 2>/dev/null

  if [ $? -eq 0 ] && [ -s "$OPENCODE_DATA_DIR/auth.json" ]; then
    chmod 600 "$OPENCODE_DATA_DIR/auth.json"
    log "✓ auth.json restored"
  else
    log "WARNING: Failed to decode OPENCODE_AUTH_JSON"
    rm -f "$OPENCODE_DATA_DIR/auth.json"
    return 1
  fi
}

# ============================================================
# メイン処理
# ============================================================
if [ -n "$OPENCODE_AUTH_JSON" ]; then
  log "OPENCODE_AUTH_JSON is set (OAuth credentials available)"
else
  log "OPENCODE_AUTH_JSON not set (free models only)"
fi

install_opencode
restore_auth

log "✓ Setup completed"
