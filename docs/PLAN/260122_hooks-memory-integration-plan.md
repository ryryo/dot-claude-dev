# Hooks & Memory Integration 実装計画書（ストーリー統合版）

> **目的**: 「Everything Claude Code」の実装パターンを**ストーリー駆動開発フレームワーク**に統合

**作成日**: 2026-01-22
**更新日**: 2026-01-23
**対象**: dot-claude-dev プロジェクト
**参照**: `docs/SAMPLE/dot-claude-dev/everything-claude-code/`

---

## エグゼクティブサマリー

著者の実装パターンを、**現在のストーリー駆動開発フレームワークに最適化**して統合:

- ✅ **ストーリー単位のセッションメモリ**: `SESSION.md` を TODO.md, DESIGN.md と同じ場所で管理
- ✅ **継続学習システム**: 繰り返しパターンを自動抽出・スキル化
- ✅ **戦略的コンパクション**: 論理的なタイミングでのcompact提案

**コア3機能の実装で、10ヶ月の実戦で証明された開発効率化を実現する。**

---

## 現状分析

### 既存の強み（そのまま活用）

| 領域 | 実装状況 |
|------|----------|
| ストーリー駆動開発 | ✅ dev:story → dev:developing → dev:feedback |
| TDD/E2E/TASK分類 | ✅ workflow-branching.md で判定ロジック定義 |
| Progressive Disclosure | ✅ 必要時のみリソース読み込み |
| Worktree統合 | ✅ dev:story Phase 0 で自動判定・作成 |

### 統合対象（新規実装 - コア3機能のみ）

| 機能 | 実装内容 | 実装時間 |
|------|---------|---------|
| **セッションメモリ永続化** | ストーリー単位のSESSION.md | 1-2時間 |
| **継続学習システム** | /learn + evaluate-session.sh | 2-3時間 |
| **戦略的コンパクション** | suggest-compact.sh | 30分 |

**合計**: 4-6時間で完了

---

## セッションメモリの設計（ストーリー統合）

### 基本方針

```
主: docs/features/{feature-slug}/stories/{story-slug}/SESSION.md
   → ストーリー固有の状態を記録（Git管理）

補: .claude/sessions/YYYY-MM-DD-global.tmp
   → ストーリー外の作業のみ（緊急バグ修正等）
```

### ストーリーディレクトリ構造

```
docs/features/{feature-slug}/stories/{story-slug}/
├── story-analysis.json    # ストーリー分析（dev:story Phase 1）
├── task-list.json         # タスクリスト（dev:story Phase 2）
├── TODO.md                # 進捗管理（dev:story Phase 3）
├── SESSION.md             # セッション記録（新規 - dev:story Phase 4）
└── DESIGN.md              # 設計記録（dev:feedback）
```

### SESSION.md のフォーマット

```markdown
# Session Log: {story-slug}

**Feature**: {feature-slug}
**Story**: {story-slug}
**Started**: 2026-01-22
**Last Updated**: 2026-01-23 15:30

---

## Current State

ストーリーの現在の状態を記述。

### Completed Tasks
- [x] [TDD][RED] validateEmail のテスト作成
- [x] [TDD][GREEN] validateEmail の実装
- [x] [TDD][REFACTOR] リファクタリング完了

### In Progress
- [ ] [TDD][RED] validatePassword のテスト作成

### Blockers
- バリデーションライブラリの選定が未定
- パスワードポリシーの仕様確認待ち

### Notes for Next Session
- validatePassword: 最低8文字、大文字小文字数字を含む
- 参考: docs/features/user-auth/references/password-policy.md
- Zod でのバリデーション実装を検討

### Context to Load
\`\`\`
src/utils/validation.ts
src/utils/validation.test.ts
\`\`\`

---

## Session History

### 2026-01-23 15:30 - Session 3
- validateEmail の REFACTOR 完了
- ヘルパー関数 isValidDomain() を抽出
- 全テスト通過

### 2026-01-22 18:00 - Session 2
- validateEmail の GREEN フェーズ
- 正規表現パターンを実装
- エッジケース対応

### 2026-01-22 10:00 - Session 1 (Story Start)
- dev:story でストーリー開始
- TODO.md, SESSION.md 作成
```

---

## Phase 1: Hooks基盤 + セッションメモリ永続化

### 1.1 ディレクトリ構造構築

```bash
.claude/
├── hooks/
│   ├── hooks.json                    # hooks設定ファイル（新規）
│   ├── memory-persistence/           # セッションメモリ（新規）
│   │   ├── session-start.sh         # ストーリー検出 + SESSION.md読み込み
│   │   ├── pre-compact.sh           # コンパクション前の記録
│   │   └── session-end.sh           # SESSION.md更新
│   └── continuous-learning/          # Phase 2で実装
│       ├── evaluate-session.sh
│       └── config.json
├── sessions/                         # グローバルセッション（補助）
│   └── YYYY-MM-DD-global.tmp
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
        ],
        "description": "Load story session or global session"
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
        ],
        "description": "Save state before compaction"
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
        ],
        "description": "Update SESSION.md or global session"
      }
    ]
  }
}
```

