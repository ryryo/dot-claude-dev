# Hooks 実装サンプル集（TODO.md拡張版）

> **対象**: TODO.md拡張 + 戦略的コンパクション
> **方式**: SESSION.md不要、TODO.mdにメタデータを追加
> **ストーリー一覧**: キャッシュ方式（セッション終了時に保存、開始時は読むだけ）

---

## 実装するHooks一覧 + スキル統合

| Hook/スキル | スクリプト | 機能 |
|------|-----------|------|
| **SessionStart** | `session-start.sh` | TODO.md または保存済みストーリー一覧を表示 |
| **PreCompact** | `pre-compact.sh` | TODO.md の Last Updated を更新 + ストーリー一覧保存 |
| **Stop** | `session-end.sh` | TODO.md の Last Updated を更新 + ストーリー一覧保存 |
| **PreToolUse** | `suggest-compact.sh` | 戦略的コンパクション：50ツール呼び出しで提案 |
| **dev:feedback** | Phase 5 追加 | ストーリー完了時に in-progress-stories.tmp を更新 |

---

## 実装パターン

### パターン1: SessionStart（TODO.md読み込み）

**用途**: セッション開始時にストーリー進捗または保存済み一覧を表示

**hooks.json**:
```json
{
  "matcher": "*",
  "hooks": [{
    "type": "command",
    "command": "~/.claude/hooks/memory-persistence/session-start.sh"
  }],
  "description": "Load TODO.md metadata or cached stories"
}
```

**スクリプト**: `~/.claude/hooks/memory-persistence/session-start.sh`

```bash
#!/bin/bash
# SessionStart Hook - Load TODO.md metadata or cached stories

SESSIONS_DIR="${HOME}/.claude/sessions"
STORIES_FILE="$SESSIONS_DIR/in-progress-stories.tmp"

if [ -f "TODO.md" ]; then
  # ストーリー内 - 現在のTODO.mdを表示
  LAST_UPDATED=$(grep "^\*\*Last Updated\*\*:" TODO.md | sed 's/\*\*Last Updated\*\*: //' || echo "unknown")

  echo "📝 Story Session Found" >&2
  echo "  Last Updated: $LAST_UPDATED" >&2

  # タスク進捗をカウント
  COMPLETED=$(grep -c "^- \[x\]" TODO.md 2>/dev/null || echo "0")
  IN_PROGRESS=$(grep -c "^- \[ \]" TODO.md 2>/dev/null || echo "0")
  echo "  Progress: $COMPLETED completed, $IN_PROGRESS remaining" >&2

  # Blockers セクションがあれば通知
  if grep -q "^## Blockers" TODO.md; then
    echo "  ⚠️  Blockers section exists - check TODO.md" >&2
  fi

elif [ -f "$STORIES_FILE" ]; then
  # プロジェクトルート - 保存されたストーリー一覧を表示
  echo "📋 Recent In-Progress Stories:" >&2
  tail -n +4 "$STORIES_FILE" | head -5 >&2  # ヘッダー3行スキップ、最初の5件
  echo "" >&2
  echo "💡 Tip: Say 'resume story' to choose and continue a story" >&2

else
  echo "ℹ️  No TODO.md found (outside story context)" >&2
fi
```

**ポイント**:
- **ストーリー内**: TODO.mdの進捗を表示（0.001秒以下）
- **プロジェクトルート**: 保存済みストーリー一覧を表示 + ストーリー再開のヒント
- **パフォーマンス**: SessionStartでfind検索を実行しない
- **対話的選択**: Claudeが自動的にAskUserQuestionでストーリー選択を促す
- パススルー不要（SessionStart hookはツール呼び出しなし）

---

### パターン2: PreCompact（TODO.md更新 + ストーリー一覧保存）

**用途**: コンパクション前にTODO.mdを更新し、進行中ストーリー一覧を保存

**hooks.json**:
```json
{
  "matcher": "*",
  "hooks": [{
    "type": "command",
    "command": "~/.claude/hooks/memory-persistence/pre-compact.sh"
  }],
  "description": "Update TODO.md + Save stories list"
}
```

**スクリプト**: `~/.claude/hooks/memory-persistence/pre-compact.sh`

