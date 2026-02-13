#!/bin/bash
# scripts/setup-self-remote.sh
# dot-claude-dev プロジェクト自身のリモート環境セットアップ
#
# setup-claude-remote.sh との違い:
#   - dot-claude-dev のクローン・シンボリックリンク作成をスキップ
#     （このプロジェクト自体が dot-claude-dev なので不要）
#   - opencode CLI セットアップのみ実行

# ローカル環境ではスキップ
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  exit 0
fi

echo "[setup-self-remote] This is dot-claude-dev itself, skipping shared config clone."

# --- opencode CLI セットアップ ---

# OPENCODE_AUTH_JSON 環境変数の存在確認
if [ -n "$OPENCODE_AUTH_JSON" ]; then
  echo "[setup-self-remote] ✓ OPENCODE_AUTH_JSON is set (provider credentials available)"
else
  echo "[setup-self-remote] ✗ OPENCODE_AUTH_JSON is not set (free models only)"
fi

if [ -n "$OPENCODE_AUTH_JSON" ]; then
  echo "[setup-self-remote] Setting up opencode CLI..."

  # opencode インストール（未インストールの場合）
  if ! command -v opencode &>/dev/null; then
    echo "[setup-self-remote] Installing opencode..."
    curl -fsSL https://opencode.ai/install | bash 2>/dev/null

    # PATHに追加（現在のセッション）
    export PATH="$HOME/.local/share/opencode/bin:$HOME/.opencode/bin:$HOME/bin:$PATH"

    # シンボリックリンクを既存PATH内に作成
    OPENCODE_BIN=$(command -v opencode 2>/dev/null)
    if [ -n "$OPENCODE_BIN" ] && [ -d "$HOME/.local/bin" ]; then
      ln -sf "$OPENCODE_BIN" "$HOME/.local/bin/opencode"
      echo "[setup-self-remote] opencode symlinked to ~/.local/bin/opencode"
    fi

    if ! command -v opencode &>/dev/null; then
      echo "[setup-self-remote] WARNING: opencode installation failed."
    else
      echo "[setup-self-remote] opencode installed: $(opencode -v 2>/dev/null)"
    fi
  else
    echo "[setup-self-remote] opencode already installed: $(opencode -v 2>/dev/null)"
  fi

  # auth.json を復元（全プロバイダの認証情報を引き継ぐ）
  OPENCODE_DATA_DIR="$HOME/.local/share/opencode"
  mkdir -p "$OPENCODE_DATA_DIR"

  echo "$OPENCODE_AUTH_JSON" | base64 -d > "$OPENCODE_DATA_DIR/auth.json" 2>/dev/null

  if [ $? -eq 0 ] && [ -s "$OPENCODE_DATA_DIR/auth.json" ]; then
    chmod 600 "$OPENCODE_DATA_DIR/auth.json"
    echo "[setup-self-remote] opencode auth.json restored."

    # 利用可能プロバイダ一覧を表示
    if command -v python3 &>/dev/null; then
      echo "[setup-self-remote] Available providers:"
      python3 -c "
import json, sys
try:
    with open('$OPENCODE_DATA_DIR/auth.json') as f:
        data = json.load(f)
    for name, info in data.items():
        auth_type = info.get('type', 'unknown')
        print(f'  - {name} ({auth_type})')
except Exception:
    print('  (failed to parse auth.json)')
" 2>/dev/null
    fi
  else
    echo "[setup-self-remote] WARNING: Failed to decode OPENCODE_AUTH_JSON."
    rm -f "$OPENCODE_DATA_DIR/auth.json"
  fi
else
  echo "[setup-self-remote] OPENCODE_AUTH_JSON not set, skipping provider auth setup."

  # 無料モデル用にopencode本体だけインストール
  if ! command -v opencode &>/dev/null; then
    echo "[setup-self-remote] Installing opencode (free models only)..."
    curl -fsSL https://opencode.ai/install | bash 2>/dev/null

    export PATH="$HOME/.local/share/opencode/bin:$HOME/.opencode/bin:$HOME/bin:$PATH"

    OPENCODE_BIN=$(command -v opencode 2>/dev/null)
    if [ -n "$OPENCODE_BIN" ] && [ -d "$HOME/.local/bin" ]; then
      ln -sf "$OPENCODE_BIN" "$HOME/.local/bin/opencode"
      echo "[setup-self-remote] opencode symlinked to ~/.local/bin/opencode"
    fi

    if command -v opencode &>/dev/null; then
      echo "[setup-self-remote] opencode installed: $(opencode -v 2>/dev/null)"
    else
      echo "[setup-self-remote] WARNING: opencode installation may have failed."
    fi
  fi
fi

# セットアップ完了メッセージ
echo ""
echo "[setup-self-remote] ✓ Setup completed"
if command -v opencode &>/dev/null; then
  echo "[setup-self-remote] opencode is ready to use"
  echo "[setup-self-remote] Command available: opencode"
else
  echo "[setup-self-remote] ⚠ opencode not available"
fi

exit 0
