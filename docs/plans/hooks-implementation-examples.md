# Hooks 実装サンプル集

> **参照**: 著者の実際の実装パターンから抽出
> **出典**: `docs/SAMPLE/dot-claude-dev/everything-claude-code/`

---

## 実装パターン

### パターン1: インラインBashスクリプト

**用途**: シンプルで短いチェック処理

**例**: console.log 警告

```json
{
  "matcher": "tool == \"Edit\" && tool_input.file_path matches \"\\\\.(ts|tsx|js|jsx)$\"",
  "hooks": [
    {
      "type": "command",
      "command": "#!/bin/bash\ninput=$(cat)\nfile_path=$(echo \"$input\" | jq -r '.tool_input.file_path // \"\"')\n\nif [ -n \"$file_path\" ] && [ -f \"$file_path\" ]; then\n  console_logs=$(grep -n \"console\\\\.log\" \"$file_path\" 2>/dev/null || true)\n  \n  if [ -n \"$console_logs\" ]; then\n    echo \"[Hook] WARNING: console.log found in $file_path\" >&2\n    echo \"$console_logs\" | head -5 >&2\n  fi\nfi\n\necho \"$input\""
    }
  ]
}
```

**ポイント**:
- `input=$(cat)` でstdinから入力を受け取る
- `jq -r '.tool_input.file_path'` でパラメータを抽出
- `>&2` でエラー出力（ユーザーに表示）
- `echo "$input"` でパススルー（必須）

---

### パターン2: 外部スクリプト参照

**用途**: 複雑な処理、再利用可能なロジック

**例**: セッション開始

```json
{
  "matcher": "*",
  "hooks": [
    {
      "type": "command",
      "command": "~/.claude/hooks/memory-persistence/session-start.sh"
    }
  ]
}
```

**スクリプト**: `session-start.sh`

```bash
#!/bin/bash
# SessionStart Hook - Load previous context on new session

SESSIONS_DIR="${HOME}/.claude/sessions"
LEARNED_DIR="${HOME}/.claude/skills/learned"

# Check for recent session files (last 7 days)
recent_sessions=$(find "$SESSIONS_DIR" -name "*.tmp" -mtime -7 2>/dev/null | wc -l | tr -d ' ')

if [ "$recent_sessions" -gt 0 ]; then
  latest=$(ls -t "$SESSIONS_DIR"/*.tmp 2>/dev/null | head -1)
  echo "[SessionStart] Found $recent_sessions recent session(s)" >&2
  echo "[SessionStart] Latest: $latest" >&2
fi

# Check for learned skills
learned_count=$(find "$LEARNED_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

if [ "$learned_count" -gt 0 ]; then
  echo "[SessionStart] $learned_count learned skill(s) available in $LEARNED_DIR" >&2
fi
```

**ポイント**:
- 環境変数でディレクトリをカスタマイズ可能
- `>&2` でユーザーへの通知
- パススルー不要（SessionStart hookはツール呼び出しなし）

---

### パターン3: 処理ブロック（ツール呼び出し中断）

**用途**: 危険な操作を防止

**例**: dev server tmux 強制

```json
{
  "matcher": "tool == \"Bash\" && tool_input.command matches \"(npm run dev|pnpm( run)? dev|yarn dev|bun run dev)\"",
  "hooks": [
    {
      "type": "command",
      "command": "#!/bin/bash\ninput=$(cat)\necho '[Hook] BLOCKED: Dev server must run in tmux for log access' >&2\necho '[Hook] Use: tmux new-session -d -s dev \"npm run dev\"' >&2\nexit 1"
    }
  ]
}
```

**ポイント**:
- `exit 1` でツール呼び出しを中断
- エラーメッセージで代替コマンドを提案

---

### パターン4: 条件付き処理

**用途**: 環境やコンテキストに応じた処理

**例**: tmux推奨（強制ではない）

