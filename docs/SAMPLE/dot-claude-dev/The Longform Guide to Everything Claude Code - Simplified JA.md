---
title: "The Longform Guide to Everything Claude Code（簡潔版）"
source_url: "https://x.com/affaanmustafa/status/2014040193557471352"
source: X (formerly Twitter)
extracted_at: "2026-01-22T08:05:43.756Z"
---

# The Longform Guide to Everything Claude Code（簡潔版）

このガイドは、生産的なセッションと無駄なセッションを分ける手法をカバーする。テーマは**トークンエコノミクス**、**メモリ永続化**、**検証パターン**、**並列化戦略**、そして**再利用可能なワークフローの構築による複利効果**である。

---

## 1. メモリ管理とセッション永続化

### セッションログパターン

セッション間でメモリを共有するには、進捗を要約して`.claude`フォルダの`.tmp`ファイルに保存するスキルまたはコマンドが最適である。

```
~/.claude/sessions/YYYY-MM-DD-topic.tmp
```

セッションファイルには以下を含める：
- 機能したアプローチ（検証可能な証拠付き）
- 試みたが失敗したアプローチ
- まだ試していないアプローチと残りのタスク

### メモリ永続化フック

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

**フックの役割**：
- **PreCompact Hook**: コンテキスト圧縮前に重要な状態をファイルに保存
- **SessionComplete Hook**: セッション終了時に学習内容をファイルに永続化
- **SessionStart Hook**: 新セッション開始時に前回のコンテキストを自動読み込み

**設定例**：

```json
{
  "hooks": {
    "PreCompact": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/memory-persistence/pre-compact.sh"
      }]
    }],
    "SessionStart": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/memory-persistence/session-start.sh"
      }]
    }],
    "Stop": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/memory-persistence/session-end.sh"
      }]
    }]
  }
}
```

---

## 2. コンテキスト管理（Strategic Compacting）

計画を設定してコンテキストをクリアしたら、その計画から作業できる。これは実行に不要な探索コンテキストが蓄積された場合に有効である。

**戦略的圧縮のポイント**：
- 自動圧縮を無効化
- 論理的な区切りで手動圧縮を実行（または条件に基づいて提案するスキルを作成）

```bash
#!/bin/bash
# Strategic Compact Suggester
# PreToolUseで実行し、論理的な区切りで手動圧縮を提案

COUNTER_FILE="/tmp/claude-tool-count-$$"
THRESHOLD=${COMPACT_THRESHOLD:-50}

# カウンター初期化または増分
if [ -f "$COUNTER_FILE" ]; then
  count=$(cat "$COUNTER_FILE")
  count=$((count + 1))
  echo "$count" > "$COUNTER_FILE"
else
  echo "1" > "$COUNTER_FILE"
  count=1
fi

# 閾値に達したら圧縮を提案
if [ "$count" -eq "$THRESHOLD" ]; then
  echo "[StrategicCompact] $THRESHOLD tool calls reached - consider /compact if transitioning phases" >&2
fi
```

---

## 3. 継続学習パターン

### 問題

同じ問題に繰り返し遭遇し、「修正」プロンプトでClaudeのコンパスを再調整する必要がある。

### 解決策

Claude Codeが非自明な発見をしたとき（デバッグ手法、回避策、プロジェクト固有のパターン）、その知識を新しいスキルとして保存する。次に同様の問題が発生したとき、スキルが自動的にロードされる。

**なぜStopフックを使うのか？**

UserPromptSubmitは送信するすべてのメッセージで実行され、オーバーヘッドとレイテンシが増加する。Stopはセッション終了時に一度だけ実行され、軽量で、セッション全体を評価できる。

