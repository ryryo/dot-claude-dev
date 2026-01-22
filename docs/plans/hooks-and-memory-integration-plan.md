# Hooks & Memory Integration 実装計画書

> **目的**: 「Everything Claude Code」リポジトリの実装パターンを参考に、hooks基盤とセッションメモリ永続化を統合する

**作成日**: 2026-01-22
**対象**: dot-claude-dev プロジェクト
**参照**: `docs/SAMPLE/dot-claude-dev/everything-claude-code/`

---

## エグゼクティブサマリー

著者の実装から確認できた**本番稼働中**のパターン:
- **15個のhooks**（PreToolUse×5, PostToolUse×4, PreCompact×1, SessionStart×1, Stop×3）
- **セッションメモリ永続化**（.tmp ファイル、3つのライフサイクルスクリプト）
- **継続学習システム**（/learn コマンド + Stop hook 自動評価）
- **戦略的コンパクション**（ツールカウント閾値ベース提案）
- **9つの専門エージェント** + **10個のコマンド** + **8つのルール**

これらを段階的に統合し、**10ヶ月の実戦で証明された開発効率化**を実現する。

---

## 現状分析

### 既存の強み（そのまま活用）

| 領域 | 実装状況 |
|------|----------|
| ストーリー駆動開発 | ✅ dev:story → dev:developing → dev:feedback |
| TDD/E2E/TASK分類 | ✅ workflow-branching.md で判定ロジック定義 |
| Progressive Disclosure | ✅ 必要時のみリソース読み込み |
| Worktree統合 | ✅ dev:story Phase 0 で自動判定・作成 |

### 統合対象（新規実装）

| 領域 | 著者の実装 | 統合方針 |
|------|-----------|----------|
| Hooks基盤 | 15 hooks | → **Phase 1で基盤構築** |
| セッションメモリ | 3 scripts + .tmp | → **Phase 1で実装** |
| 継続学習 | /learn + evaluate-session.sh | → **Phase 2で統合** |
| 戦略的コンパクション | suggest-compact.sh | → **Phase 2で実装** |
| エージェント | 9 agents | → **Phase 3で拡張** |
| コマンド | 10 commands | → **Phase 3で追加** |

---

## Phase 1: Hooks基盤 + セッションメモリ永続化（優先度：高）

### 1.1 ディレクトリ構造構築

```bash
.claude/
├── hooks/
│   ├── hooks.json                    # hooks設定ファイル（新規）
│   ├── memory-persistence/           # セッションメモリ（新規）
│   │   ├── session-start.sh
│   │   ├── pre-compact.sh
│   │   └── session-end.sh
│   └── strategic-compact/            # 戦略的コンパクション（Phase 2）
│       └── suggest-compact.sh
├── sessions/                         # セッションログ保存先（新規）
│   ├── .gitkeep
│   └── session-template.md
└── (existing structure...)
```

### 1.2 hooks.json 実装

**ファイル**: `.claude/hooks/hooks.json`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/memory-persistence/session-start.sh"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/memory-persistence/pre-compact.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/memory-persistence/session-end.sh"
          }
        ]
      }
    ]
  }
}
```

**実装タスク**:
- [ ] hooks.json 作成
- [ ] settings.json に hooks 設定を統合（または hooks.json を参照）

### 1.3 session-start.sh 実装

**ファイル**: `.claude/hooks/memory-persistence/session-start.sh`

**機能**:
1. 最近7日間のセッションファイルを検索
2. 利用可能なコンテキストを通知
3. プロジェクトのDESIGN.mdを検出・通知
4. 学習済みスキルの存在を通知

**参考実装** (著者のコードより):

```bash
#!/bin/bash
# セッション開始時に最近のコンテキストを読み込む

SESSIONS_DIR="${CLAUDE_SESSIONS_DIR:-$HOME/.claude/sessions}"
RECENT_DAYS=7

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Session Context Loader"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 最近のセッションファイルを検索
recent_sessions=$(find "$SESSIONS_DIR" -name "*.tmp" -mtime -$RECENT_DAYS -type f 2>/dev/null | sort -r | head -5)

