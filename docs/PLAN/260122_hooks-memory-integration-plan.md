# Hooks & Memory Integration 実装計画書（TODO.md拡張版）

> **目的**: セッションメモリを**既存TODO.md拡張**で実装し、最小コストで効率化

**作成日**: 2026-01-22
**更新日**: 2026-01-23
**対象**: dot-claude-dev プロジェクト

---

## エグゼクティブサマリー

**目的**: セッション間でストーリー進捗を自動的に引き継ぎ、作業再開を高速化

**実現内容**:
- ✅ セッション再開時に前回の続きから作業可能（Last Updated表示）
- ✅ プロジェクトルートから進行中ストーリーを選択して再開
- ✅ 長時間セッションでのコンテキスト枯渇を防止（50回で提案）
- ✅ ストーリー完了時に自動的に進行中一覧から削除

**実装方針**:
- 既存TODO.mdにメタデータを追加（新規ファイル不要）
- セッション開始時は高速（ファイル検索なし）
- 既存ワークフロー（dev:story/dev:feedback）に統合

**実装時間**: 1時間5分

---

## 現状分析

### 既存の強み（そのまま活用）

| 領域 | 実装状況 |
|------|----------|
| ストーリー駆動開発 | ✅ dev:story → dev:developing → dev:feedback |
| TODO.md | ✅ タスク管理、進捗追跡 |
| DESIGN.md | ✅ 設計記録（dev:feedback） |

### 統合対象（最小構成）

| 機能 | 実装内容 | 実装時間 |
|------|---------|---------|
| **TODO.md拡張** | Last Updated + メタデータ追加 | 30分 |
| **戦略的コンパクション** | suggest-compact.sh | 30分 |
| **スキル統合** | dev:story + dev:feedback | 5分 |

**合計**: 1時間5分で完了

---

## TODO.md 拡張仕様

### 拡張前（現在）

```markdown
# TODO: implement-email-validation

- [ ] [TDD][RED] validateEmail のテスト作成
- [ ] [TDD][GREEN] validateEmail の実装
- [ ] [TDD][REFACTOR] リファクタリング
```

### 拡張後

```markdown
# TODO: implement-email-validation

**Last Updated**: 2026-01-22 16:45

## Blockers
- パスワードポリシー仕様確認待ち

## Tasks

- [x] [TDD][RED] validateEmail のテスト作成
- [x] [TDD][GREEN] validateEmail の実装
- [ ] [TDD][RED] validatePassword のテスト作成
  <!-- 注: 最低8文字、大文字小文字数字を含む -->
  <!-- 参考: docs/features/user-auth/references/password-policy.md -->

## Context Files
<!-- セッション再開時に読み込むべきファイル -->
- src/utils/validation.ts
- src/utils/validation.test.ts
```

### セクション定義

| セクション | 必須 | 用途 |
|-----------|------|------|
| **Last Updated** | ✅ | hooks が自動更新 |
| **## Blockers** | ⚪ | 作業を止めている問題 |
| **## Tasks** | ✅ | タスクリスト（既存） |
| **## Context Files** | ⚪ | セッション再開時に読むファイル |

---

## Hooks 実装

### 実装するHooks（4つ）+ dev:feedback統合

| Hook/スキル | スクリプト | 機能 |
|------|-----------|------|
| **SessionStart** | `session-start.sh` | TODO.md または保存済みストーリー一覧を表示 |
| **PreCompact** | `pre-compact.sh` | TODO.md の Last Updated を更新 + ストーリー一覧保存 |
| **Stop** | `session-end.sh` | TODO.md の Last Updated を更新 + ストーリー一覧保存 |
| **PreToolUse** | `suggest-compact.sh` | 50ツール呼び出しで compact 提案 |
| **dev:feedback** | Phase 5 追加 | ストーリー完了時に in-progress-stories.tmp を更新 |

---

## Phase 1: TODO.md拡張 + SessionStart hook

### 1.1 ディレクトリ構造

