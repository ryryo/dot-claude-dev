# Longform Guide 統合分析レポート

> **目的**: 「The Longform Guide to Everything Claude Code」のテクニックを現在の開発スキルセットに統合するための網羅的分析

## 現状分析サマリー

### 現在の強み（既に実装済み）

| 領域 | 実装状況 | 詳細 |
|------|----------|------|
| **ストーリー駆動開発** | ✅ 完全実装 | dev:story → dev:developing → dev:feedback |
| **TDD/E2E/TASK分類** | ✅ 完全実装 | workflow-branching.md で判定ロジック定義 |
| **スキル自己改善** | ✅ 実装済み | LOGS.md, EVALS.json, patterns.md |
| **Progressive Disclosure** | ✅ 実装済み | 必要時のみリソース読み込み |
| **サブエージェント活用** | ✅ 部分実装 | モデル指定（opus/sonnet/haiku）あり |
| **Worktree統合** | ✅ 実装済み | dev:story Phase 0 で自動判定・作成 |
| **言語別ルール** | ✅ 完全実装 | 6言語×3カテゴリ（coding/testing/design） |

### 改善機会（未実装または強化可能）

| 領域 | 現状 | 記事の提案 | 優先度 |
|------|------|-----------|--------|
| **セッションメモリ永続化** | ❌ 未実装 | SessionStart/Stop/PreCompact hooks | 🔴 高 |
| **戦略的コンテキスト圧縮** | ❌ 未実装 | 手動compactタイミング提案hook | 🟡 中 |
| **動的システムプロンプト注入** | ❌ 未実装 | CLIフラグでコンテキスト切り替え | 🟢 低 |
| **継続学習の自動抽出** | 🟡 部分実装 | セッション終了時に自動スキル生成 | 🔴 高 |
| **トークン最適化** | 🟡 部分実装 | モデル選択ガイドライン強化 | 🟡 中 |
| **評価パターン** | 🟡 基本のみ | checkpoint/continuous eval | 🟡 中 |
| **並列化戦略** | 🟡 基本のみ | Cascade Method, 2インスタンス起動 | 🟢 低 |
| **MCP最適化** | ❌ 未検討 | CLI代替スキル化 | 🟢 低 |

---

## 1. セッションメモリ永続化（優先度：高）

### 記事の提案

```
SESSION 1                              SESSION 2
─────────                              ─────────

[Start]                                [Start]
   │                                      │
   ▼                                      ▼
┌──────────────┐                    ┌──────────────┐
│ SessionStart │ ◄─── reads ─────── │ SessionStart │◄── loads previous
│    Hook      │     nothing yet    │    Hook      │    context
└──────┬───────┘                    └──────┬───────┘
       │                                   │
       ▼                                   ▼
   [Working]                           [Working]
       │                               (informed)
       ▼                                   │
┌──────────────┐                           ▼
│  PreCompact  │──► saves state       [Continue...]
│    Hook      │    before summary
└──────┬───────┘
       │
       ▼
   [Compacted]
       │
       ▼
┌──────────────┐
│  Stop Hook   │──► persists to ──────────►
│ (session-end)│    ~/.claude/sessions/
└──────────────┘
```

### 現在の状態

- `.claude/hooks/` ディレクトリが**存在しない**
- セッション間メモリはファイルベース（DESIGN.md, LOGS.md）だが**手動**
- 自動的な前回セッション読み込みは**なし**

### 統合提案

#### 1.1 ディレクトリ構造

```
.claude/
├── hooks/
│   ├── session-start.sh       # セッション開始時の自動読み込み
│   ├── pre-compact.sh         # 圧縮前の状態保存
│   ├── session-end.sh         # セッション終了時の永続化
│   └── memory-persistence/
│       └── session-template.md
├── sessions/                  # セッションログ保存先
│   └── .gitkeep
```

#### 1.2 session-start.sh 実装案

```bash
#!/bin/bash
# セッション開始時に最近のコンテキストを読み込む

SESSIONS_DIR="$HOME/.claude/sessions"
RECENT_DAYS=7

# 最近7日間のセッションファイルを検索
recent_sessions=$(find "$SESSIONS_DIR" -name "*.md" -mtime -$RECENT_DAYS -type f | sort -r | head -5)

if [ -n "$recent_sessions" ]; then
  echo "📚 Recent sessions found:"
  for session in $recent_sessions; do
    echo "  - $(basename $session)"
  done
  echo ""
  echo "💡 Use '@session-YYYY-MM-DD.md' to load specific context"
fi

# 現在のプロジェクトのDESIGN.mdを検出
if [ -d "docs/features" ]; then
  design_files=$(find docs/features -name "DESIGN.md" -type f 2>/dev/null | head -3)
  if [ -n "$design_files" ]; then
    echo "📐 Project design docs available:"
    for design in $design_files; do
      echo "  - $design"
    done
  fi
fi
```