if [ -n "$recent_sessions" ]; then
  echo ""
  echo "📝 Recent sessions (last $RECENT_DAYS days):"
  for session in $recent_sessions; do
    filename=$(basename "$session")
    echo "  - $filename"
  done
  echo ""
  echo "💡 Use '@$filename' to load specific context"
fi

# プロジェクトのDESIGN.mdを検出
if [ -d "docs/features" ]; then
  design_files=$(find docs/features -name "DESIGN.md" -type f 2>/dev/null | head -3)
  if [ -n "$design_files" ]; then
    echo ""
    echo "📐 Project design docs available:"
    for design in $design_files; do
      echo "  - $design"
    done
  fi
fi

# 学習済みスキルの確認
if [ -d ".claude/skills/learned" ]; then
  learned_count=$(find .claude/skills/learned -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "$learned_count" -gt 0 ]; then
    echo ""
    echo "🧠 Learned skills available: $learned_count"
    echo "  Location: .claude/skills/learned/"
  fi
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
```

**実装タスク**:
- [ ] session-start.sh 作成
- [ ] 実行権限付与 (`chmod +x`)
- [ ] 環境変数 `CLAUDE_SESSIONS_DIR` のサポート
- [ ] テスト実行

### 1.4 pre-compact.sh 実装

**ファイル**: `.claude/hooks/memory-persistence/pre-compact.sh`

**機能**:
1. コンパクション発生時にタイムスタンプをログ
2. アクティブなセッションファイルに記録
3. コンパクションログファイルを作成・更新

**参考実装**:

```bash
#!/bin/bash
# コンパクション前の状態保存

SESSIONS_DIR="${CLAUDE_SESSIONS_DIR:-$HOME/.claude/sessions}"
TODAY=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%H:%M:%S)
SESSION_FILE="$SESSIONS_DIR/$TODAY-session.tmp"
COMPACTION_LOG="$SESSIONS_DIR/compaction-log.txt"

mkdir -p "$SESSIONS_DIR"

# コンパクションイベントをログ
echo "[$TODAY $TIMESTAMP] Context compaction triggered" >> "$COMPACTION_LOG"

# アクティブセッションファイルに記録
if [ -f "$SESSION_FILE" ]; then
  echo "" >> "$SESSION_FILE"
  echo "**Compaction Event:** $TIMESTAMP" >> "$SESSION_FILE"
  echo "" >> "$SESSION_FILE"
fi

echo "💾 Pre-compact state saved"
```

**実装タスク**:
- [ ] pre-compact.sh 作成
- [ ] 実行権限付与
- [ ] コンパクションログのローテーション戦略検討
- [ ] テスト実行

### 1.5 session-end.sh 実装

**ファイル**: `.claude/hooks/memory-persistence/session-end.sh`

**機能**:
1. 日次セッションファイル作成/更新
2. セッションテンプレート適用
3. タイムスタンプ記録

**参考実装**:

```bash
#!/bin/bash
# セッション終了時に状態を永続化

SESSIONS_DIR="${CLAUDE_SESSIONS_DIR:-$HOME/.claude/sessions}"
TODAY=$(date +%Y-%m-%d)
SESSION_FILE="$SESSIONS_DIR/$TODAY-session.tmp"
TIMESTAMP=$(date +%H:%M:%S)

mkdir -p "$SESSIONS_DIR"

# 新規セッションファイルの場合はテンプレートを作成
if [ ! -f "$SESSION_FILE" ]; then
  cat > "$SESSION_FILE" << 'EOF'
# Session: DATE_PLACEHOLDER

**Date:** DATE_PLACEHOLDER
**Started:** START_TIME_PLACEHOLDER
**Ended:** END_TIME_PLACEHOLDER

## Current State
<!-- What is the current state of the work? -->

## Completed
<!-- What was accomplished in this session? -->

## In Progress
<!-- What is currently being worked on? -->

## Blockers
<!-- Any issues or blockers encountered? -->

## Notes for Next Session
<!-- What to pick up next time? -->

## Context to Load
<!-- Specific files or docs to load next session -->