**実装タスク**:
- [ ] hooks.json 作成
- [ ] settings.json に hooks 設定を統合（または hooks.json を参照）

### 1.3 session-start.sh 実装（ストーリー検出版）

**ファイル**: `.claude/hooks/memory-persistence/session-start.sh`

**機能**:
1. 現在のディレクトリから TODO.md を検出（ストーリー内か判定）
2. SESSION.md があれば読み込んで通知
3. なければグローバルセッションを確認

**実装**:

```bash
#!/bin/bash
# SessionStart Hook - Load story session or global session

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Session Context Loader"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ストーリーディレクトリの検出（TODO.md の存在確認）
if [ -f "TODO.md" ] && [ -f "SESSION.md" ]; then
  # ストーリー内のセッション
  FEATURE=$(grep -m1 "^# " SESSION.md | sed 's/# Session Log: //' || echo "unknown")
  LAST_UPDATED=$(grep "Last Updated" SESSION.md | sed 's/\*\*Last Updated:\*\* //' || echo "unknown")

  echo "📝 Story Session Found"
  echo "  Story: $FEATURE"
  echo "  Last Updated: $LAST_UPDATED"
  echo "  File: SESSION.md"
  echo ""
  echo "💡 Load context with: @SESSION.md"

  # Completed Tasks をカウント
  COMPLETED=$(grep -c "^- \[x\]" SESSION.md 2>/dev/null || echo "0")
  IN_PROGRESS=$(grep -c "^- \[ \]" SESSION.md 2>/dev/null || echo "0")

  echo ""
  echo "📊 Progress:"
  echo "  ✓ Completed: $COMPLETED tasks"
  echo "  ⧗ In Progress: $IN_PROGRESS tasks"

elif [ -f "TODO.md" ] && [ ! -f "SESSION.md" ]; then
  # ストーリー内だがSESSION.mdがない（新規ストーリー）
  echo "🆕 New Story Detected (SESSION.md not found)"
  echo "  SESSION.md will be created when dev:story completes"

else
  # ストーリー外 - グローバルセッション確認
  SESSIONS_DIR=".claude/sessions"
  TODAY=$(date '+%Y-%m-%d')
  GLOBAL_SESSION="$SESSIONS_DIR/$TODAY-global.tmp"

  if [ -f "$GLOBAL_SESSION" ]; then
    echo "🌐 Global Session Found"
    echo "  File: $GLOBAL_SESSION"
    echo ""
    echo "💡 Load context with: @$GLOBAL_SESSION"
  else
    echo "ℹ️  No active session found"
    echo ""
    echo "To start a story-driven workflow:"
    echo "  Use /dev:story command"
  fi
fi

# 学習済みスキルの確認
LEARNED_DIR=".claude/skills/learned"
if [ -d "$LEARNED_DIR" ]; then
  learned_count=$(find "$LEARNED_DIR" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "$learned_count" -gt 0 ]; then
    echo ""
    echo "🧠 Learned Skills Available: $learned_count"
    echo "  Location: $LEARNED_DIR/"
  fi
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
```

**実装タスク**:
- [ ] session-start.sh 作成
- [ ] 実行権限付与 (`chmod +x`)
- [ ] ストーリー検出ロジックのテスト
- [ ] グローバルセッションのフォールバック確認

### 1.4 pre-compact.sh 実装（ストーリー対応版）

**ファイル**: `.claude/hooks/memory-persistence/pre-compact.sh`

**機能**:
1. コンパクション発生時にタイムスタンプをログ
2. SESSION.md または global.tmp に記録

**実装**:

```bash
#!/bin/bash
# PreCompact Hook - Save state before compaction

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# ストーリー内ならSESSION.mdに記録
if [ -f "SESSION.md" ]; then
  echo "" >> SESSION.md
  echo "**Compaction Event:** $TIMESTAMP" >> SESSION.md
  echo "" >> SESSION.md
  echo "[PreCompact] State saved to SESSION.md" >&2

# ストーリー外ならグローバルセッションに記録
else
  SESSIONS_DIR=".claude/sessions"
  TODAY=$(date '+%Y-%m-%d')
  GLOBAL_SESSION="$SESSIONS_DIR/$TODAY-global.tmp"
  COMPACTION_LOG="$SESSIONS_DIR/compaction-log.txt"

  mkdir -p "$SESSIONS_DIR"

  echo "[$TIMESTAMP] Context compaction triggered" >> "$COMPACTION_LOG"

  if [ -f "$GLOBAL_SESSION" ]; then
    echo "" >> "$GLOBAL_SESSION"
    echo "**Compaction Event:** $TIMESTAMP" >> "$GLOBAL_SESSION"
    echo "" >> "$GLOBAL_SESSION"
  fi

  echo "[PreCompact] State saved to global session" >&2
fi
```

