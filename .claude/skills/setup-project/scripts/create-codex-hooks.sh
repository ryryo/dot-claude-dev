#!/bin/bash
# プロジェクトの Codex hooks 設定から旧 commit-check Stop hook を外す
#
# 使い方:
#   bash create-codex-hooks.sh /path/to/project
#
# 終了コード:
#   0 = 削除または未登録（スキップ）
#   1 = エラー

set -e

PROJECT="${1:?Usage: $0 /path/to/project}"
HOOKS="$PROJECT/.codex/hooks.json"
HOOK_PATH=".codex/hooks/dev/commit-check.sh"

remove_commit_check_hook() {
  if [ ! -f "$HOOKS" ]; then
    echo "✓ Codex Stop hook の commit-check は未登録です"
    return
  fi

  if ! command -v jq >/dev/null 2>&1; then
    echo "⚠️  jq が見つからないため、$HOOKS から旧 commit-check hook を削除できません。"
    return
  fi

  if ! jq -e --arg path "$HOOK_PATH" '
    .hooks.Stop[]?.hooks[]?
    | select(.type == "command" and ((.command // "") | contains($path)))
  ' "$HOOKS" >/dev/null 2>&1; then
    echo "✓ Codex Stop hook の commit-check は未登録です"
    return
  fi

  TMP=$(mktemp)
  jq --arg path "$HOOK_PATH" '
    .hooks.Stop = [
      (.hooks.Stop // [])[]
      | .hooks = [
          (.hooks // [])[]
          | select((.type != "command") or (((.command // "") | contains($path)) | not))
        ]
      | select((.hooks | length) > 0)
    ]
    | if (.hooks.Stop | length) == 0 then del(.hooks.Stop) else . end
    | if ((.hooks // {}) | length) == 0 then del(.hooks) else . end
  ' "$HOOKS" > "$TMP"
  mv "$TMP" "$HOOKS"
  echo "✓ Codex Stop hook から commit-check を削除しました"
}

remove_commit_check_hook
