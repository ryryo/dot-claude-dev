#!/bin/bash
# scripts/create-settings-json.sh
# プロジェクトの .claude/settings.json が存在しない場合にデフォルト設定を作成する
#
# 使い方:
#   bash create-settings-json.sh /path/to/project
#
# 終了コード:
#   0 = 新規作成または既存（スキップ）
#   1 = エラー

PROJECT="${1:?Usage: $0 /path/to/project}"
SETTINGS="$PROJECT/.claude/settings.json"

if [ -f "$SETTINGS" ]; then
  echo "⚠️  $SETTINGS は既に存在します（スキップ）"
  echo "   フック設定が含まれているか手動で確認してください"
  exit 0
fi

mkdir -p "$PROJECT/.claude"

cat > "$SETTINGS" << 'EOF'
{
  "hooks": {
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
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-opencode.sh"
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-local.sh"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/dev/suggest-compact.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/dev/commit-check.sh"
          }
        ]
      }
    ]
  }
}
EOF

echo "✓ $SETTINGS を作成しました"
