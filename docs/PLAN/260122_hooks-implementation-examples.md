# Hooks 実装サンプル集（ストーリー統合版）

> **参照**: 著者の実際の実装パターンから抽出し、ストーリー駆動開発に統合
> **出典**: `docs/SAMPLE/dot-claude-dev/everything-claude-code/`
> **統合**: ストーリーごとのセッション管理に対応

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

**スクリプト**: `session-start.sh` (ストーリー対応版)

```bash
#!/bin/bash
# SessionStart Hook - Load story session or global session

LEARNED_DIR="${HOME}/.claude/skills/learned"

# ストーリーディレクトリの検出（TODO.md の存在確認）
if [ -f "TODO.md" ] && [ -f "SESSION.md" ]; then
  # ストーリー内のセッション
  FEATURE=$(grep -m1 "^# Session Log: " SESSION.md | sed 's/# Session Log: //' || echo "unknown")
  LAST_UPDATED=$(grep "Last Updated" SESSION.md | sed 's/\*\*Last Updated:\*\* //' || echo "unknown")

  echo "📝 Story Session Found" >&2
  echo "  Story: $FEATURE" >&2
  echo "  Last Updated: $LAST_UPDATED" >&2

  # Completed Tasks をカウント
  COMPLETED=$(grep -c "^- \[x\]" TODO.md 2>/dev/null || echo "0")
  IN_PROGRESS=$(grep -c "^- \[ \]" TODO.md 2>/dev/null || echo "0")
  echo "  Progress: $COMPLETED completed, $IN_PROGRESS remaining" >&2

elif [ -f "TODO.md" ] && [ ! -f "SESSION.md" ]; then
  # ストーリー内だがSESSION.mdがない（新規ストーリー）
  echo "🆕 New Story Detected (SESSION.md not found)" >&2
  echo "  Run /dev:story to initialize SESSION.md" >&2

else
  # ストーリー外 - グローバルセッション確認
  SESSIONS_DIR="${HOME}/.claude/sessions"
  TODAY=$(date '+%Y-%m-%d')
  GLOBAL_SESSION="$SESSIONS_DIR/$TODAY-global.tmp"

  if [ -f "$GLOBAL_SESSION" ]; then
    echo "🌐 Global Session Found: $GLOBAL_SESSION" >&2
  else
    echo "🌐 Global Session (outside story context)" >&2
  fi
fi

# Check for learned skills
learned_count=$(find "$LEARNED_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

if [ "$learned_count" -gt 0 ]; then
  echo "💡 $learned_count learned skill(s) available in $LEARNED_DIR" >&2
fi
```

**ポイント**:
- **ストーリー検出**: TODO.mdの存在でストーリーコンテキストを判定
- **二重管理**: ストーリー内SESSION.md + グローバル.tmp
- **進捗表示**: ストーリー内ではTODO.mdの進捗も表示
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

### ストーリー単位セッション（推奨）

**ファイルパス**: `docs/features/user-auth/stories/implement-email-validation/SESSION.md`

```markdown
# Session Log: implement-email-validation

**Feature**: user-auth
**Story**: implement-email-validation
**Started**: 2026-01-22 14:30
**Last Updated**: 2026-01-22 16:45

---

## Current State

TDD ワークフローで email バリデーション機能を実装中。
RED → GREEN → REFACTOR の第2サイクル完了。

### Completed Tasks (TODO.md から自動更新)
- [x] [TDD][RED] validateEmail のテスト作成
- [x] [TDD][GREEN] validateEmail の実装
- [x] [TDD][REFACTOR] validateEmail のリファクタリング
- [x] [TDD][REVIEW] セルフレビュー
- [ ] [TDD][CHECK] lint/format/build  ← 次はここ

### Progress Summary
- Phase: TDD - CHECK フェーズ
- Files Modified:
  - `src/utils/validation.ts`
  - `src/utils/validation.test.ts`

---

## Context

### 実装の要点

**バリデーションロジック**:
- RFC 5322 準拠の簡易版正規表現
- 空文字・null チェック
- Result型で統一的なエラーハンドリング

**テストカバレッジ**:
- 正常系: 標準的なメールアドレス 5パターン
- 異常系: 不正形式 8パターン
- 境界値: 空文字、null、undefined

### 学んだこと

**Result型パターンの有効性**:
```typescript
type Result<T> =
  | { ok: true; value: T }
  | { ok: false; error: string };