**実装タスク**:
- [ ] pre-compact.sh 作成
- [ ] 実行権限付与
- [ ] コンパクションログのテスト

### 1.5 session-end.sh 実装（ストーリー対応版）

**ファイル**: `.claude/hooks/memory-persistence/session-end.sh`

**機能**:
1. ストーリー内なら SESSION.md を更新
2. ストーリー外ならグローバルセッションを更新

**実装**:

```bash
#!/bin/bash
# Stop Hook - Update SESSION.md or global session

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

# ストーリー内ならSESSION.mdを更新
if [ -f "SESSION.md" ]; then
  # Last Updated を更新（macOS対応）
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/\*\*Last Updated:\*\*.*/\*\*Last Updated:\*\* $TIMESTAMP/" SESSION.md
  else
    sed -i "s/\*\*Last Updated:\*\*.*/\*\*Last Updated:\*\* $TIMESTAMP/" SESSION.md
  fi

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "📝 Story session updated: SESSION.md" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2

# ストーリー外ならグローバルセッション
else
  SESSIONS_DIR=".claude/sessions"
  TODAY=$(date '+%Y-%m-%d')
  GLOBAL_SESSION="$SESSIONS_DIR/$TODAY-global.tmp"

  mkdir -p "$SESSIONS_DIR"

  # 新規作成の場合はテンプレート適用
  if [ ! -f "$GLOBAL_SESSION" ]; then
    cat > "$GLOBAL_SESSION" << EOF
# Global Session: $TODAY

**Date:** $TODAY
**Started:** $TIMESTAMP
**Last Updated:** $TIMESTAMP

---

## Activities

[Non-story work goes here]

### Completed
- [ ]

### Notes
-

EOF
  else
    # 既存の場合は Last Updated のみ更新
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "s/\*\*Last Updated:\*\*.*/\*\*Last Updated:\*\* $TIMESTAMP/" "$GLOBAL_SESSION"
    else
      sed -i "s/\*\*Last Updated:\*\*.*/\*\*Last Updated:\*\* $TIMESTAMP/" "$GLOBAL_SESSION"
    fi
  fi

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "📝 Global session updated: $GLOBAL_SESSION" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
fi
```

**実装タスク**:
- [ ] session-end.sh 作成
- [ ] 実行権限付与
- [ ] macOS/Linux 両対応確認
- [ ] テスト実行

---

## Phase 1.5: dev:story との統合

### dev:story の Phase 4 を拡張

**ファイル**: `.claude/skills/dev/story/SKILL.md`

**Phase 4 に SESSION.md 作成を追加**:

```markdown
## Phase 4: ユーザー確認 + SESSION.md 作成

### 4.1 TODO.md 確認

（既存のAskUserQuestion）

### 4.2 SESSION.md 作成（新規）

**⚠️ 必ずWriteツールで作成すること**

\`\`\`javascript
Write({
  file_path: "docs/features/{feature-slug}/stories/{story-slug}/SESSION.md",
  content: `# Session Log: ${storySlug}

**Feature**: ${featureSlug}
**Story**: ${storySlug}
**Started**: ${TODAY}
**Last Updated**: ${TODAY} ${TIME}

---

## Current State

ストーリー実装開始。TODO.md を参照して進める。

### Completed Tasks
- [ ]

### In Progress
- [ ] ${TODO.mdの最初のタスク}

### Blockers
なし

### Notes for Next Session
- TODO.md を参照して実装を進める
- ${acceptanceCriteriaから抽出した重要ポイント}

### Context to Load
\`\`\`
（該当するファイルパス）
\`\`\`

---

## Session History

### ${TODAY} ${TIME} - Session 1 (Story Start)
- dev:story でストーリー開始
- story-analysis.json, task-list.json, TODO.md, SESSION.md 作成
- 次: ${最初のタスク}
\`
})
\`\`\`

### 4.3 完了条件の更新

**旧**:
- [ ] story-analysis.json 作成
- [ ] task-list.json 作成
- [ ] TODO.md 作成

**新**:
- [ ] story-analysis.json 作成
- [ ] task-list.json 作成
- [ ] TODO.md 作成
- [ ] SESSION.md 作成 ← 追加
```

**実装タスク**:
- [ ] dev:story SKILL.md に Phase 4.2 追加
- [ ] SESSION.md テンプレート定義
- [ ] 完了条件の更新