**設定例**：

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/skills/continuous-learning/evaluate-session.sh"
          }
        ]
      }
    ]
  }
}
```

Stopフックはセッション終了時に発火し、スクリプトがセッションを分析して抽出価値のあるパターン（エラー解決、デバッグ手法、回避策、プロジェクト固有のパターンなど）を検出し、再利用可能なスキルとして`~/.claude/skills/learned/`に保存する。

---

## 4. トークン最適化

### サブエージェントアーキテクチャ

タスクに十分な最も安価なモデルに委譲するサブエージェントアーキテクチャを設計する。

**モデル選択クイックリファレンス**：

| モデル | 用途 | コスト |
|--------|------|--------|
| Haiku | 反復タスク、明確な指示、ワーカー | 最安 |
| Sonnet | コーディングタスクの90% | 中間 |
| Opus | 最初の試行が失敗、5+ファイルにまたがるタスク、アーキテクチャ決定、セキュリティクリティカル | 最高 |

Haiku vs Opusは5倍のコスト差があり、Sonnet vs Opusの1.67倍の差と比較して大きい。

**エージェント定義でのモデル指定**：

```yaml
---
name: quick-search
description: Fast file search
tools: Glob, Grep
model: haiku  # 安価で高速
---
```

### ツール固有の最適化

頻繁に呼び出されるツールを考慮する。例えば、grepをmgrepに置き換えると、従来のgrepやripgrepと比較して平均約半分のトークン削減効果がある。

### バックグラウンドプロセス

Claudeが全出力を処理してライブストリーミングする必要がない場合、バックグラウンドプロセスをClaude外部で実行する。tmuxを使用して実現できる。ターミナル出力を要約するか、必要な部分のみをコピーする。これにより入力トークン（コストの大部分を占める）を大幅に節約できる。

### モジュラーコードベースの利点

数千行ではなく数百行のメインファイルを持つ、より再利用可能なユーティリティ、関数、フックを持つモジュラーコードベースは、トークン最適化コストと初回でタスクを正しく完了することの両方に役立つ。

```
root/
├── docs/                   # グローバルドキュメント
├── scripts/                # CI/CDとビルドスクリプト
├── src/
│   ├── apps/               # エントリポイント（API、CLI、Workers）
│   │   ├── api-gateway/    # モジュールへのリクエストルーティング
│   │   └── cron-jobs/
│   │
│   ├── modules/            # システムのコア
│   │   ├── ordering/       # 自己完結型「Ordering」モジュール
│   │   │   ├── api/        # 他モジュール向けパブリックインターフェース
│   │   │   ├── domain/     # ビジネスロジック＆エンティティ（Pure）
│   │   │   ├── infrastructure/ # DB、外部クライアント、リポジトリ
│   │   │   ├── use-cases/  # アプリケーションロジック（オーケストレーション）
│   │   │   └── tests/      # ユニット＆インテグレーションテスト
│   │   │
│   │   ├── catalog/        # 自己完結型「Catalog」モジュール
│   │   └── identity/       # 自己完結型「Auth/User」モジュール
│   │
│   ├── shared/             # すべてのモジュールで使用するコード
│   │   ├── kernel/         # 基底クラス（Entity、ValueObject）
│   │   ├── events/         # グローバルイベントバス定義
│   │   └── utils/          # 汎用ヘルパー
│   │
│   └── main.ts             # アプリケーションブートストラップ
├── tests/                  # E2Eグローバルテスト
├── package.json
└── README.md
```

### リーンなコードベース = 安価なトークン

コードベースがリーンであればあるほど、トークンコストは安くなる。スキルとコマンドを使用してリファクタリングし、コードベースを継続的にクリーンアップすることで、デッドコードを特定することが重要である。また、特定の時点で、コードベース全体をスキムして、目立つものや繰り返しに見えるものを探し、手動でそのコンテキストをまとめ、リファクタリングスキルとデッドコードスキルと一緒にClaudeに入力することを推奨する。

---

## 5. 評価とハーネス調整

### 観測性メソッド

スキルがトリガーされたときに思考ストリームと出力をトレースするtmuxプロセスをフックする方法、またはClaudeが具体的に何を実行し、正確な変更と出力が何だったかをログに記録するPostToolUseフックを持つ方法がある。

### ベンチマークワークフロー

```
[Same Task]
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
    ┌───────────────┐         ┌───────────────┐
    │  Worktree A   │         │  Worktree B   │
    │  WITH skill   │         │ WITHOUT skill │
    └───────┬───────┘         └───────┬───────┘
            │                         │
            ▼                         ▼
       [Output A]                [Output B]
            │                         │
            └──────────┬──────────────┘
                       ▼
                  [git diff]
                       │
                       ▼
              ┌────────────────┐
              │ Compare logs,  │
              │ token usage,   │
              │ output quality │
              └────────────────┘