---
EOF

  # プレースホルダー置換
  sed -i.bak "s/DATE_PLACEHOLDER/$TODAY/g" "$SESSION_FILE"
  sed -i.bak "s/START_TIME_PLACEHOLDER/$TIMESTAMP/g" "$SESSION_FILE"
  rm -f "$SESSION_FILE.bak"
fi

# 終了時刻を更新
sed -i.bak "s/Ended: .*/Ended: $TIMESTAMP/" "$SESSION_FILE"
rm -f "$SESSION_FILE.bak"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Session persisted to: $SESSION_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

**実装タスク**:
- [ ] session-end.sh 作成
- [ ] 実行権限付与
- [ ] テンプレートのカスタマイズ検討
- [ ] テスト実行

### 1.6 session-template.md

**ファイル**: `.claude/sessions/session-template.md`

**テンプレート内容**:

```markdown
# Session: YYYY-MM-DD

**Date:** YYYY-MM-DD
**Started:** HH:MM:SS
**Ended:** HH:MM:SS

## Current State
<!-- What is the current state of the work? -->

## Completed
<!-- What was accomplished in this session? -->
-

## In Progress
<!-- What is currently being worked on? -->
-

## Blockers
<!-- Any issues or blockers encountered? -->
-

## Notes for Next Session
<!-- What to pick up next time? -->
-

## Context to Load
<!-- Specific files or docs to load next session -->
-

## Key Decisions
<!-- Important architectural or design decisions made -->
-

## Learnings
<!-- Patterns discovered, techniques that worked -->
-

---

## Session Timeline

### HH:MM - Session Start
-

### HH:MM - Activity
-

### HH:MM - Session End
-
```

**実装タスク**:
- [ ] session-template.md 作成
- [ ] .gitignore に `sessions/*.tmp` 追加（プライバシー保護）

---

## Phase 2: 継続学習 + 戦略的コンパクション（優先度：中）

### 2.1 /learn コマンド実装

**ファイル**: `.claude/commands/learn.md`

**機能**:
- セッション中に発見したパターンを即座にスキル化
- ユーザー確認後に `.claude/skills/learned/` に保存
- 次回セッションで自動読み込み

**内容**:

```markdown
---
name: learn
description: |
  現在のセッションから学習パターンを抽出し、再利用可能なスキルとして保存。
  エラー解決、デバッグ手法、ワークアラウンド、プロジェクト固有パターンなど。

  Trigger:
  学習, パターン抽出, /learn, extract pattern
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

# /learn - パターン抽出コマンド

## 概要

セッション中に発見した**非自明なパターン**をスキルとして抽出・保存する。

## 使用タイミング

| タイミング | 例 |
|-----------|-----|
| エラー解決直後 | 「このエラー、3回目だ」 |
| 新しいデバッグ手法発見 | 「このログ方法、効果的だった」 |
| ワークアラウンド発見 | 「このライブラリの制約回避方法」 |
| プロジェクト固有パターン | 「このプロジェクトでは常にこうする」 |

## ワークフロー

```
1. ユーザーに抽出内容を確認
   → AskUserQuestion でパターンの種類を選択

2. スキルファイルをドラフト
   → パターンの詳細、適用条件、コード例を含む

3. 確認後に保存
   → .claude/skills/learned/{pattern-slug}.md

4. 次回セッションで自動読み込み
   → SessionStart hook が learned/ を検出
