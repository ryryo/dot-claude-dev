#!/usr/bin/env bash
# caffon — Mac スリープ防止（蓋閉じ対応）
#   - sudo pmset -a disablesleep 1 を設定してフォアグラウンド常駐
#   - 2 時間経過 or バッテリー 20% 以下で自動解除
#   - Ctrl+C / SIGTERM でも確実に解除（trap）
set -u

readonly PID_FILE="/tmp/caffon.pid"
readonly TIMEOUT_SEC=$((2 * 3600))
readonly BATTERY_THRESHOLD=20
readonly POLL_INTERVAL=60

notify() {
  local msg="$1"
  osascript -e "display notification \"${msg}\" with title \"caffon\"" 2>/dev/null || true
}

disable_sleep_off() {
  sudo -n pmset -a disablesleep 0 2>/dev/null || sudo pmset -a disablesleep 0
}

cleanup() {
  local reason="${1:-manual}"
  trap - EXIT INT TERM
  echo ""
  echo "[caffon] 解除中 (reason: ${reason})..."
  disable_sleep_off
  rm -f "${PID_FILE}"
  notify "スリープ防止を解除しました (${reason})"
  echo "[caffon] 終了"
  exit 0
}

battery_percent() {
  pmset -g batt | awk -F'[ \t;%]+' '/InternalBattery/ {for(i=1;i<=NF;i++) if($i ~ /^[0-9]+$/){print $i; exit}}'
}

format_elapsed() {
  local s=$1
  printf "%02d:%02d:%02d" $((s/3600)) $(((s%3600)/60)) $((s%60))
}

# 残骸検出
if [[ -f "${PID_FILE}" ]]; then
  old_pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
  if [[ -n "${old_pid}" ]] && kill -0 "${old_pid}" 2>/dev/null; then
    echo "[caffon] 既に実行中 (pid=${old_pid})。終了します。"
    exit 1
  fi
  echo "[caffon] ⚠️  前回の pid ファイルが残っています (pid=${old_pid})"
fi

current_state="$(pmset -g custom 2>/dev/null | awk '/^AC Power/{f=1} f && /disablesleep/ {print $2; exit}')"
if [[ "${current_state:-0}" == "1" ]]; then
  echo "[caffon] ⚠️  pmset disablesleep が既に 1 です（残骸の可能性）"
  read -r -p "続行しますか？ [y/N]: " ans
  [[ "${ans}" =~ ^[Yy]$ ]] || { echo "中止しました。"; exit 1; }
fi

echo "[caffon] sudo 権限を要求します..."
sudo pmset -a disablesleep 1 || { echo "[caffon] pmset 失敗"; exit 1; }

echo $$ > "${PID_FILE}"
trap 'cleanup timeout' EXIT
trap 'cleanup sigint' INT
trap 'cleanup sigterm' TERM

start_ts=$(date +%s)
echo "[caffon] スリープ防止を有効化 (pid=$$, timeout=2h, battery_threshold=${BATTERY_THRESHOLD}%)"
echo "[caffon] 停止は Ctrl+C または 別端末で caffoff"
notify "スリープ防止を有効化しました"

while true; do
  sudo -v 2>/dev/null || true

  now=$(date +%s)
  elapsed=$((now - start_ts))

  if (( elapsed >= TIMEOUT_SEC )); then
    cleanup "timeout 2h"
  fi

  batt="$(battery_percent || true)"
  if [[ -n "${batt}" ]] && (( batt <= BATTERY_THRESHOLD )); then
    cleanup "battery ${batt}%"
  fi

  remaining=$((TIMEOUT_SEC - elapsed))
  printf "\r[caffon] 経過 %s / 残 %s / battery %s%%   " \
    "$(format_elapsed "${elapsed}")" \
    "$(format_elapsed "${remaining}")" \
    "${batt:-?}"

  sleep "${POLL_INTERVAL}"
done