```
- エラーハンドリングが型安全
- テストが書きやすい
- 呼び出し側で強制的にエラーチェック

**Zodとの使い分け**:
- 単純なバリデーション → 自前のResult型
- フォーム全体・複雑なスキーマ → Zod

---

## Issues & Resolutions

### Issue 1: Vitest の expect.toEqual が構造等価で失敗
**原因**: エラーオブジェクトに追加プロパティが含まれていた
**解決**: `expect.objectContaining()` で必要なプロパティのみ検証

### Issue 2: TypeScript strict mode でのnullチェック
**学び**: `value ?? ''` より `value == null` の方が意図明確

---

## Next Steps

1. lint/format/build 実行
2. 問題なければコミット
3. validatePassword の実装に移行（新規セッション開始）

---

## Files to Keep Context

```
src/utils/validation.ts
src/utils/validation.test.ts
docs/features/user-auth/stories/implement-email-validation/TODO.md
```

---

## Notes for /learn Evaluation

このセッションで**繰り返し使用した手法**:
- Result型パターン（3回目の使用 → スキル化検討）
- TDDサイクルの厳密な遵守（効果実感）
- expect.objectContaining パターン（2回目 → 定着）

**推奨アクション**:
- Result型パターンを `learned/result-type-pattern.md` として保存
```

**配置**: ストーリーディレクトリ内に配置され、Git管理される

**dev:developing での自動更新**:
- タスク完了時に "Completed Tasks" セクションを更新
- /compact 実行前に PreCompact hook が状態を保存

**このセッションから学習可能なパターン**:
- Result型パターンの実装と使い方
- Vitest での構造比較テスト
- TDDサイクルの実践ノウハウ

→ `/learn` コマンドで `learned/result-type-pattern.md` として保存可能

---

### グローバルセッション（補助的）

**ファイルパス**: `~/.claude/sessions/2026-01-22-global.tmp`

```markdown
# Global Session: 2026-01-22

**Date**: 2026-01-22
**Context**: Story外の作業（緊急バグ修正等）

---

## Quick Fixes

### 14:00 - Production Hotfix
- 本番環境のメモリリーク緊急対応
- WebSocket listener cleanup を適用
- デプロイ完了

### 16:00 - Documentation Update
- README.md の環境構築手順を更新
- Node.js バージョン要件を明記

---

## Notes

ストーリー外の短時間作業のみ記録。
通常はストーリー単位のSESSION.mdを使用。
```

**用途**: ストーリー外の緊急対応・軽微な作業のみ

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

### Hooks設定

- [ ] `.claude/hooks/hooks.json` 作成
- [ ] SessionStart hook 実装（ストーリー検出対応）
- [ ] PreCompact hook 実装（ストーリー検出対応）
- [ ] Stop hook 実装（ストーリー検出対応）
- [ ] 全スクリプトに実行権限付与 (`chmod +x`)

### ディレクトリ構成

- [ ] グローバルセッションディレクトリ作成 (`~/.claude/sessions/`)
- [ ] .gitignore に `.claude/sessions/*.tmp` 追加（グローバルセッションのみ）
- [ ] ストーリーディレクトリの SESSION.md は Git 管理対象（.gitignore 不要）

### dev:story スキル更新

- [ ] `.claude/skills/dev/story/SKILL.md` に Phase 4.2 追加
- [ ] SESSION.md テンプレートを追加

### テスト実行

- [ ] ストーリー外で新規セッション開始 → グローバルセッション確認
- [ ] /dev:story 実行 → SESSION.md 自動作成確認
- [ ] ストーリー内で新規セッション開始 → ストーリーセッション読み込み確認
- [ ] /compact 実行 → PreCompact hook で状態保存確認
- [ ] セッション終了 → Stop hook で SESSION.md 更新確認
