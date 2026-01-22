# Hooks 実装サンプル集（コア2機能版）

> **対象**: セッションメモリ永続化 + 戦略的コンパクション
> **参照**: 著者の実装パターンをストーリー駆動開発に統合
> **出典**: `docs/SAMPLE/dot-claude-dev/everything-claude-code/`

---

## 実装するHooks一覧

| Hook | スクリプト | 機能 |
|------|-----------|------|
| **SessionStart** | `session-start.sh` | ストーリーセッション or グローバルセッション読み込み |
| **PreCompact** | `pre-compact.sh` | コンパクション前に状態保存 |
| **Stop** | `session-end.sh` | セッション終了時に状態保存 |
| **PreToolUse** | `suggest-compact.sh` | 戦略的コンパクション：50ツール呼び出しで提案 |

---

## 実装パターン

### パターン1: 外部スクリプト参照（SessionStart）

**用途**: セッション開始時にストーリーコンテキストを読み込む

**hooks.json**:
```json
{
  "matcher": "*",
  "hooks": [{
    "type": "command",
    "command": "~/.claude/hooks/memory-persistence/session-start.sh"
  }],
  "description": "Load story or global session"
}
```

**スクリプト**: `~/.claude/hooks/memory-persistence/session-start.sh`

```bash
#!/bin/bash
# SessionStart Hook - Load story session or global session

LEARNED_DIR="${HOME}/.claude/skills/learned"  # dev:feedback Phase 4 で使用

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
- パススルー不要（SessionStart hookはツール呼び出しなし）

---

### パターン2: PreCompact（状態保存）

**用途**: コンパクション前に現在の状態を保存

**hooks.json**:
```json
{
  "matcher": "*",
  "hooks": [{
    "type": "command",
    "command": "~/.claude/hooks/memory-persistence/pre-compact.sh"
  }],
  "description": "Save state before compaction"
}
```

**スクリプト**: `~/.claude/hooks/memory-persistence/pre-compact.sh`

```bash
#!/bin/bash
# PreCompact Hook - Save current state before compaction

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

if [ -f "TODO.md" ] && [ -f "SESSION.md" ]; then
  # ストーリー内セッション - SESSION.md を更新

  # "Last Updated" 行を更新
  if grep -q "Last Updated" SESSION.md; then
    # macOS対応: -i '' が必要
    sed -i '' "s/\*\*Last Updated:\*\*.*/\*\*Last Updated:\*\* $TIMESTAMP/" SESSION.md
  fi

  echo "[PreCompact] Saved story session state to SESSION.md" >&2

else
  # グローバルセッション - .tmp ファイルに保存
  SESSIONS_DIR="${HOME}/.claude/sessions"
  mkdir -p "$SESSIONS_DIR"

  TODAY=$(date '+%Y-%m-%d')
  SESSION_FILE="$SESSIONS_DIR/$TODAY-global.tmp"

  {
    echo "# Global Session: $TODAY"
    echo "**Last Updated**: $TIMESTAMP"
    echo ""
    echo "## State Snapshot"
    echo "Session compacted at $TIMESTAMP"
    echo ""
    pwd
  } > "$SESSION_FILE"

  echo "[PreCompact] Saved global session state to $SESSION_FILE" >&2
fi
```

**ポイント**:
- ストーリー内：SESSION.mdのタイムスタンプを更新
- ストーリー外：グローバル.tmpに状態を保存

---

### パターン3: Stop（セッション終了時の保存）

**hooks.json**:
```json
{
  "matcher": "*",
  "hooks": [{
    "type": "command",
    "command": "~/.claude/hooks/memory-persistence/session-end.sh"
  }],
  "description": "Persist session state on exit"
}
```

**スクリプト**: `~/.claude/hooks/memory-persistence/session-end.sh`

```bash
#!/bin/bash
# Stop Hook - Persist session state on exit

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

if [ -f "TODO.md" ] && [ -f "SESSION.md" ]; then
  # ストーリー内セッション

  # Last Updated を更新
  if grep -q "Last Updated" SESSION.md; then
    sed -i '' "s/\*\*Last Updated:\*\*.*/\*\*Last Updated:\*\* $TIMESTAMP/" SESSION.md
  fi

  echo "[Stop] Session saved to SESSION.md" >&2

