#!/usr/bin/env bash
# caffon 残骸チェック — .zshrc に以下を追加して使用する:
#   source ~/dev/dot-claude-dev/scripts/mac-sleep-prevention/zshrc-snippet.sh

__caffon_check_leftover() {
  local state
  state="$(pmset -g custom 2>/dev/null | awk '/^AC Power/{f=1} f && /disablesleep/ {print $2; exit}')"
  if [[ "${state:-0}" == "1" ]] && [[ ! -f /tmp/caffon.pid ]]; then
    echo "⚠️  [caffon] pmset disablesleep=1 が残留しています (caffon 未起動)" >&2
    echo "   復旧: sudo pmset -a disablesleep 0" >&2
  fi
}

__caffon_check_leftover
unset -f __caffon_check_leftover
