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
  local result
  # data: URL（外部ネットワーク不要、一部環境では https:// プリフィックスで失敗）
  result=$($PREFIX open 'data:text/html,<h1>OK</h1>' 2>&1)
  if echo "$result" | grep -q "✓"; then
    echo "$result"
    return 0
  fi
  # fallback: 外部URL（Cloud Code Web では外部ブロックで失敗する場合あり）
  result=$($PREFIX open 'https://example.com' 2>&1)
  if echo "$result" | grep -q "✓"; then
    echo "$result"
    return 0
  fi
  echo "$result"
  return 1
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
  # 3. 修復: 既存バイナリ流用 → ダウンロード試行
  # ============================================================

  # 要求バージョンをエラーメッセージから取得（data: URL と外部URLの両方を試行）
  ERROR_MSG=$($PREFIX open 'data:text/html,<h1>OK</h1>' 2>&1 || $PREFIX open 'https://example.com' 2>&1 || true)
  close_browser
  REQUIRED_VER=$(echo "$ERROR_MSG" | grep -oP 'chromium_headless_shell-\K[0-9]+' | head -1)
  # Playwright cache path（WSL/Mac/Cloud Code Web 対応）
  if [[ -n "${PLAYWRIGHT_BROWSERS_PATH:-}" ]]; then
    PW_CACHE="$PLAYWRIGHT_BROWSERS_PATH"
  elif [[ -d "$HOME/Library/Caches/ms-playwright" ]]; then
    PW_CACHE="$HOME/Library/Caches/ms-playwright"
  else
    PW_CACHE="$HOME/.cache/ms-playwright"
  fi

  REPAIRED=false

  # 3a. 別バージョンの既存バイナリがあればシンボリックリンクで流用
  if [[ -n "$REQUIRED_VER" && -d "$PW_CACHE" ]]; then
    log "Required: chromium_headless_shell-$REQUIRED_VER"

    # 既存の chromium_headless_shell バイナリを探す（要求バージョン以外）
    for DIR in "$PW_CACHE"/chromium_headless_shell-*/; do
      [[ -d "$DIR" ]] || continue
      EXISTING_VER=$(basename "$DIR" | grep -oP '\d+')
      [[ "$EXISTING_VER" == "$REQUIRED_VER" ]] && continue

      # バイナリの実体を探す（ディレクトリ構造がバージョンで異なる）
      EXISTING_BINARY=""
      for CANDIDATE in \
        "$DIR/chrome-linux/headless_shell" \
        "$DIR/chrome-headless-shell-linux64/chrome-headless-shell"; do
        if [[ -f "$CANDIDATE" ]]; then
          EXISTING_BINARY="$CANDIDATE"
          break
        fi
      done
      [[ -z "$EXISTING_BINARY" ]] && continue

      REQUIRED_DIR="$PW_CACHE/chromium_headless_shell-${REQUIRED_VER}/chrome-headless-shell-linux64"
      mkdir -p "$REQUIRED_DIR"
      ln -sf "$EXISTING_BINARY" "$REQUIRED_DIR/chrome-headless-shell"
      log "✓ Symlink: v$REQUIRED_VER → v$EXISTING_VER ($EXISTING_BINARY)"
      REPAIRED=true
      break
    done
  fi

  # 3b. 既存バイナリがなければダウンロード試行
  if [[ "$REPAIRED" != "true" ]]; then
    log "No existing browser found, attempting download..."
    PW_VERSION=$(node -e "console.log(require('$(npm root -g)/agent-browser/node_modules/playwright-core/package.json').version)" 2>/dev/null || echo "")
    if [[ -n "$PW_VERSION" ]]; then
      log "Installing Playwright chromium (v$PW_VERSION)..."
      if npx --package="playwright-core@$PW_VERSION" -- playwright-core install chromium 2>&1; then
        REPAIRED=true
      else
        log "Download failed"
      fi
    fi
  fi

  if [[ "$REPAIRED" != "true" ]]; then
    fail "ブラウザバイナリの修復に失敗しました"
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