```bash
.claude/
├── hooks/
│   ├── hooks.json
│   ├── memory-persistence/
│   │   ├── session-start.sh
│   │   ├── pre-compact.sh
│   │   └── session-end.sh
│   └── strategic-compact/
│       └── suggest-compact.sh
└── sessions/
    └── in-progress-stories.tmp  # 進行中ストーリー一覧キャッシュ
```

**注**: `~/.claude/sessions/` にストーリー一覧キャッシュを保存（セッション開始時の高速化）

### 1.2 session-start.sh (SessionStart Hook)

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
- **その他**: 何もしない

**Claudeの自動応答**:
- SessionStart hookでストーリー一覧が表示された場合、Claudeは自動的にAskUserQuestionでストーリー選択を促す

### 1.3 pre-compact.sh (PreCompact Hook)

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

### 1.4 session-end.sh (Stop Hook)

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

### 1.5 hooks.json

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
        "description": "Load TODO.md metadata"
      }
    ],
    "PreCompact": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "~/.claude/hooks/memory-persistence/pre-compact.sh"
        }],
        "description": "Update TODO.md timestamp"
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "~/.claude/hooks/memory-persistence/session-end.sh"
        }],
        "description": "Update TODO.md timestamp on exit"
      }
    ]
  }
}
```

### 1.6 dev:story 統合（Phase 4.2 追加）

**ファイル**: `.claude/skills/dev/story/SKILL.md`

**Phase 4.2**: TODO.md に Last Updated メタデータを追加

```javascript
// TODO.md 生成時に Last Updated を追加
const todoContent = `# TODO: ${storySlug}

**Last Updated**: ${new Date().toISOString().slice(0, 16).replace('T', ' ')}

## Tasks

${tasks.map(t => `- [ ] ${t}`).join('\n')}
`;
```

**実装タスク**:
- [ ] dev:story SKILL.md の Phase 4 で TODO.md に `**Last Updated**` を追加
- [ ] 既存のタスクリスト生成ロジックは変更なし

### 1.7 dev:feedback 統合（Phase 5 追加）

**ファイル**: `.claude/skills/dev/feedback/SKILL.md`

**Phase 5**: ストーリー完了時に in-progress-stories.tmp を更新

**目的**: ストーリー完了直後に進行中ストーリー一覧から削除し、確実に反映

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

**実装タスク**:
- [ ] dev:feedback SKILL.md の Phase 5 に in-progress-stories.tmp 更新処理を追加
- [ ] PR作成・Worktreeクリーンアップの後に実行

**メリット**:
- ✅ ストーリー完了直後に一覧から削除（PreCompact/Stopを待たない）
- ✅ 次回SessionStartで完了済みストーリーが表示されない

---

## Phase 2: 戦略的コンパクション

### 2.1 suggest-compact.sh (PreToolUse Hook)

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

### 2.2 hooks.json 更新

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "~/.claude/hooks/strategic-compact/suggest-compact.sh"
        }],
        "description": "Suggest /compact at logical checkpoints"
      }
    ]
  }
}
```

---

## 実装ロードマップ

### Phase 1（30分） - TODO.md拡張 + hooks基盤

| タスク | 成果物 | 所要時間 |
|--------|--------|---------|
| ディレクトリ作成 | `.claude/hooks/memory-persistence/` | 5分 |
| session-start.sh 実装 | SessionStart hook | 10分 |
| pre-compact.sh 実装 | PreCompact hook | 5分 |
| session-end.sh 実装 | Stop hook | 5分 |
| hooks.json 作成 | hooks設定 | 5分 |

**チェックポイント**:
- [ ] ストーリー内で SessionStart hook が TODO.md を検出
- [ ] Last Updated が表示される
- [ ] Stop/PreCompact hook で Last Updated が更新される

### Phase 2（35分） - 戦略的コンパクション + スキル統合

| タスク | 成果物 | 所要時間 |
|--------|--------|---------|
| ディレクトリ作成 | `.claude/hooks/strategic-compact/` | 5分 |
| suggest-compact.sh 実装 | PreToolUse hook | 10分 |
| hooks.json 更新 | PreToolUse hook追加 | 5分 |
| dev:story 統合 | Phase 4.2 Last Updated追加 | 10分 |
| dev:feedback 統合 | Phase 5 ストーリー一覧更新追加 | 5分 |