```bash
#!/bin/bash
# PreCompact Hook - Update TODO.md Last Updated + Save stories list

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
SESSIONS_DIR="${HOME}/.claude/sessions"
mkdir -p "$SESSIONS_DIR"

# 現在のストーリーのTODO.md更新
if [ -f "TODO.md" ]; then
  # "Last Updated" 行を更新
  if grep -q "^\*\*Last Updated\*\*:" TODO.md; then
    sed -i '' "s/^\*\*Last Updated\*\*:.*/\*\*Last Updated\*\*: $TIMESTAMP/" TODO.md
  else
    # Last Updated が存在しない場合は追加
    sed -i '' "1a\\
\\
\*\*Last Updated\*\*: $TIMESTAMP\\
" TODO.md
  fi

  echo "[PreCompact] Updated TODO.md Last Updated: $TIMESTAMP" >&2
fi

# 進行中ストーリー一覧を保存（次回SessionStart用）
{
  echo "# In-Progress Stories"
  echo "**Updated**: $TIMESTAMP"
  echo ""

  find docs/features -name "TODO.md" -type f 2>/dev/null | while read todo; do
    if grep -q "^- \[ \]" "$todo"; then
      STORY_PATH=$(dirname "$todo")
      LAST_UPDATED=$(grep "^\*\*Last Updated\*\*:" "$todo" | sed 's/\*\*Last Updated\*\*: //' || echo "unknown")
      COMPLETED=$(grep -c "^- \[x\]" "$todo" 2>/dev/null || echo "0")
      IN_PROGRESS=$(grep -c "^- \[ \]" "$todo" 2>/dev/null || echo "0")

      echo "- $STORY_PATH | Updated: $LAST_UPDATED | Progress: $COMPLETED/$((COMPLETED + IN_PROGRESS))"
    fi
  done
} > "$SESSIONS_DIR/in-progress-stories.tmp"

echo "[PreCompact] Saved in-progress stories list" >&2
```

**ポイント**:
- **TODO.md更新**: Last Updatedのタイムスタンプを更新
- **ストーリー一覧保存**: find検索は**ここで1回だけ実行**
- **キャッシュ作成**: 次回SessionStartで高速に読み込めるよう保存

---

### パターン3: Stop（TODO.md更新 + ストーリー一覧保存）

**用途**: セッション終了時にTODO.mdを更新し、進行中ストーリー一覧を保存

**hooks.json**:
```json
{
  "matcher": "*",
  "hooks": [{
    "type": "command",
    "command": "~/.claude/hooks/memory-persistence/session-end.sh"
  }],
  "description": "Update TODO.md + Save stories list on exit"
}
```

**スクリプト**: `~/.claude/hooks/memory-persistence/session-end.sh`

```bash
#!/bin/bash
# Stop Hook - Update TODO.md Last Updated + Save stories list on exit

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
SESSIONS_DIR="${HOME}/.claude/sessions"
mkdir -p "$SESSIONS_DIR"

# 現在のストーリーのTODO.md更新
if [ -f "TODO.md" ]; then
  if grep -q "^\*\*Last Updated\*\*:" TODO.md; then
    sed -i '' "s/^\*\*Last Updated\*\*:.*/\*\*Last Updated\*\*: $TIMESTAMP/" TODO.md
  else
    sed -i '' "1a\\
\\
\*\*Last Updated\*\*: $TIMESTAMP\\
" TODO.md
  fi

  echo "[Stop] Updated TODO.md Last Updated: $TIMESTAMP" >&2
fi

# 進行中ストーリー一覧を保存（次回SessionStart用）
{
  echo "# In-Progress Stories"
  echo "**Updated**: $TIMESTAMP"
  echo ""

  find docs/features -name "TODO.md" -type f 2>/dev/null | while read todo; do
    if grep -q "^- \[ \]" "$todo"; then
      STORY_PATH=$(dirname "$todo")
      LAST_UPDATED=$(grep "^\*\*Last Updated\*\*:" "$todo" | sed 's/\*\*Last Updated\*\*: //' || echo "unknown")
      COMPLETED=$(grep -c "^- \[x\]" "$todo" 2>/dev/null || echo "0")
      IN_PROGRESS=$(grep -c "^- \[ \]" "$todo" 2>/dev/null || echo "0")

      echo "- $STORY_PATH | Updated: $LAST_UPDATED | Progress: $COMPLETED/$((COMPLETED + IN_PROGRESS))"
    fi
  done
} > "$SESSIONS_DIR/in-progress-stories.tmp"

echo "[Stop] Saved in-progress stories list" >&2
```

**ポイント**:
- **PreCompactと同じ処理**: セッション終了時にも最新の一覧を保存
- **find検索のタイミング**: ユーザーが離席するタイミングなので体感なし

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

### パターン5: dev:feedback統合（ストーリー完了時の一覧更新）

**用途**: ストーリー完了時に進行中ストーリー一覧から完了したストーリーを削除

**ファイル**: `.claude/skills/dev/feedback/SKILL.md`

**Phase 5 追加**:

```bash
# dev:feedback の最終フェーズで実行
SESSIONS_DIR="${HOME}/.claude/sessions"
STORIES_FILE="$SESSIONS_DIR/in-progress-stories.tmp"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

# 進行中ストーリー一覧を再生成（完了したストーリーを除外）
{
  echo "# In-Progress Stories"
  echo "**Updated**: $TIMESTAMP"
  echo ""

  find docs/features -name "TODO.md" -type f 2>/dev/null | while read todo; do
    if grep -q "^- \[ \]" "$todo"; then
      STORY_PATH=$(dirname "$todo")
      LAST_UPDATED=$(grep "^\*\*Last Updated\*\*:" "$todo" | sed 's/\*\*Last Updated\*\*: //' || echo "unknown")
      COMPLETED=$(grep -c "^- \[x\]" "$todo" 2>/dev/null || echo "0")
      IN_PROGRESS=$(grep -c "^- \[ \]" "$todo" 2>/dev/null || echo "0")

      echo "- $STORY_PATH | Updated: $LAST_UPDATED | Progress: $COMPLETED/$((COMPLETED + IN_PROGRESS))"
    fi
  done
} > "$STORIES_FILE"

echo "[dev:feedback] Updated in-progress stories list (removed completed story)" >&2
```

**ポイント**:
- **実行タイミング**: PR作成・Worktreeクリーンアップの後
- **メリット**: ストーリー完了直後に一覧から削除（PreCompact/Stopを待たない）
- **確実性**: 次回SessionStartで完了済みストーリーが表示されない

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
        "description": "Load TODO.md metadata or cached stories"
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
        "description": "Update TODO.md + Save stories list"
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "~/.claude/hooks/memory-persistence/session-end.sh"
        }],
        "description": "Update TODO.md + Save stories list on exit"
      }
    ]
  }
}
```

---

## ファイルサンプル

### 拡張されたTODO.md

**ファイルパス**: `docs/features/user-auth/stories/implement-email-validation/TODO.md`

```markdown
# TODO: implement-email-validation

**Last Updated**: 2026-01-22 16:45

## Blockers
- パスワードポリシー仕様確認待ち

## Tasks

- [x] [TDD][RED] validateEmail のテスト作成
- [x] [TDD][GREEN] validateEmail の実装
- [x] [TDD][REFACTOR] リファクタリング
- [x] [TDD][REVIEW] セルフレビュー
- [ ] [TDD][CHECK] lint/format/build
- [ ] [TDD][RED] validatePassword のテスト作成
  <!-- 注: 最低8文字、大文字小文字数字を含む -->
  <!-- 参考: docs/features/user-auth/references/password-policy.md -->

## Context Files
<!-- セッション再開時に読み込むべきファイル -->
- src/utils/validation.ts
- src/utils/validation.test.ts
```

**配置**: ストーリーディレクトリ内に配置され、Git管理される

**hooks による自動更新**:
- PreCompact/Stop hook が `**Last Updated**` を自動更新
- dev:story が初期生成時に `**Last Updated**` を追加

**学んだことの蓄積**:
- 繰り返しパターンは dev:feedback Phase 4 で検出・スキル化
- ストーリー完了時に DESIGN.md へ記録

---

### 進行中ストーリー一覧キャッシュ

**ファイルパス**: `~/.claude/sessions/in-progress-stories.tmp`

```markdown
# In-Progress Stories
**Updated**: 2026-01-22 18:30

- docs/features/user-auth/stories/implement-email-validation | Updated: 2026-01-22 16:45 | Progress: 4/6
- docs/features/payment/stories/add-stripe-integration | Updated: 2026-01-22 10:20 | Progress: 2/5
- docs/features/dashboard/stories/add-charts | Updated: 2026-01-21 15:30 | Progress: 1/3
```

**配置**: `~/.claude/sessions/` ディレクトリ（Git管理外）

**用途**:
- SessionStart hookで高速に進行中ストーリー一覧を表示
- PreCompact/Stop hookが自動生成・更新

**パフォーマンス**:
- find検索はセッション終了時のみ実行（ユーザー体感なし）
- SessionStartは単純なファイル読み込み（0.001秒以下）

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
- [ ] .gitignore に `.claude/sessions/*.tmp` 追加（ストーリー一覧キャッシュ）

### スキル統合

- [ ] `.claude/skills/dev/story/SKILL.md` に Phase 4.2 追加
- [ ] TODO.md 生成時に `**Last Updated**` を自動追加
- [ ] `.claude/skills/dev/feedback/SKILL.md` に Phase 5 追加
- [ ] PR作成後に in-progress-stories.tmp を更新

### テスト実行

- [ ] プロジェクトルートで新規セッション開始 → 進行中ストーリー一覧表示確認
- [ ] Claudeが自動的に「どのストーリーを再開しますか？」と質問確認
- [ ] /dev:story 実行 → TODO.md に `**Last Updated**` 追加確認
- [ ] ストーリー内で新規セッション開始 → TODO.md 進捗表示確認
- [ ] /compact 実行 → PreCompact hook で TODO.md + ストーリー一覧更新確認
- [ ] セッション終了 → Stop hook で TODO.md + ストーリー一覧更新確認
- [ ] 50ツール呼び出し → 戦略的コンパクション提案確認
- [ ] /dev:feedback 実行 → 完了したストーリーが一覧から削除確認