```bash
#!/bin/bash
input=$(cat)

if [ -z "$TMUX" ]; then
  echo '[Hook] Consider running in tmux for session persistence' >&2
  echo '[Hook] tmux new -s dev  |  tmux attach -t dev' >&2
fi

echo "$input"  # パススルー継続
```

**ポイント**:
- `if [ -z "$TMUX" ]` で環境チェック
- `exit 1` せず推奨のみ

---

### パターン5: PostToolUse 処理

**用途**: ツール実行後のクリーンアップや追加処理

**例**: Prettier自動フォーマット

```bash
#!/bin/bash
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')

if [ -n "$file_path" ] && [ -f "$file_path" ]; then
  if command -v prettier >/dev/null 2>&1; then
    prettier --write "$file_path" 2>&1 | head -5 >&2
  fi
fi

echo "$input"
```

**ポイント**:
- `tool_input` と `tool_output` 両方がstdinに含まれる
- ツール実行後なのでファイルが存在することが保証される

---

### パターン6: 状態追跡（カウンター）

**用途**: 頻度ベースの提案

**例**: 戦略的コンパクション

```bash
#!/bin/bash
COUNTER_FILE="/tmp/claude-tool-count-$$"
THRESHOLD=${COMPACT_THRESHOLD:-50}

if [ -f "$COUNTER_FILE" ]; then
  count=$(cat "$COUNTER_FILE")
  count=$((count + 1))
  echo "$count" > "$COUNTER_FILE"
else
  echo "1" > "$COUNTER_FILE"
  count=1
fi

if [ "$count" -eq "$THRESHOLD" ]; then
  echo "[StrategicCompact] $THRESHOLD tool calls - consider /compact" >&2
fi

if [ "$count" -gt "$THRESHOLD" ] && [ $((count % 25)) -eq 0 ]; then
  echo "[StrategicCompact] $count tool calls - checkpoint for /compact" >&2
fi
```

**ポイント**:
- `/tmp/` でセッション固有のカウンター（`$$` はプロセスID）
- 環境変数 `COMPACT_THRESHOLD` でカスタマイズ可能
- モジュロ演算 `%` で定期的な通知

---

## hooks.json 完全サンプル

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "tool == \"Bash\" && tool_input.command matches \"git push\"",
        "hooks": [{
          "type": "command",
          "command": "#!/bin/bash\necho '[Hook] Review changes before push...' >&2\nread -r"
        }],
        "description": "Pause before git push"
      },
      {
        "matcher": "tool == \"Write\" && tool_input.file_path matches \"\\\\.(md|txt)$\" && !(tool_input.file_path matches \"README|CLAUDE|AGENTS\")",
        "hooks": [{
          "type": "command",
          "command": "#!/bin/bash\ninput=$(cat)\nfile_path=$(echo \"$input\" | jq -r '.tool_input.file_path')\necho \"[Hook] BLOCKED: Unnecessary doc file: $file_path\" >&2\nexit 1"
        }],
        "description": "Block random .md files"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "tool == \"Edit\" && tool_input.file_path matches \"\\\\.(ts|tsx)$\"",
        "hooks": [{
          "type": "command",
          "command": "#!/bin/bash\ninput=$(cat)\nfile_path=$(echo \"$input\" | jq -r '.tool_input.file_path')\nif [ -f \"$file_path\" ]; then\n  prettier --write \"$file_path\" 2>&1 | head -5 >&2\nfi\necho \"$input\""
        }],
        "description": "Auto-format with Prettier"
      }
    ],
    "PreCompact": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "~/.claude/hooks/memory-persistence/pre-compact.sh"
        }],
        "description": "Save state before compaction"
      }
    ],
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "~/.claude/hooks/memory-persistence/session-start.sh"
        }],
        "description": "Load previous context"
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "~/.claude/hooks/memory-persistence/session-end.sh"
        }],
        "description": "Persist session state"
      },
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "~/.claude/skills/continuous-learning/evaluate-session.sh"
        }],
        "description": "Evaluate for patterns"
      }
    ]
  }
}
```

---

## セッションファイル サンプル

**ファイル名**: `~/.claude/sessions/2026-01-17-debugging-memory.tmp`

```markdown
# Session: Memory Leak Investigation
**Date:** 2026-01-17
**Started:** 09:00
**Last Updated:** 12:00

