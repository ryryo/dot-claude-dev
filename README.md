# dot-claude-dev

Claude Codeのための仕様書駆動開発ワークフロー。スキル・コマンド群で仕様書作成から実装まで一貫してサポートする。

## 概要

このリポジトリは以下の構造化された開発ワークフローを提供します：

1. **仕様書を作成** - `/dev:spec` で要件深掘り→タスク分解→自己完結した実装仕様書を生成
2. **仕様書を実行** - `/dev:spec-run` でGateごとにIMPL + VERIFYを実行（従来 or Codexモード）

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

### 1. 仕様書を作成

```bash
/dev:spec
```

要件を深掘りし、タスク分解→レビューループを経て自己完結した実装仕様書（`docs/PLAN/*/spec.md`）を生成します。別エージェントがその仕様書だけで実装を完遂できることをゴールとします。

### 2. 仕様書を実行

```bash
/dev:spec-run
```

実行モードを選択してGateごとにIMPL + VERIFYを実行：

| モード | 動作 |
|---|---|
| **従来モード** | Claude Code が全Todoを直接実行 |
| **Codexモード** | 全タスクをCodexプラグインに委任、VERIFYはcodex review |

## ワークフロー図

```
┌─────────────────────────────────────────────────────────────┐
│                  仕様書駆動開発                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. /dev:spec                                               │
│     └── 要件深掘り → タスク分解 → 仕様書 → レビューループ      │
│                                                             │
│  2. /dev:spec-run                                           │
│     ├── [従来]  Claude が全Todoを直接実行                    │
│     └── [Codex] Codex委任 → codex review                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## コマンド一覧

### 仕様書駆動ワークフロー

| コマンド | 説明 |
|---|---|
| `/dev:spec` | 自己完結した実装仕様書を作成（要件深掘り→タスク分解→レビューループ） |
| `/dev:spec-run` | 仕様書を実行。従来モードまたはCodexモードを選択 |
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

機能別仕様書。実装で得た知見・決定事項・発見されたパターンを蓄積します。

### Hook駆動コミット

`PostToolUse` フックが各Taskエージェント完了後に発火し、未コミット行数が10行以上あれば自動コミットを促します。

## ライセンス

MIT