#### 1.3 session-end.sh 実装案

```bash
#!/bin/bash
# セッション終了時に学習内容を永続化

SESSIONS_DIR="$HOME/.claude/sessions"
TODAY=$(date +%Y-%m-%d)
SESSION_FILE="$SESSIONS_DIR/session-$TODAY.md"

mkdir -p "$SESSIONS_DIR"

# セッションテンプレートを作成/更新
cat >> "$SESSION_FILE" << EOF

---
## Session: $(date +%H:%M)

### Completed
<!-- What was accomplished -->

### Learnings
<!-- Patterns discovered, techniques that worked -->

### Blockers
<!-- Issues encountered, unresolved problems -->

### Next Steps
<!-- What to continue next session -->

---
EOF

echo "📝 Session logged to: $SESSION_FILE"
```

#### 1.4 hooks設定（settings.json）

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/session-start.sh"
      }]
    }],
    "PreCompact": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/pre-compact.sh"
      }]
    }],
    "Stop": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/session-end.sh"
      }]
    }]
  }
}
```

#### 1.5 dev:feedbackとの統合

現在の `dev:feedback` スキルに以下を追加:

```markdown
## Phase 7: セッション永続化（新規）

実装完了後、セッションで得た知見を永続化:

1. DESIGN.md更新（既存）
2. patterns.md更新（既存）
3. **session-summary.md作成（新規）**
   - 成功したアプローチ
   - 失敗したアプローチ
   - 未試行のアプローチ
   - 次回の開始点
```

---

## 2. 戦略的コンテキスト圧縮（優先度：中）

### 記事の提案

- auto-compactを無効化し、論理的な区切りで手動compact
- ツール呼び出し回数をカウントし、閾値で提案

### 現在の状態

- 自動圧縮に依存
- 論理的フェーズ移行時の圧縮タイミング指針なし

### 統合提案

#### 2.1 compact-suggester hook

```bash
#!/bin/bash
# 戦略的圧縮提案 (PreToolUse hook)

COUNTER_FILE="/tmp/claude-tool-count-$$"
THRESHOLD=${COMPACT_THRESHOLD:-50}

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
  echo "[StrategicCompact] $THRESHOLD tool calls reached" >&2
  echo "💡 Consider /compact if transitioning between phases" >&2
fi
```

#### 2.2 TDD/E2Eワークフローへの統合

`dev:developing` スキルに圧縮タイミングを明示:

```markdown
## 推奨圧縮ポイント

| フェーズ移行 | 圧縮推奨 | 理由 |
|-------------|---------|------|
| Phase 0→1 | ❌ | Worktree作成のコンテキスト必要 |
| RED→GREEN | ❌ | テストコンテキスト必要 |
| GREEN→REFACTOR | ✅ | 実装完了、探索コンテキスト不要 |
| REFACTOR→COMMIT | ✅ | リファクタ完了、新規開始可能 |
| TASK完了後 | ✅ | セットアップ完了、実装開始 |
```

---

## 3. 継続学習スキル自動抽出（優先度：高）

### 記事の提案

Stop hookでセッションを評価し、非自明なパターンをスキルとして保存

### 現在の状態

- `meta-skill-creator` が手動スキル作成をサポート
- LOGS.md, EVALS.json で使用状況追跡
- **自動抽出は未実装**

### 統合提案

#### 3.1 evaluate-session.sh

```bash
#!/bin/bash
# セッション終了時にパターン抽出を評価

SKILLS_DIR=".claude/skills/learned"
SESSION_LOG="$HOME/.claude/sessions/session-$(date +%Y-%m-%d).tmp"

mkdir -p "$SKILLS_DIR"

# パターン抽出候補を検出
# - 同じエラーを3回以上解決
# - 特定のワークアラウンドを繰り返し使用
# - デバッグ手法の発見

echo "🔍 Evaluating session for learnable patterns..."
echo "📂 Learned skills will be saved to: $SKILLS_DIR"
```

#### 3.2 /learn コマンド

`.claude/commands/learn.md`:

```markdown
---
name: learn
description: 現在のセッションから学習パターンを抽出
---

# /learn コマンド

## 概要

セッション中に発見した非自明なパターンをスキルとして抽出・保存する。

## 使用タイミング

- エラーを解決した直後
- 新しいデバッグ手法を発見した直後
- プロジェクト固有のパターンを見つけた直後

## ワークフロー