---

## Current State

Investigating memory leak in production. Heap growing unbounded over 24h period.

### Completed
- [x] Set up heap snapshots in staging
- [x] Identified leak source: event listeners not being cleaned up
- [x] Fixed leak in WebSocket handler
- [x] Verified fix with 4h soak test

### Root Cause
WebSocket `onMessage` handlers were being added on reconnect but not removed on disconnect. After ~1000 reconnects, memory grew from 200MB to 2GB.

### The Fix
\`\`\`javascript
// Before (leaking)
socket.on('connect', () => {
  socket.on('message', handleMessage)
})

// After (fixed)
socket.on('connect', () => {
  socket.off('message', handleMessage) // Remove old listener first
  socket.on('message', handleMessage)
})

// Even better - use once or cleanup on disconnect
socket.on('disconnect', () => {
  socket.removeAllListeners('message')
})
\`\`\`

### Debugging Technique Worth Saving
1. Take heap snapshot at T=0
2. Force garbage collection: \`global.gc()\`
3. Run suspected operation N times
4. Take heap snapshot at T=1
5. Compare snapshots - look for objects with count = N

### Notes for Next Session
- Add memory monitoring alert at 1GB threshold
- Document this debugging pattern for team

### Context to Load
\`\`\`
src/services/websocket.js
\`\`\`
```

**このセッションから学習可能なパターン**:
- エラー解決: メモリリーク修正手法
- デバッグ手法: Heap スナップショット比較
- コードスニペット: WebSocket listener クリーンアップ

→ `/learn` コマンドで `learned/debug-memory-leak.md` として保存可能

---

## matcher 構文リファレンス

### ツール種類でマッチ

```json
"tool == \"Bash\""
"tool == \"Edit\""
"tool == \"Write\""
"tool == \"Read\""
```

### パラメータでマッチ（正規表現）

```json
"tool_input.command matches \"git push\""
"tool_input.file_path matches \"\\\\.(ts|tsx)$\""
"tool_input.file_path matches \"src/.*\\\\.test\\\\.ts$\""
```

### 複合条件

```json
"tool == \"Bash\" && tool_input.command matches \"npm (install|test)\""
"tool == \"Write\" && !(tool_input.file_path matches \"README\")"
```

### ワイルドカード

```json
"*"  // すべてのツール呼び出しにマッチ
```

---

## デバッグTips

### hookが実行されない場合

1. **matcher構文を確認**
   ```bash
   # テスト: Bashツールでコマンド実行時の入力
   echo '{"tool":"Bash","tool_input":{"command":"git push"}}' | jq .
   ```

2. **スクリプトの実行権限を確認**
   ```bash
   chmod +x ~/.claude/hooks/**/*.sh
   ```

3. **エラー出力を確認**
   - hookは `>&2` でエラー出力に書き込む
   - Claude Codeのターミナルで確認可能

### hookがツール呼び出しをブロックする場合

- `exit 1` を使用している場合、ツール呼び出しは中断される
- 意図しないブロックの場合は `exit 1` を削除

### パススルー忘れ

- PreToolUse / PostToolUse hookは必ず `echo "$input"` でパススルー
- SessionStart / Stop hookはパススルー不要（ツール呼び出しなし）

---

## 実装チェックリスト

- [ ] `.claude/hooks/hooks.json` 作成
- [ ] SessionStart hook 実装
- [ ] PreCompact hook 実装
- [ ] Stop hook 実装
- [ ] 全スクリプトに実行権限付与 (`chmod +x`)
- [ ] セッションディレクトリ作成 (`~/.claude/sessions/`)
- [ ] .gitignore に `sessions/*.tmp` 追加
- [ ] テスト実行（新規セッション開始して確認）
