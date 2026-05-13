#!/bin/bash
# プロジェクトの Codex hooks 設定を作成・更新する
#
# 使い方:
#   bash create-codex-hooks.sh /path/to/project
#
# 終了コード:
#   0 = 作成・更新または既存（スキップ）
#   1 = エラー

set -e

PROJECT="${1:?Usage: $0 /path/to/project}"
CODEX_DIR="$PROJECT/.codex"
CONFIG="$CODEX_DIR/config.toml"
HOOKS="$CODEX_DIR/hooks.json"
HOOK_COMMAND='bash "$(git rev-parse --show-toplevel)/.codex/hooks/dev/commit-check.sh"'
HOOK_COMMAND_JSON='bash \"$(git rev-parse --show-toplevel)/.codex/hooks/dev/commit-check.sh\"'
HOOK_TIMEOUT=120
HOOK_STATUS_MESSAGE="Sync PLAN tasks and check uncommitted changes"

mkdir -p "$CODEX_DIR"

ensure_codex_hooks_feature() {
  if [ ! -f "$CONFIG" ]; then
    cat > "$CONFIG" << 'EOF'
[features]
codex_hooks = true
EOF
    echo "✓ $CONFIG を作成しました"
    return
  fi

  if grep -Eq '^[[:space:]]*codex_hooks[[:space:]]*=[[:space:]]*true[[:space:]]*$' "$CONFIG"; then
    echo "✓ $CONFIG は codex_hooks = true 設定済みです"
    return
  fi

  if grep -Eq '^[[:space:]]*codex_hooks[[:space:]]*=' "$CONFIG"; then
    TMP=$(mktemp)
    sed -E 's/^([[:space:]]*codex_hooks[[:space:]]*=[[:space:]]*).*/\1true/' "$CONFIG" > "$TMP"
    mv "$TMP" "$CONFIG"
    echo "✓ $CONFIG の codex_hooks を true に更新しました"
    return
  fi

  if grep -Eq '^[[:space:]]*\[features\][[:space:]]*$' "$CONFIG"; then
    TMP=$(mktemp)
    awk '
      BEGIN { in_features = 0; inserted = 0 }
      /^[[:space:]]*\[features\][[:space:]]*$/ {
        print
        print "codex_hooks = true"
        in_features = 1
        inserted = 1
        next
      }
      /^[[:space:]]*\[/ {
        in_features = 0
      }
      { print }
      END {
        if (!inserted) {
          print ""
          print "[features]"
          print "codex_hooks = true"
        }
      }
    ' "$CONFIG" > "$TMP"
    mv "$TMP" "$CONFIG"
    echo "✓ $CONFIG の [features] に codex_hooks = true を追加しました"
  else
    {
      echo ""
      echo "[features]"
      echo "codex_hooks = true"
    } >> "$CONFIG"
    echo "✓ $CONFIG に [features] を追加しました"
  fi
}

ensure_hooks_json() {
  if [ ! -f "$HOOKS" ]; then
    cat > "$HOOKS" << EOF
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOOK_COMMAND_JSON",
            "timeout": $HOOK_TIMEOUT,
            "statusMessage": "$HOOK_STATUS_MESSAGE"
          }
        ]
      }
    ]
  }
}
EOF
    echo "✓ $HOOKS を作成しました"
    return
  fi

  if command -v jq >/dev/null 2>&1; then
    if jq -e --arg cmd "$HOOK_COMMAND" '
      .hooks.Stop[]?.hooks[]? | select(.type == "command" and .command == $cmd)
    ' "$HOOKS" >/dev/null 2>&1; then
      echo "✓ Codex Stop hook の commit-check は登録済みです"
      TMP=$(mktemp)
      jq \
        --arg cmd "$HOOK_COMMAND" \
        --arg msg "$HOOK_STATUS_MESSAGE" \
        --argjson timeout "$HOOK_TIMEOUT" \
        '
          (.hooks.Stop[]?.hooks[]? | select(.type == "command" and .command == $cmd)) |=
            (.timeout = $timeout | .statusMessage = $msg)
        ' "$HOOKS" > "$TMP"
      mv "$TMP" "$HOOKS"
      echo "✓ Codex Stop hook の timeout/statusMessage を更新しました"
    else
      TMP=$(mktemp)
      jq \
        --arg cmd "$HOOK_COMMAND" \
        --arg msg "$HOOK_STATUS_MESSAGE" \
        --argjson timeout "$HOOK_TIMEOUT" \
        '
          .hooks = (.hooks // {}) |
          .hooks.Stop = ((.hooks.Stop // []) + [{
            "hooks": [{
              "type": "command",
              "command": $cmd,
              "timeout": $timeout,
              "statusMessage": $msg
            }]
          }])
        ' "$HOOKS" > "$TMP"
      mv "$TMP" "$HOOKS"
      echo "✓ Codex Stop hook に commit-check を追加しました"
    fi
  else
    echo "⚠️  $HOOKS は既に存在します。jq が見つからないため、Codex Stop hook の登録状態は未確認です。"
  fi
}

ensure_codex_hooks_feature
ensure_hooks_json