else
  # グローバルセッション
  SESSIONS_DIR="${HOME}/.claude/sessions"
  mkdir -p "$SESSIONS_DIR"

  TODAY=$(date '+%Y-%m-%d')
  SESSION_FILE="$SESSIONS_DIR/$TODAY-global.tmp"

  {
    echo "# Global Session: $TODAY"
    echo "**Ended**: $TIMESTAMP"
  } > "$SESSION_FILE"

  echo "[Stop] Global session saved to $SESSION_FILE" >&2
fi
```

---

### パターン4: 状態追跡（戦略的コンパクション）

**用途**: ツール呼び出し回数をカウントし、50回で /compact を提案

**hooks.json**:
```json
{
  "matcher": "*",
  "hooks": [{
    "type": "command",
    "command": "~/.claude/hooks/strategic-compact/suggest-compact.sh"
  }],
  "description": "Suggest /compact at logical checkpoints"
}
```

**スクリプト**: `~/.claude/hooks/strategic-compact/suggest-compact.sh`

```bash
#!/bin/bash
# PreToolUse Hook - Suggest compact at logical checkpoints

COUNTER_FILE="/tmp/claude-tool-count-$$"
THRESHOLD=${COMPACT_THRESHOLD:-50}

# カウンターを読み込み・更新
if [ -f "$COUNTER_FILE" ]; then
  count=$(cat "$COUNTER_FILE")
  count=$((count + 1))
  echo "$count" > "$COUNTER_FILE"
else
  echo "1" > "$COUNTER_FILE"
  count=1
fi

# 50回目で提案
if [ "$count" -eq "$THRESHOLD" ]; then
  echo "💡 $THRESHOLD tool calls reached - consider /compact if transitioning phases" >&2
fi

# その後25回ごとに再提案
if [ "$count" -gt "$THRESHOLD" ] && [ $((count % 25)) -eq 0 ]; then
  echo "💡 $count tool calls - checkpoint for /compact if context is stale" >&2
fi
```

**ポイント**:
- `/tmp/claude-tool-count-$$` でプロセス固有のカウンター
- 環境変数 `COMPACT_THRESHOLD` でカスタマイズ可能
- 50回目 + 以降25回ごとに提案

---

## hooks.json 完全サンプル

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "~/.claude/hooks/memory-persistence/session-start.sh"
        }],
        "description": "Load story or global session"
      }
    ],
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "~/.claude/hooks/strategic-compact/suggest-compact.sh"
        }],
        "description": "Suggest /compact at logical checkpoints"
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
    "Stop": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "~/.claude/hooks/memory-persistence/session-end.sh"
        }],
        "description": "Persist session state on exit"
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
- 境界値: 空文字、null, undefined

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
```

**配置**: ストーリーディレクトリ内に配置され、Git管理される

**dev:developing での自動更新**:
- タスク完了時に "Completed Tasks" セクションを更新
- /compact 実行前に PreCompact hook が状態を保存

**パターンの学習**:
- 繰り返しパターンは dev:feedback Phase 4 で検出・スキル化
- ストーリー完了時に DESIGN.md へ記録

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

### ワイルドカード

```json
"*"  // すべてのツール呼び出しにマッチ
```

---

## デバッグTips

### hookが実行されない場合

1. **スクリプトの実行権限を確認**
   ```bash
   chmod +x ~/.claude/hooks/**/*.sh
   ```

2. **エラー出力を確認**
   - hookは `>&2` でエラー出力に書き込む
   - Claude Codeのターミナルで確認可能

### パススルー忘れ

- PreToolUse hookは必ず `echo "$input"` でパススルー
- SessionStart / Stop hookはパススルー不要（ツール呼び出しなし）

---

## 実装チェックリスト

### Hooks設定

- [ ] `.claude/hooks/hooks.json` 作成
- [ ] SessionStart hook 実装（ストーリー検出対応）
- [ ] PreCompact hook 実装（ストーリー検出対応）
- [ ] Stop hook 実装（session-end.sh）
- [ ] PreToolUse hook 実装（suggest-compact.sh）
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
- [ ] 50ツール呼び出し → 戦略的コンパクション提案確認