1. ユーザーに抽出内容を確認
2. スキルファイルをドラフト
3. 確認後 `.claude/skills/learned/` に保存
4. 次回セッションで自動読み込み

## 出力形式

```
.claude/skills/learned/
├── error-resolution-{slug}.md
├── debug-technique-{slug}.md
└── project-pattern-{slug}.md
```
```

#### 3.3 dev:feedbackとの統合

```markdown
## Phase 4: パターン検出（強化）

### 自動抽出トリガー

| 条件 | アクション |
|------|----------|
| 同じパターンが3回出現 | スキル化を提案 |
| エラー解決で新手法発見 | `learned/` に保存提案 |
| ワークアラウンド使用 | ルール追加を提案 |
```

---

## 4. トークン最適化パターン（優先度：中）

### 記事の提案

- モデル選択の明確なガイドライン
- Haiku/Opus組み合わせ（5x価格差活用）
- 背景プロセスのtmux分離

### 現在の状態

- `dev:story` でモデル指定あり（opus→sonnet→haiku）
- 体系的なガイドラインは未文書化
- tmux統合なし

### 統合提案

#### 4.1 モデル選択ガイドライン文書

`.claude/rules/optimization/model-selection.md`:

```markdown
# モデル選択ガイドライン

## 基本原則

| モデル | 用途 | コスト |
|--------|------|--------|
| **Haiku** | 反復作業、明確な指示、ワーカー役 | $1/M入力 |
| **Sonnet** | 90%のコーディングタスク（デフォルト） | $3/M入力 |
| **Opus** | 初回失敗後、5+ファイル、アーキテクチャ決定 | $5/M入力 |

## タスク別推奨

| タスク | モデル | 理由 |
|--------|--------|------|
| ストーリー分析 | Opus | 深い理解が必要 |
| タスク分解 | Sonnet | 標準的な分解作業 |
| TDD/E2E分類 | Haiku | 明確な判定基準あり |
| テスト実行 | Haiku | 結果報告のみ |
| リファクタリング | Opus | 品質判断が必要 |
| 検証 | Haiku | チェックリスト処理 |

## アップグレード条件

Sonnet → Opus:
- 初回試行が失敗
- 変更が5+ファイルにまたがる
- セキュリティクリティカル

## ダウングレード条件

Sonnet → Haiku:
- 指示が非常に明確
- 反復的なタスク
- マルチエージェントのワーカー
```

#### 4.2 サブエージェント定義の標準化

現在の各スキルのTask呼び出しにモデル指定を明示:

```javascript
// 現在
Task({
  subagent_type: "general-purpose",
  model: "sonnet"  // ← 既に指定あり（良い）
})

// 提案: エージェント定義ファイルでも標準化
// .claude/agents/test-runner.md
---
name: test-runner
description: テスト実行とサマリー報告
tools: Bash
model: haiku  // 明示的に安価モデル指定
---
```

---

## 5. 評価パターンの強化（優先度：中）

### 記事の提案

- チェックポイントベース評価（線形ワークフロー向け）
- 継続評価（長時間セッション向け）
- pass@k / pass^k メトリクス

### 現在の状態

- EVALS.json で基本メトリクス追跡
- 体系的な評価パターンは未定義

### 統合提案

#### 5.1 EVALS.json スキーマ拡張

```json
{
  "skillName": "dev:story",
  "currentLevel": 3,
  "metrics": {
    "totalUsageCount": 150,
    "successCount": 142,
    "failureCount": 8,
    "successRate": 94.67,
    "averageDuration": 45,
    "lastEvaluated": "2026-01-22T08:00:00Z"
  },
  "evalPatterns": {
    "type": "checkpoint",  // 新規追加
    "checkpoints": [
      { "name": "Phase 1 Complete", "passRate": 98 },
      { "name": "Phase 2 Complete", "passRate": 95 },
      { "name": "Phase 3 Complete", "passRate": 92 }
    ]
  },
  "passMetrics": {  // 新規追加
    "pass_at_1": 0.70,
    "pass_at_3": 0.91,
    "pass_at_5": 0.97
  }
}
```

#### 5.2 検証フロー統合

```markdown
## TDDワークフロー検証パターン