```

### 評価パターンタイプ

```
CHECKPOINT-BASED                         CONTINUOUS
─────────────────                        ──────────

  [Task 1]                                 [Work]
     │                                        │
     ▼                                        ▼
  ┌─────────┐                            ┌─────────┐
  │Checkpoint│◄── verify                 │ Timer/  │
  │   #1    │    criteria                │ Change  │
  └────┬────┘                            └────┬────┘
       │ pass?                                │
   ┌───┴───┐                                  ▼
   │       │                            ┌──────────┐
  yes     no ──► fix ──┐                │Run Tests │
   │              │    │                │  + Lint  │
   ▼              └────┘                └────┬─────┘
  [Task 2]                                   │
     │                                  ┌────┴────┐
     ▼                                  │         │
  ┌─────────┐                          pass     fail
  │Checkpoint│                          │         │
  │   #2    │                           ▼         ▼
  └────┬────┘                        [Continue] [Stop & Fix]
       │                                          │
      ...                                    └────┘

Best for: Linear workflows              Best for: Long sessions
with clear milestones                   exploratory refactoring
```

**チェックポイントベース評価**：
- ワークフローに明示的なチェックポイントを設定
- 各チェックポイントで定義された基準に対して検証
- 検証失敗時、Claudeは続行前に修正必須
- 明確なマイルストーンを持つ線形ワークフローに適切

**継続評価**：
- N分ごとまたは大きな変更後に実行
- フルテストスイート、ビルドステータス、lint
- リグレッションを即座に報告
- 続行前に停止して修正
- 長時間実行セッションに適切

### グレーダータイプ

| タイプ | 説明 | 特性 |
|--------|------|------|
| コードベース | 文字列マッチ、バイナリテスト、静的解析、結果検証 | 高速、安価、客観的、ただし有効なバリエーションに脆弱 |
| モデルベース | ルーブリックスコアリング、自然言語アサーション、ペアワイズ比較 | 柔軟でニュアンスを扱える、ただし非決定論的で高価 |
| 人間 | SMEレビュー、クラウドソース判断、スポットチェックサンプリング | ゴールドスタンダード品質、ただし高価で遅い |

### 主要メトリクス

```
pass@k: k回の試行のうち少なくとも1回成功
        ┌─────────────────────────────────────┐
        │  k=1: 70%  k=3: 91%  k=5: 97%      │
        │  Higher k = higher odds of success  │
        └─────────────────────────────────────┘

pass^k: k回の試行すべてが成功必須
        ┌─────────────────────────────────────┐
        │  k=1: 70%  k=3: 34%  k=5: 17%      │
        │  Higher k = harder (consistency)    │
        └─────────────────────────────────────┘
```

- **pass@k**: 動作すればよく、検証フィードバックがあれば十分な場合に使用
- **pass^k**: 一貫性が不可欠で、ほぼ決定論的な出力一貫性が必要な場合に使用

---

## 6. 並列化戦略

### 基本原則

会話をフォークする際、フォークと元の会話のアクションのスコープを明確に定義する。コード変更に関してはオーバーラップを最小限にする。干渉の可能性を防ぐため、互いに直交するタスクを選択する。

### 推奨パターン

メインチャットはコード変更に取り組み、フォークはコードベースとその現在の状態についての質問、または外部サービスに関するリサーチ（ドキュメントの取得、適用可能なオープンソースリポジトリのGitHub検索など）に使用する。

### 任意のターミナル数について

ターミナルとインスタンスの追加は、真の必要性と目的から行うべきである。スクリプトでそのタスクを処理できるなら、スクリプトを使用する。

**目標**: 最小限の並列化で最大限の成果を得る

### Git Worktreeによる並列インスタンス

```bash
# 並列作業用のworktreeを作成
git worktree add ../project-feature-a feature-a
git worktree add ../project-feature-b feature-b
git worktree add ../project-refactor refactor-branch

# 各worktreeが独自のClaudeインスタンスを持つ
cd ../project-feature-a && claude
```

**メリット**：
- インスタンス間でgitコンフリクトなし
- 各インスタンスがクリーンな作業ディレクトリを持つ
- 出力の比較が容易
- 異なるアプローチで同じタスクをベンチマーク可能

### カスケードメソッド

複数のClaude Codeインスタンスを実行する際、「カスケード」パターンで整理する：
- 新しいタスクは右側の新しいタブで開く
- 左から右へ、古いものから新しいものへスイープ
- 一貫した方向フローを維持
- 必要に応じて特定のタスクをチェック
- **一度に最大3-4タスクに集中** - それ以上は生産性よりも精神的オーバーヘッドが速く増加

---

## 7. サブエージェントオーケストレーション

### サブエージェントコンテキスト問題

サブエージェントは要約を返すことでコンテキストを節約するために存在する。しかし、オーケストレーターにはサブエージェントが持たないセマンティックコンテキストがある。サブエージェントはリクエストの背後にあるPURPOSE/REASONINGではなく、文字通りのクエリのみを知っている。

### イテレーティブ取得パターン

```
┌─────────────────┐
│  ORCHESTRATOR   │
│  (has context)  │
└────────┬────────┘
         │ dispatch with query + objective
         ▼
