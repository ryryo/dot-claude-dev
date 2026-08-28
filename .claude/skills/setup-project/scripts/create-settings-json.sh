#!/bin/bash
# scripts/create-settings-json.sh
# プロジェクトの .claude/settings.json を作成し、旧 commit-check Stop hook を外す
#
# 使い方:
#   bash create-settings-json.sh /path/to/project
#
# 終了コード:
#   0 = 新規作成または既存設定の更新・確認
#   1 = エラー

PROJECT="${1:?Usage: $0 /path/to/project}"
SETTINGS="$PROJECT/.claude/settings.json"
HOOK_PATH=".claude/hooks/dev/commit-check.sh"

if [ -f "$SETTINGS" ]; then
  if ! command -v jq >/dev/null 2>&1; then
    echo "⚠️  jq が見つからないため、$SETTINGS から旧 commit-check hook を削除できません。"
    exit 0
  fi

  if ! jq -e --arg path "$HOOK_PATH" '
    .hooks.Stop[]?.hooks[]?
    | select(.type == "command" and ((.command // "") | contains($path)))
  ' "$SETTINGS" >/dev/null 2>&1; then
    echo "✓ Claude Stop hook の commit-check は未登録です"
    exit 0
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
  ' "$SETTINGS" > "$TMP"
  mv "$TMP" "$SETTINGS"
  echo "✓ Claude Stop hook から commit-check を削除しました"
  exit 0
fi

mkdir -p "$PROJECT/.claude"

cat > "$SETTINGS" << 'EOF'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/dev/sync-spec-md-hook.sh"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-claude-remote.sh"
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-local.sh"
          }
        ]
      }
    ]
  }
}
EOF

echo "✓ $SETTINGS を作成しました"