```
[CHECKPOINT 1: RED Phase]
├── テストファイル作成確認
├── テスト実行→失敗確認
└── 失敗 → 修正ループ（最大3回）

[CHECKPOINT 2: GREEN Phase]
├── 実装ファイル作成確認
├── テスト実行→成功確認
└── 失敗 → 実装修正（テスト変更禁止）

[CHECKPOINT 3: REFACTOR Phase]
├── コード品質チェック
├── テスト実行→成功維持確認
└── 失敗 → リファクタ修正
```
```

---

## 6. 並列化戦略の体系化（優先度：低）

### 記事の提案

- Git Worktreeによる並列インスタンス分離
- Cascade Method（左→右スイープ）
- 2インスタンス起動パターン

### 現在の状態

- `dev:story` でWorktree作成サポート
- 体系的な並列化ガイドラインなし

### 統合提案

#### 6.1 並列化ガイドライン文書

`.claude/rules/optimization/parallelization.md`:

```markdown
# 並列化戦略ガイドライン

## 基本原則

1. **最小限の並列化**: 本当に必要な場合のみ
2. **直交タスク**: コード変更が重複しないこと
3. **明確な責務**: 各インスタンスの役割を明確に

## 推奨パターン

### 2インスタンス起動（プロジェクト開始時）

| インスタンス | 役割 | ツール |
|-------------|------|--------|
| **Instance 1** | スキャフォールド | Write, Bash, Edit |
| **Instance 2** | 深層リサーチ | WebSearch, WebFetch |

### 開発中の並列化

| メインインスタンス | フォーク | 目的 |
|-------------------|---------|------|
| コード変更 | 質問・調査 | コンテキスト分離 |
| 実装 | ドキュメント取得 | 非干渉 |

## 避けるべきパターン

- ❌ 5+インスタンスの同時起動
- ❌ 同じファイルへの並列変更
- ❌ 目的なしのフォーク
```

---

## 7. 統合優先度マトリクス

| 改善項目 | 効果 | 実装コスト | 優先度 | 推奨フェーズ |
|----------|------|-----------|--------|-------------|
| セッションメモリ永続化 | 高 | 中 | 🔴 | Phase 1 |
| 継続学習自動抽出 | 高 | 中 | 🔴 | Phase 1 |
| 戦略的コンテキスト圧縮 | 中 | 低 | 🟡 | Phase 2 |
| トークン最適化ガイドライン | 中 | 低 | 🟡 | Phase 2 |
| 評価パターン強化 | 中 | 中 | 🟡 | Phase 2 |
| 並列化戦略ガイドライン | 低 | 低 | 🟢 | Phase 3 |
| 動的システムプロンプト注入 | 低 | 低 | 🟢 | Phase 3 |
| MCP→CLI変換 | 低 | 中 | 🟢 | Phase 3 |

---

## 8. 実装ロードマップ

### Phase 1（即時実装推奨）

1. `.claude/hooks/` ディレクトリ作成
2. session-start.sh, session-end.sh 実装
3. /learn コマンド作成
4. dev:feedback Phase 7 追加

### Phase 2（安定後実装）

1. compact-suggester hook 追加
2. model-selection.md ガイドライン作成
3. EVALS.json スキーマ拡張
4. 検証フロー統合

### Phase 3（最適化フェーズ）

1. parallelization.md ガイドライン作成
2. CLIエイリアス設定例
3. MCP代替スキル検討

---

## 9. 現在のスキルセットとの相乗効果

### dev:story × セッションメモリ

```
前回セッション → session-YYYY-MM-DD.md
     ↓ SessionStart hook で自動読み込み
今回セッション → 「前回はPhase 2まで完了」
     ↓ コンテキストを引き継ぎ
dev:story Phase 3から継続
```

### dev:feedback × 継続学習

```
実装完了 → dev:feedback 実行
     ↓
Phase 4: パターン検出
     ↓ 3回以上の繰り返しパターン発見
Phase 7: 自動スキル生成提案
     ↓ ユーザー承認
.claude/skills/learned/{pattern}.md 保存
```

### meta-skill-creator × 評価パターン

```
スキル作成 → EVALS.json 初期化
     ↓ 使用回数増加
10回実行 → 自動評価トリガー
     ↓ pass@k 計算
パフォーマンス低下検出 → 改善提案
```

---

## 10. まとめ

記事の主要テクニックのうち、現在のスキルセットに**即座に統合可能**なもの:

1. **セッションメモリ永続化** - hooks基盤の追加で実現
2. **継続学習自動抽出** - dev:feedbackの拡張で実現
3. **トークン最適化ガイドライン** - 文書追加のみ

**既存の強みを活かせる**もの:

- Progressive Disclosureは既に実装済み
- サブエージェントのモデル指定も一部実装済み
- Worktree統合も実装済み

**統合により得られる効果**:

| 効果 | 説明 |
|------|------|
| セッション継続性 | 複数日にわたる開発の効率化 |
| 知識蓄積 | 繰り返しパターンの自動スキル化 |
| コスト削減 | 適切なモデル選択による最適化 |
| 品質向上 | 体系的な評価パターンによる検証 |