┌─────────────────┐
│   SUB-AGENT     │
│ (lacks context) │
└────────┬────────┘
         │ returns summary
         ▼
┌─────────────────┐      ┌─────────────┐
│   EVALUATE      │─no──►│  FOLLOW-UP  │
│   Sufficient?   │      │  QUESTIONS  │
└────────┬────────┘      └──────┬──────┘
         │ yes                  │
         ▼                      │ sub-agent
    [ACCEPT]              fetches answers
                                │
         ◄──────────────────────┘
              (max 3 cycles)
```

**修正方法**：
- オーケストレーターがすべてのサブエージェント返却を評価
- 受け入れる前にフォローアップ質問を行う
- サブエージェントがソースに戻り、回答を取得して返却
- 十分になるまでループ（無限ループ防止のため最大3サイクル）

**クエリだけでなく目的コンテキストを渡す**: サブエージェントをディスパッチする際、具体的なクエリとより広い目的の両方を含める。これによりサブエージェントが要約に何を含めるべきか優先順位付けできる。

### シーケンシャルフェーズを持つオーケストレーターパターン

```markdown
Phase 1: RESEARCH (use Explore agent)
- コンテキストを収集
- パターンを特定
- Output: research-summary.md

Phase 2: PLAN (use planner agent)
- research-summary.mdを読む
- 実装計画を作成
- Output: plan.md

Phase 3: IMPLEMENT (use tdd-guide agent)
- plan.mdを読む
- テストを先に書く
- コードを実装
- Output: code changes

Phase 4: REVIEW (use code-reviewer agent)
- すべての変更をレビュー
- Output: review-comments.md

Phase 5: VERIFY (use build-error-resolver if needed)
- テストを実行
- 問題を修正
- Output: done or loop back
```

**主要ルール**：
1. 各エージェントは1つの明確な入力を受け取り、1つの明確な出力を生成
2. 出力が次フェーズの入力になる
3. フェーズをスキップしない - 各フェーズが価値を追加
4. エージェント間で`/clear`を使用してコンテキストを新鮮に保つ
5. 中間出力をファイルに保存（メモリだけでなく）

### エージェント抽象化ティアリスト

**Tier 1: 直接バフ（使いやすい）**
- **サブエージェント** - コンテキスト腐敗防止とアドホック特化のための直接バフ。マルチエージェントの半分の有用性だが、はるかに低い複雑さ
- **メタプロンプティング** - 「20分のタスクのプロンプトに3分かける」直接バフ - 安定性を向上させ、仮定をサニティチェック
- **最初にユーザーにもっと質問** - 一般的にバフ、ただしプランモードで質問に答える必要がある

**Tier 2: 高スキルフロア（うまく使うのが難しい）**
- **長時間実行エージェント** - 15分タスク vs 1.5時間 vs 4時間タスクの形状とトレードオフを理解する必要がある
- **並列マルチエージェント** - 非常に高い分散、非常に複雑またはよくセグメント化されたタスクにのみ有用
- **ロールベースマルチエージェント** - 裁定取引が非常に高くない限り、ハードコードされたヒューリスティクスにはモデルの進化が速すぎる
- **コンピュータ使用エージェント** - 非常に初期のパラダイム、調整が必要

**結論**: Tier 1パターンから始める。基本をマスターし、真のニーズがある場合にのみTier 2に進む。

---

## 8. 再利用可能なパターンの哲学

> "Early on, I spent time building reusable workflows/patterns. Tedious to build, but this had a wild compounding effect as models and agent harnesses improved."

**投資すべきもの**：
- サブエージェント
- スキル
- コマンド
- 計画パターン
- MCPツール
- コンテキストエンジニアリングパターン

**なぜ複利効果があるのか**: 一度構築すれば、モデルアップグレード間で機能する。パターンへの投資 > 特定のモデルトリックへの投資。

---

## References

- Anthropic: Demystifying evals for AI agents (Jan 2026)
- Anthropic: "Claude Code Best Practices" (Apr 2025)
- Fireworks AI: "Eval Driven Development with Claude Code" (Aug 2025)
- YK: 32 Claude Code Tips (Dec 2025)
- Addy Osmani: "My LLM coding workflow going into 2026"
