# dot-claude-dev

Claude Codeのためのストーリー駆動開発ワークフロー。TDD/E2E/TASKの自動分類と多段階のスキル・コマンド群で開発を加速する。

## 概要

このリポジトリは以下の構造化された開発ワークフローを提供します：

1. **フィーチャーを設計** - `/dev:epic` でストーリー分割・計画書生成
2. **タスクに分解** - `/dev:story` でTDD/E2E/TASK自動分類
3. **タスクを実行** - `dev:developing` で適切なワークフローを自動選択
4. **学びを蓄積** - `/dev:feedback` でDESIGN.md更新・スキル改善提案

## インストール

### 共有リポジトリをセットアップ

```bash
# 1. このリポジトリをホームディレクトリにクローン（推奨）
git clone https://github.com/ryryo/dot-claude-dev.git ~/.claude-shared

# または任意の場所に配置（環境変数で指定）
export CLAUDE_SHARED_DIR="$HOME/repos/claude-shared"
git clone https://github.com/ryryo/dot-claude-dev.git "$CLAUDE_SHARED_DIR"
```

### プロジェクトに適用

```bash
# 2. プロジェクトディレクトリで実行
cd /path/to/your-project
bash ~/.claude-shared/scripts/setup-claude.sh
```

これにより以下の構造が作成されます：

```
your-project/.claude/
├── rules/
│   ├── languages -> ~/.claude-shared/.claude/rules/languages  # シンボリックリンク
│   └── workflow -> ~/.claude-shared/.claude/rules/workflow    # シンボリックリンク
├── skills/
│   └── dev -> ~/.claude-shared/.claude/skills/dev             # シンボリックリンク
├── commands/
│   └── dev -> ~/.claude-shared/.claude/commands/dev           # シンボリックリンク
└── settings.local.json # プロジェクト固有
```

### 更新

```bash
cd ~/.claude-shared
git pull
# すべてのプロジェクトに自動反映される
```

## 使い方

### 1. フィーチャーを設計（任意）

```bash
/dev:epic
```

大きなフィーチャー向け。要件を入力すると `PLAN.md` + `plan.json`（ストーリー一覧・executionType付き）を生成します。

### 2. ストーリーからタスクを生成

```bash
/dev:story
```

ストーリーを分析し `task-list.json`（workflowフィールド付き）を生成します：
- **TDD** — ロジック・バリデーション・計算
- **E2E** — UIコンポーネント・レイアウト・視覚的確認が必要なもの
- **TASK** — 設定・セットアップ・インフラ・ドキュメント

### 3. タスクを実行

```bash
/dev:developing
```

`task-list.json` のワークフローに応じて自動選択：

| ワークフロー | フロー |
|---|---|
| **TDD** | CYCLE (RED→GREEN→REFACTOR+OpenCode) → REVIEW(+OpenCode) → CHECK → SPOT |
| **E2E** | IMPL(UI実装) → AUTO(agent-browser検証, FIXループ最大3回) → CHECK → SPOT |
| **TASK** | EXEC → VERIFY → SPOT |

### 4. フィードバックを記録

```bash
/dev:feedback
```

実装後、DESIGN.mdを更新し、繰り返しパターンを検出してスキル/ルールの改善を提案。PR作成まで実行します。

## ワークフロー図