```

## 抽出パターンの種類

| 種類 | 説明 | 保存形式 |
|------|------|----------|
| **エラー解決** | 特定エラーの解決方法 | `error-{error-slug}.md` |
| **デバッグ手法** | 効果的なデバッグアプローチ | `debug-{technique-slug}.md` |
| **ワークアラウンド** | ライブラリ/ツールの制約回避 | `workaround-{library-slug}.md` |
| **プロジェクト固有** | このプロジェクト特有のパターン | `project-{pattern-slug}.md` |

## 実装

### Step 1: パターン種類の確認

```javascript
AskUserQuestion({
  questions: [{
    question: "どの種類のパターンを抽出しますか？",
    header: "Pattern Type",
    options: [
      { label: "エラー解決", description: "特定エラーの解決方法を記録" },
      { label: "デバッグ手法", description: "効果的なデバッグアプローチを記録" },
      { label: "ワークアラウンド", description: "ライブラリの制約回避方法を記録" },
      { label: "プロジェクト固有", description: "プロジェクト特有のパターンを記録" }
    ],
    multiSelect: false
  }]
})
```

### Step 2: パターンの詳細入力

```javascript
AskUserQuestion({
  questions: [{
    question: "パターンのタイトルを入力してください",
    header: "Title",
    options: [
      { label: "カスタム入力", description: "自由入力" }
    ],
    multiSelect: false
  }]
})
```

### Step 3: スキルファイル生成

```markdown
---
name: learned-{slug}
description: {pattern description}
trigger: {when to apply this pattern}
---

# {Pattern Title}

## 問題

{What problem does this solve?}

## 解決策

{How to solve it?}

## コード例

\`\`\`{language}
{code example}
\`\`\`

## 適用条件

- {When to use this pattern}
- {When NOT to use this pattern}

## 関連リソース

- {Related docs, files, or patterns}
```

### Step 4: 保存確認

```javascript
Write({
  file_path: ".claude/skills/learned/{slug}.md",
  content: {skill_content}
})
```

## 完了条件

- [ ] パターンが `.claude/skills/learned/` に保存された
- [ ] スキルファイルが正しい形式
- [ ] 次回セッションで読み込み可能

## 関連

- **SessionStart hook**: learned/ の存在を通知
- **evaluate-session.sh**: セッション終了時に自動抽出提案
```

**実装タスク**:
- [ ] learn.md コマンド作成
- [ ] スキルテンプレート定義
- [ ] .claude/skills/learned/ ディレクトリ作成
- [ ] テスト実行

### 2.2 evaluate-session.sh (Stop Hook)

**ファイル**: `.claude/hooks/continuous-learning/evaluate-session.sh`

**機能**:
1. セッション終了時にメッセージ数をチェック
2. 閾値（最低10メッセージ）を超えていれば評価を提案
3. Claudeにパターン抽出を促す

**参考実装**:

```bash
#!/bin/bash
# セッション終了時にパターン抽出を評価

CONFIG_FILE=".claude/hooks/continuous-learning/config.json"
MIN_SESSION_LENGTH=10  # デフォルト

# config.json があれば読み込み
if [ -f "$CONFIG_FILE" ]; then
  MIN_SESSION_LENGTH=$(jq -r '.min_session_length // 10' "$CONFIG_FILE")
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Evaluating session for learnable patterns..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Please analyze this session for extractable patterns:"
echo ""
echo "  - Error resolutions (solved 2+ times)"
echo "  - Debugging techniques that worked well"
echo "  - Workarounds for library limitations"
echo "  - Project-specific patterns"
echo ""
echo "If patterns found, suggest using /learn command to save them."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

**実装タスク**:
- [ ] evaluate-session.sh 作成
- [ ] config.json 作成
- [ ] hooks.json に Stop hook として追加
- [ ] テスト実行

### 2.3 config.json (継続学習設定)

**ファイル**: `.claude/hooks/continuous-learning/config.json`

```json
{
  "min_session_length": 10,
  "extraction_threshold": "medium",
  "auto_approve": false,
  "learned_skills_path": ".claude/skills/learned/",
  "patterns_to_detect": [
    "error_resolution",
    "user_corrections",
    "workarounds",
    "debugging_techniques",
    "project_specific"
  ],
  "ignore_patterns": [
    "simple_typos",
    "one_time_fixes",
    "external_api_issues"
  ]
}
```

**実装タスク**:
- [ ] config.json 作成
- [ ] ドキュメント作成

### 2.4 suggest-compact.sh (戦略的コンパクション)

**ファイル**: `.claude/hooks/strategic-compact/suggest-compact.sh`

**機能**:
1. ツール呼び出し回数をカウント
2. 閾値（デフォルト50回）で提案
3. 以降25回ごとに再提案

**参考実装**:

```bash
#!/bin/bash
# 戦略的コンパクション提案 (PreToolUse hook)

COUNTER_FILE="/tmp/claude-tool-count-$$"
THRESHOLD=${COMPACT_THRESHOLD:-50}
REMINDER_INTERVAL=25

# カウント管理
if [ -f "$COUNTER_FILE" ]; then
  count=$(cat "$COUNTER_FILE")
  count=$((count + 1))
  echo "$count" > "$COUNTER_FILE"
else
  echo "1" > "$COUNTER_FILE"
  count=1
fi

# 閾値到達で提案
if [ "$count" -eq "$THRESHOLD" ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "💡 Strategic Compaction Suggestion" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "" >&2
  echo "$THRESHOLD tool calls reached." >&2
  echo "" >&2
  echo "Consider /compact if transitioning between phases:" >&2
  echo "  ✓ Exploration → Implementation" >&2
  echo "  ✓ RED → GREEN (TDD)" >&2
  echo "  ✓ Task completion → New task" >&2
  echo "" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
elif [ $(( (count - THRESHOLD) % REMINDER_INTERVAL )) -eq 0 ] && [ "$count" -gt "$THRESHOLD" ]; then
  echo "💡 [$count tool calls] Consider /compact if changing context" >&2
fi
```

**実装タスク**:
- [ ] suggest-compact.sh 作成
- [ ] 環境変数 `COMPACT_THRESHOLD` サポート
- [ ] hooks.json に PreToolUse hook として追加
- [ ] テスト実行

---

## Phase 3: エージェント + コマンド拡張（優先度：低）

### 3.1 専門エージェント追加

著者の9つのエージェントを参考に、必要に応じて追加:

| エージェント | 用途 | モデル | 優先度 |
|-------------|------|--------|--------|
| **planner** | 機能計画、アーキテクチャレビュー | Opus | 高 |
| **code-reviewer** | 品質、セキュリティレビュー | Opus | 高 |
| **tdd-guide** | TDD実施のガイド | Opus | 中（既存あり） |
| **security-reviewer** | 脆弱性分析 | Opus | 中 |
| **build-error-resolver** | ビルドエラー解決 | Sonnet | 中 |
| **refactor-cleaner** | デッドコード削除 | Sonnet | 低 |
| **doc-updater** | ドキュメント同期 | Haiku | 低 |

**実装判断基準**:
- 既存のサブエージェント（Task tool）で対応可能か？
- 頻度の高いタスクか？
- 専用エージェントで品質向上するか？

### 3.2 コマンド追加候補

著者の10コマンドから優先度の高いもの:

| コマンド | 用途 | Phase |
|---------|------|-------|
| **/learn** | パターン抽出 | Phase 2 ✅ |
| **/code-review** | コードレビュー | Phase 3 |
| **/refactor-clean** | デッドコード削除 | Phase 3 |
| **/update-codemaps** | コードマップ更新 | Phase 3 |

---

## 実装ロードマップ

### Phase 1（1-2日） - 基盤構築

**目標**: セッションメモリ永続化の実現

| タスク | 成果物 | 所要時間 |
|--------|--------|---------|
| ディレクトリ構造作成 | `.claude/hooks/`, `.claude/sessions/` | 10分 |
| hooks.json 作成 | hooks設定ファイル | 20分 |
| session-start.sh 実装 | SessionStart hook | 30分 |
| pre-compact.sh 実装 | PreCompact hook | 20分 |
| session-end.sh 実装 | Stop hook | 30分 |
| session-template.md 作成 | テンプレート | 15分 |
| .gitignore 更新 | `sessions/*.tmp` 除外 | 5分 |
| **テスト実行** | 全hooks動作確認 | 30分 |

**チェックポイント**:
- [ ] SessionStart hook でセッション一覧表示
- [ ] Stop hook でセッションファイル作成
- [ ] PreCompact hook でログ記録

### Phase 2（2-3日） - 継続学習 + 戦略的コンパクション

**目標**: 自動学習とコンテキスト最適化