---

## Phase 2: 継続学習システム

### 2.1 /learn コマンド実装

**ファイル**: `.claude/commands/learn.md`

（内容は既存計画書と同じ - 省略）

**実装タスク**:
- [ ] learn.md コマンド作成
- [ ] .claude/skills/learned/ ディレクトリ作成

### 2.2 evaluate-session.sh (Stop Hook)

**ファイル**: `.claude/hooks/continuous-learning/evaluate-session.sh`

（内容は既存計画書と同じ - 省略）

**実装タスク**:
- [ ] evaluate-session.sh 作成
- [ ] config.json 作成
- [ ] hooks.json に Stop hook として追加

### 2.3 戦略的コンパクション

**ファイル**: `.claude/hooks/strategic-compact/suggest-compact.sh`

（内容は既存計画書と同じ - 省略）

**実装タスク**:
- [ ] suggest-compact.sh 作成
- [ ] hooks.json に PreToolUse hook として追加

---

## 実装ロードマップ（更新版）

### Phase 1（2-3時間） - セッションメモリ基盤

| タスク | 成果物 | 所要時間 |
|--------|--------|---------|
| ディレクトリ構造作成 | `.claude/hooks/`, `.claude/sessions/` | 10分 |
| hooks.json 作成 | hooks設定ファイル | 20分 |
| session-start.sh 実装 | ストーリー検出版SessionStart hook | 45分 |
| pre-compact.sh 実装 | ストーリー対応PreCompact hook | 20分 |
| session-end.sh 実装 | ストーリー対応Stop hook | 45分 |
| dev:story 統合 | Phase 4.2 SESSION.md作成 | 30分 |
| **テスト実行** | 全hooks動作確認 | 30分 |

**チェックポイント**:
- [ ] ストーリー内で SessionStart hook が SESSION.md を検出
- [ ] ストーリー外で グローバルセッションにフォールバック
- [ ] Stop hook で SESSION.md が更新される
- [ ] dev:story で SESSION.md が自動作成される

### Phase 2（2-3時間） - 継続学習 + コンパクション

（既存計画書と同じ）

---

## 統合後の開発フロー

```
┌────────────────────────────────────────────────────────────┐
│                  /dev:story 実行                            │
└───────────────────┬────────────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Phase 0-3: 既存処理  │
         │  - story-analysis.json │
         │  - task-list.json     │
         │  - TODO.md            │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Phase 4: 新規追加    │
         │  - SESSION.md 作成   │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   開発作業開始        │
         │  (dev:developing)    │
         └──────────┬───────────┘
                    │
              [セッション終了]
                    │
                    ▼
         ┌──────────────────────┐
         │   Stop Hook 実行     │
         │  - SESSION.md 更新   │
         │  - Last Updated更新  │
         └──────────┬───────────┘
                    │
         [翌日セッション開始]
                    │
                    ▼
         ┌──────────────────────┐
         │ SessionStart Hook    │
         │ - SESSION.md 検出    │
         │ - 前回状態を通知     │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  作業継続            │
         │  (前回の続きから)     │
         └──────────────────────┘
```

---

## 成功指標

### Phase 1 完了時

- [ ] ストーリー内で SESSION.md が自動作成される
- [ ] SessionStart hook で前回の状態が通知される
- [ ] Stop hook で SESSION.md が更新される
- [ ] グローバルセッションへのフォールバックが機能する

### Phase 2 完了時

- [ ] /learn でパターン保存成功
- [ ] Stop hook でパターン抽出提案
- [ ] 戦略的コンパクション提案が機能

---

## リスク と対策

| リスク | 影響 | 対策 |
|--------|------|------|
| SESSION.md のコミット漏れ | チームで状態共有できない | pre-commit hook で警告 |
| 複数ストーリー同時作業 | どのSESSION.mdか混乱 | ディレクトリ構造で明確化 |
| グローバルセッションの肥大化 | ファイルサイズ増大 | 30日自動削除 |

---

## 次のステップ

1. **Phase 1 実装開始**: hooks基盤とセッションメモリ（ストーリー統合版）
2. **動作確認**: 実際のストーリーで検証
3. **フィードバック収集**: 使用感の評価
4. **Phase 2 移行判断**: Phase 1 が安定したら継続学習実装

---

## 参照

- **著者リポジトリ**: `docs/SAMPLE/dot-claude-dev/everything-claude-code/`
- **Longform Guide**: `docs/SAMPLE/dot-claude-dev/The Longform Guide to Everything Claude Code.md`
- **初期分析**: `docs/analysis/longform-guide-integration-analysis.md`
- **手法一覧**: `docs/analysis/implementation-techniques-overview.md`