```
┌─────────────────────────────────────────────────────────────┐
│                  ストーリー駆動開発                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  0. /dev:epic（任意）                                        │
│     └── 要件入力 → PLAN.md + plan.json（ストーリー一覧）      │
│                                                             │
│  1. /dev:story                                              │
│     └── ストーリー → task-list.json（TDD/E2E/TASK付き）       │
│                                                             │
│  2. /dev:developing                                         │
│     ├── [TDD]  CYCLE→REVIEW→CHECK→SPOT                     │
│     ├── [E2E]  IMPL→AUTO→CHECK→SPOT                        │
│     └── [TASK] EXEC→VERIFY→SPOT                            │
│                                                             │
│  3. /dev:feedback                                           │
│     └── DESIGN.md更新 → パターン検出 → 改善提案 → PR作成     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## コマンド一覧

### 開発ワークフロー

| コマンド | 説明 |
|---|---|
| `/dev:epic` | フィーチャー全体設計・ストーリー分割。PLAN.md + plan.json 生成 |
| `/dev:story` | ストーリーからタスクリスト（task-list.json）生成 |
| `/dev:developing` | タスクリストのworkflowに応じて実装（TDD/E2E/TASK） |
| `/dev:feedback` | 実装完了後の振り返り。DESIGN.md更新・改善提案・PR作成 |

### 仕様書

| コマンド | 説明 |
|---|---|
| `/dev:spec` | 自己完結した実装仕様書を作成（要件深掘り→タスク分解→レビューループ） |
| `/dev:spec-run` | 仕様書を実行。OpenCodeハイブリッドレビュー付き |
| `/dev:clarify` | 不明点を繰り返し明確化して詳細な仕様書を作成 |
| `/dev:ideation` | アイデアをJTBD分析→競合調査→SLC仕様書に構造化 |

### ユーティリティ

| コマンド | 説明 |
|---|---|
| `/dev:decomposition` | 複雑なタスクを詳細なアクション可能なTodoに分解 |
| `/dev:dig` | 未知を発見しプランを強化するための深い探索的インタビュー |
| `/dev:deslop` | ブランチのdiffからAI生成コードの不備を除去 |
| `/dev:fix-ci` | 現在のPRのCI失敗を自動で診断・修正 |
| `/dev:checkpoint` | コンテキスト圧迫時にメモリ保存→/clear→作業再開を支援 |
| `/dev:simple-add` | Git commit自動化 |

### スキル

| スキル | 説明 |
|---|---|
| `dev:agent-browser` | agent-browser CLIでブラウザ検証をサブエージェント実行 |
| `dev:cleanup-branches` | 不要なローカル・リモートブランチとworktreeを一括削除 |
| `dev:git-reflect` | Git履歴から作業セッションを自動検出し振り返りサマリーを生成 |
| `dev:design-e2e-qa` | 実装済みサイトのデザイン品質を体系的にチェック（修正は行わない） |
| `meta-skill-creator` | スキルを作成・更新・プロンプト改善するためのメタスキル |
| `skill-refactorer` | SKILL.mdの実行効率・コンテキスト効率を最適化 |
| `sync-skills` | グローバルスキル一覧を外部プロジェクトのCLAUDE.mdに同期 |
| `setup-project` | 指定プロジェクトにdot-claude-devの共通設定をセットアップ |

## 構造

```
.claude/
├── skills/dev/
│   ├── agent-browser/       # ブラウザ検証（E2Eワークフローで使用）
│   ├── cleanup-branches/    # ブランチ整理
│   ├── design-e2e-qa/       # デザインQA
│   ├── git-reflect/         # Git振り返り
│   ├── ideation/            # アイデア→仕様書
│   ├── meta-skill-creator/  # スキル作成・改善
│   ├── skill-refactorer/    # SKILL.md最適化
│   ├── spec/                # 実装仕様書作成
│   └── spec-run/            # 仕様書実行
├── commands/dev/
│   ├── epic.md              # フィーチャー設計
│   ├── story.md             # タスク分解
│   ├── developing.md        # タスク実行
│   ├── feedback.md          # 実装振り返り
│   ├── spec.md              # 仕様書作成
│   ├── spec-run.md          # 仕様書実行
│   ├── clarify.md           # 仕様明確化
│   ├── decomposition.md     # タスク分解
│   ├── dig.md               # 深掘りインタビュー
│   ├── deslop.md            # AIコード不備除去
│   ├── fix-ci.md            # CI修正
│   ├── checkpoint.md        # コンテキスト保存
│   └── simple-add.md        # Git commit
└── rules/
    ├── workflow/             # TDD/E2E/TASKワークフロールール
    └── languages/            # 言語別コーディングルール
```

## 主要コンセプト

### 3分類の判定基準

| 分類 | 対象 | 判定基準 |
|---|---|---|
| **TDD** | ロジック、バリデーション、計算 | 入出力が明確・アサーションで検証可能 |
| **E2E** | UIコンポーネント、レイアウト | 視覚的確認・UX判断が必要 |
| **TASK** | 設定、セットアップ、インフラ | テスト不要・UI検証不要 |

### OpenCode統合

TDD/E2E/TASKの各ワークフロー末尾にSPOTステップがあり、OpenCodeが実装をレビューします：

```bash
opencode run -m openai/gpt-5.3-codex "{prompt}" 2>&1
```

### DESIGN.md

機能別仕様書。実装で得た知見・決定事項・発見されたパターンを蓄積します。`/dev:feedback` が自動更新します。

### Hook駆動コミット

`PostToolUse` フックが各Taskエージェント完了後に発火し、未コミット行数が10行以上あれば自動コミットを促します。

## ライセンス

MIT