**チェックポイント**:
- [ ] 50ツール呼び出し時に compact 提案が表示される
- [ ] dev:story で TODO.md に Last Updated が自動追加される
- [ ] dev:feedback で in-progress-stories.tmp が更新される

---

## 統合後の開発フロー

### ストーリー内での開発

```
/dev:story 実行
    ↓
TODO.md 生成（Last Updated 付き）
    ↓
開発作業開始
    ↓
[セッション終了]
    ↓
Stop Hook → TODO.md の Last Updated 更新 + ストーリー一覧保存
    ↓
[次回セッション開始（ストーリー内）]
    ↓
SessionStart Hook → TODO.md の Last Updated を読んで通知
```

### プロジェクトルートからの開始

```
[セッション開始（プロジェクトルート）]
    ↓
SessionStart Hook → 保存済みストーリー一覧を表示
    ↓
Claude が AskUserQuestion で「どのストーリーを再開しますか？」
    ↓
ユーザーが選択 → 選択したストーリーディレクトリに移動
    ↓
開発作業開始
    ↓
[セッション終了]
    ↓
Stop Hook → TODO.md + ストーリー一覧を更新保存
```

### ストーリー完了時

```
開発作業完了
    ↓
/dev:feedback 実行
    ↓
Phase 5: in-progress-stories.tmp を更新（完了したストーリーを削除）
    ↓
PR作成・Worktreeクリーンアップ
```

**ポイント**:
- ✅ SessionStartは常に高速（find検索なし）
- ✅ find検索はセッション終了時のみ（ユーザー体感なし）
- ✅ ストーリー完了時に即座に一覧から削除（dev:feedback Phase 5）
- ✅ プロジェクトルートからストーリー選択が対話的に可能

---

## SESSION.md方式との比較

| 項目 | SESSION.md方式 | TODO.md拡張方式 |
|------|---------------|----------------|
| **ファイル数** | TODO.md + SESSION.md | TODO.mdのみ |
| **実装時間** | 1-2時間 | **1時間** |
| **メンテナンス** | 2ファイルの同期必要 | 1ファイルのみ |
| **Session History** | あり | **不要**（git履歴で代替） |
| **グローバルセッション** | .tmpファイル管理 | **キャッシュのみ**（in-progress-stories.tmp） |
| **可読性** | 分散 | **集中** |

---

## 完了条件

### Phase 1 完了時

- [ ] ストーリー内で TODO.md が検出される
- [ ] SessionStart hook で Last Updated が通知される
- [ ] Stop/PreCompact hook で Last Updated が更新される
- [ ] Blockers セクションがあれば警告される

### Phase 2 完了時

- [ ] 50ツール呼び出し時に compact 提案が表示される
- [ ] dev:story で TODO.md に Last Updated が自動追加される
- [ ] dev:feedback で in-progress-stories.tmp が更新される
- [ ] プロジェクトルートで進行中ストーリー一覧が表示される
- [ ] Claudeが自動的にストーリー選択を促す

---

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| TODO.mdのフォーマット崩れ | hooks が動作しない | sed の正規表現を厳密に |
| Last Updated の重複追加 | 見た目が悪い | 存在チェックを必ず行う |
| ストーリー外での誤動作 | 不要な警告 | TODO.md 存在チェックで回避 |

---

## 次のステップ

1. **Phase 1 実装開始**: TODO.md拡張 + hooks基盤（30分）
2. **動作確認**: 実際のストーリーで検証
3. **Phase 2 実装**: 戦略的コンパクション + dev:story統合（30分）
4. **フィードバック収集**: 使用感の評価と改善

---

## 参照

- **著者リポジトリ**: `docs/SAMPLE/dot-claude-dev/everything-claude-code/`
- **既存 TODO.md**: `.claude/skills/dev/story/SKILL.md` Phase 4
