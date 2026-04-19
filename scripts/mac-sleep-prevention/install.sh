#!/usr/bin/env bash
# install.sh — caffon / caffoff を ~/.local/bin/ にシンボリックリンクで配置する
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly BIN_DIR="${HOME}/.local/bin"

mkdir -p "${BIN_DIR}"

link() {
  local src="$1" name="$2"
  local dst="${BIN_DIR}/${name}"

  if [[ -L "${dst}" ]]; then
    local current
    current="$(readlink "${dst}")"
    if [[ "${current}" == "${src}" ]]; then
      echo "  OK   ${name} -> ${src} (既存)"
      return
    fi
    echo "  WARN ${name} が別のリンク先を指しています: ${current}"
    echo "       上書きしますか？ [y/N]: "
    read -r ans
    [[ "${ans}" =~ ^[Yy]$ ]] || { echo "  SKIP ${name}"; return; }
  elif [[ -e "${dst}" ]]; then
    echo "  ERR  ${dst} はシンボリックリンクではなく実ファイルです。手動で確認してください。"
    return 1
  fi

  ln -sf "${src}" "${dst}"
  echo "  OK   ${name} -> ${src}"
}

echo "[install] インストール先: ${BIN_DIR}"
link "${SCRIPT_DIR}/caffon.sh"  caffon
link "${SCRIPT_DIR}/caffoff.sh" caffoff

echo ""
echo "[install] 完了"
echo ""
echo "次のステップ:"
echo "  1. PATH に ${BIN_DIR} が含まれていることを確認: echo \$PATH | tr ':' '\\n' | grep local/bin"
echo "  2. .zshrc の末尾に以下を追加（残骸検出の警告を有効化）:"
echo "     source ${SCRIPT_DIR}/zshrc-snippet.sh"
echo "  3. 動作確認: caffon → Ctrl+C → pmset -g | grep ' sleep'"
