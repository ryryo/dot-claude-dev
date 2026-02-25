#!/usr/bin/env bash
# setup-agent-browser.sh - agent-browser CLI のセットアップと検証
#
# 使い方:
#   bash setup-agent-browser.sh [--check-url URL]
#
# 終了コード:
#   0: セットアップ成功
#   1: セットアップ失敗（修復不可）
#
# 出力 (最終行):
#   SUCCESS:<prefix>   セットアップ成功。<prefix> はコマンド名
#   FAIL:<reason>      セットアップ失敗。<reason> は原因

set -euo pipefail

CHECK_URL=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check-url) CHECK_URL="$2"; shift 2 ;;
    *) shift ;;
  esac
done

log() { echo "[agent-browser-setup] $*"; }
fail() { echo "FAIL:$1"; exit 1; }

# ============================================================
# 1. CLI 存在確認
# ============================================================
if command -v agent-browser &>/dev/null; then
  PREFIX="agent-browser"
  log "✓ agent-browser found"
else
  log "agent-browser not found, installing..."
  npm install -g agent-browser 2>&1 | tail -1
  if command -v agent-browser &>/dev/null; then
    PREFIX="agent-browser"
    log "✓ agent-browser installed"
  else
    fail "agent-browser のインストールに失敗しました"
  fi
fi

# ============================================================
# 2. ブラウザ起動テスト
# ============================================================
try_browser() {
  $PREFIX open 'data:text/html,<h1>OK</h1>' 2>&1
}

close_browser() {
  $PREFIX close 2>/dev/null || true
}

if try_browser | grep -q "✓"; then
  close_browser
  log "✓ Browser works"
else
  close_browser
  log "Browser test failed, attempting repair..."

  # ============================================================
  # 3. 環境判定 → 修復
  # ============================================================
  if [[ "${CLAUDE_CODE_REMOTE:-false}" == "true" ]]; then
    # ---- Cloud Code Web 環境 ----
    log "Cloud Code Web environment detected"

    # 要求バージョンをエラーメッセージから取得
    ERROR_MSG=$($PREFIX open 'data:text/html,<h1>OK</h1>' 2>&1 || true)
    close_browser
    REQUIRED_VER=$(echo "$ERROR_MSG" | grep -oP 'chromium_headless_shell-\K[0-9]+' | head -1)

    if [[ -z "$REQUIRED_VER" ]]; then
      fail "要求ブラウザバージョンを特定できませんでした: $ERROR_MSG"
    fi
    log "Required version: chromium_headless_shell-$REQUIRED_VER"

    # プリインストール済みバージョンを検索
    PW_CACHE="/root/.cache/ms-playwright"
    EXISTING_VER=$(ls "$PW_CACHE" 2>/dev/null | grep 'chromium_headless_shell-' | grep -oP '\d+' | head -1)

    if [[ -z "$EXISTING_VER" ]]; then
      fail "プリインストール済みブラウザが見つかりません"
    fi
    log "Found pre-installed: chromium_headless_shell-$EXISTING_VER"

    # シンボリックリンクで流用
    REQUIRED_DIR="$PW_CACHE/chromium_headless_shell-${REQUIRED_VER}/chrome-headless-shell-linux64"
    EXISTING_BINARY="$PW_CACHE/chromium_headless_shell-${EXISTING_VER}/chrome-linux/headless_shell"

    if [[ ! -f "$EXISTING_BINARY" ]]; then
      fail "既存バイナリが見つかりません: $EXISTING_BINARY"
    fi

    mkdir -p "$REQUIRED_DIR"
    ln -sf "$EXISTING_BINARY" "$REQUIRED_DIR/chrome-headless-shell"
    log "✓ Symlink created: $REQUIRED_VER → $EXISTING_VER"

  else
    # ---- ローカルマシン ----
    log "Local machine detected"
    PW_VERSION=$(node -e "console.log(require('$(npm root -g)/agent-browser/node_modules/playwright-core/package.json').version)")
    log "Installing Playwright chromium (v$PW_VERSION)..."
    npx --package="playwright-core@$PW_VERSION" -- playwright-core install chromium 2>&1
  fi

  # ============================================================
  # 4. 修復後の再テスト
  # ============================================================
  if try_browser | grep -q "✓"; then
    close_browser
    log "✓ Browser works after repair"
  else
    close_browser
    fail "修復後もブラウザが起動できません"
  fi
fi

# ============================================================
# 5. 対象URL疎通確認（オプション）
# ============================================================
if [[ -n "$CHECK_URL" ]]; then
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$CHECK_URL" 2>/dev/null || echo "000")
  if [[ "$HTTP_CODE" =~ ^[23] ]]; then
    log "✓ URL reachable: $CHECK_URL (HTTP $HTTP_CODE)"
  else
    log "⚠ URL not reachable: $CHECK_URL (HTTP $HTTP_CODE)"
  fi
fi

echo "SUCCESS:$PREFIX"
