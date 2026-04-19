#!/usr/bin/env bash
# caffoff — caffon を停止してスリープ防止を解除する
set -u

readonly PID_FILE="/tmp/caffon.pid"

if [[ ! -f "${PID_FILE}" ]]; then
  echo "[caffoff] caffon は動作していません (pid ファイルなし)"
  exit 0
fi

pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
if [[ -z "${pid}" ]] || ! kill -0 "${pid}" 2>/dev/null; then
  echo "[caffoff] プロセス ${pid:-?} は存在しません。pid ファイルを削除します。"
  rm -f "${PID_FILE}"
  echo "[caffoff] disablesleep を念のため 0 に戻します (sudo 必要)"
  sudo pmset -a disablesleep 0 || true
  exit 0
fi

echo "[caffoff] caffon (pid=${pid}) に SIGTERM を送信..."
kill -TERM "${pid}"

for _ in 1 2 3 4 5; do
  sleep 1
  [[ -f "${PID_FILE}" ]] || { echo "[caffoff] 停止完了"; exit 0; }
done

echo "[caffoff] ⚠️  5 秒以内に停止しませんでした。手動確認してください:"
echo "  ps -p ${pid}"
echo "  pmset -g | grep ' sleep'"
exit 1