| タスク | 成果物 | 所要時間 |
|--------|--------|---------|
| /learn コマンド作成 | `.claude/commands/learn.md` | 1時間 |
| evaluate-session.sh 実装 | Stop hook 追加 | 30分 |
| config.json 作成 | 継続学習設定 | 15分 |
| suggest-compact.sh 実装 | PreToolUse hook 追加 | 30分 |
| .claude/skills/learned/ 作成 | 学習スキル保存先 | 5分 |
| **テスト実行** | パターン抽出フロー確認 | 1時間 |

**チェックポイント**:
- [ ] /learn でスキル保存成功
- [ ] Stop hook でパターン抽出提案
- [ ] 50ツール呼び出しでコンパクト提案

### Phase 3（継続的） - エージェント + コマンド拡張

**目標**: 専門化と効率化

| タスク | 成果物 | タイミング |
|--------|--------|----------|
| code-reviewer エージェント | レビュー自動化 | 必要時 |
| refactor-cleaner エージェント | デッドコード削除 | 必要時 |
| /code-review コマンド | レビュー起動 | 必要時 |
| /refactor-clean コマンド | クリーンアップ起動 | 必要時 |

---

## 統合後の開発フロー

```
┌────────────────────────────────────────────────────────────┐
│                     セッション開始                           │
└───────────────────┬────────────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  SessionStart Hook   │
         │  - 前回セッション通知  │
         │  - DESIGN.md 表示    │
         │  - 学習スキル通知     │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   開発作業 (TDD/E2E) │
         │  - dev:story         │
         │  - dev:developing    │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  50ツール呼び出し達成 │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ suggest-compact.sh   │ (PreToolUse)
         │ → /compact 提案      │
         └──────────┬───────────┘
                    │
              ユーザー判断
                    │
         ┌──────────┴───────────┐
         │                      │
        YES                    NO
         │                      │
         ▼                      ▼
┌────────────────┐      ┌──────────────┐
│ PreCompact Hook│      │  作業継続    │
│ - 状態保存      │      └──────────────┘
└────────┬───────┘
         │
         ▼
┌────────────────┐
│  /compact実行  │
└────────┬───────┘
         │
         ▼
┌────────────────┐
│  作業継続      │
└────────┬───────┘
         │
         ▼
┌────────────────────┐
│  パターン発見      │
│  → /learn 実行     │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ .claude/skills/    │
│ learned/ に保存    │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  セッション終了    │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Stop Hook (3つ)   │
│  1. session-end.sh │
│  2. evaluate-      │
│     session.sh     │
│  3. (その他)       │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ セッションファイル  │
│ YYYY-MM-DD-        │
│ session.tmp 作成   │
└────────────────────┘
```

---

## 成功指標

### Phase 1 完了時

- [ ] 3つのhooksが正常動作
- [ ] セッションファイルが自動生成
- [ ] 次回セッション開始時にコンテキスト通知

### Phase 2 完了時

- [ ] /learn でパターン保存成功
- [ ] Stop hook でパターン抽出提案
- [ ] 戦略的コンパクション提案が機能

### Phase 3 完了時

- [ ] 専門エージェントが稼働
- [ ] コマンドが利用可能
- [ ] 開発効率が向上

---

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| hooks の実行失敗 | セッションメモリ喪失 | エラーハンドリング強化、ログ出力 |
| .tmp ファイルの肥大化 | ディスク容量圧迫 | 30日以上のファイル自動削除 |
| 学習スキルの重複 | スキル管理の複雑化 | slug命名規則の統一、重複チェック |
| コンパクション提案の頻度 | ユーザー体験悪化 | 閾値の調整、設定ファイルでカスタマイズ |

---

## 次のステップ

1. **Phase 1 実装開始**: hooks基盤とセッションメモリ
2. **動作確認**: 実際のセッションで検証
3. **フィードバック収集**: 使用感の評価
4. **Phase 2 移行判断**: Phase 1 が安定したら継続学習実装

---

## 参照

- **著者リポジトリ**: `docs/SAMPLE/dot-claude-dev/everything-claude-code/`
- **Longform Guide**: `docs/SAMPLE/dot-claude-dev/The Longform Guide to Everything Claude Code.md`
- **初期分析**: `docs/analysis/longform-guide-integration-analysis.md`
