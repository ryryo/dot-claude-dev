# dot-claude-dev

Claude Codeのためのストーリー駆動開発ワークフロー。TDD/PLANベースの開発と自動タスク分類を可能にするスキル、ルール、コマンドのコレクション。

## 概要

このリポジトリは以下の構造化された開発ワークフローを提供します：

1. **ユーザーストーリーをタスクに変換** - TDD/PLAN自動分類付き
2. **タスクを実行** - 適切なワークフローを使用（ロジックにはTDD、UIにはPLAN）
3. **学びを蓄積** - スキル/ルールの改善を提案

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

# WSL環境でも同様に動作
```

これにより以下の構造が作成されます：

```
your-project/.claude/
├── rules/
│   ├── languages -> ~/.claude-shared/.claude/rules/languages  # シンボリックリンク
│   └── workflow -> ~/.claude-shared/.claude/rules/workflow    # シンボリックリンク
├── skills/
│   ├── dev -> ~/.claude-shared/.claude/skills/dev             # シンボリックリンク
│   ├── meta-skill-creator -> ...                              # シンボリックリンク
│   └── agent-browser -> ...                                   # シンボリックリンク
├── commands/
│   └── dev -> ~/.claude-shared/.claude/commands/dev           # シンボリックリンク
├── settings.local.json # プロジェクト固有
└── hooks/             # プロジェクト固有
```

**利点**：
- 共通設定の更新が全プロジェクトに即座に反映
- プロジェクト固有の設定も追加可能
- WSL環境でも問題なく動作

### 更新

共通設定を更新：

```bash
cd ~/.claude-shared
git pull
# すべてのプロジェクトに自動反映される
```

## 使い方

### 1. ユーザーストーリーから始める

```bash
# Claude Codeでプロジェクトディレクトリにて
/dev:story
```

プロンプトが表示されたらユーザーストーリーを入力します。スキルは以下を実行します：
- ストーリーを分析
- タスクに分解
- 各タスクをTDDまたはPLANに分類
- workflowフィールド付きの `task-list.json` を生成

### 2. タスクを実行

`dev:developing` スキルが適切なワークフローを自動選択します：

**TDDワークフロー**（ビジネスロジック、API、データ処理向け）：
```
RED → GREEN → REFACTOR → REVIEW → CHECK → COMMIT
```

**PLANワークフロー**（UI/UX、視覚的要素向け）：
```
IMPL → AUTO（agent-browser検証） → CHECK → COMMIT
```

### 3. フィードバックを記録

```bash
/dev:feedback
```

実装後、このスキルは以下を実行します：
- 学びで `DESIGN.md` を更新
- 繰り返しパターンを検出
- スキル/ルールの改善を提案

## ワークフロー図

```
┌─────────────────────────────────────────────────────────────┐
│                  ストーリー駆動開発                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. /dev:story                                              │
│     └── ストーリー → task-list.json（workflow付き）            │
│                                                             │
│  2. dev:developing                                          │
│     ├── [TDD] RED→GREEN→REFACTOR→REVIEW→CHECK→COMMIT       │
│     └── [PLAN] IMPL→AUTO→CHECK→COMMIT                      │
│                                                             │
│  3. /dev:feedback                                           │
│     └── DESIGN.md更新 → パターン検出 → 改善提案              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 構造

```
.claude/
├── skills/
│   ├── dev/
│   │   ├── story/            # ストーリー → task-list.json変換
│   │   ├── developing/       # タスク実行（TDD/PLAN）
│   │   └── feedback/         # 学びの記録
│   └── meta-skill-creator/   # スキル作成/改善
├── rules/
│   ├── workflow/             # TDD/PLANワークフロールール
│   └── languages/            # 言語別コーディングルール
└── commands/
    └── dev/                  # ショートカットコマンド
```

## 対応言語

| 言語 | コーディング | テスト | デザイン |
|------|------------|--------|----------|
| TypeScript | ✅ | ✅ | - |
| React | ✅ | ✅ | ✅ |
| JavaScript | ✅ | ✅ | - |
| Python | ✅ | ✅ | - |
| PHP | ✅ | ✅ | - |
| HTML/CSS | ✅ | ✅ | ✅ |

## 主要コンセプト

### TDD分類
以下の場合にタスクはTDDに分類されます：
- 入出力が明確に定義できる
- アサーションで検証可能
- ロジック層（バリデーション、計算、変換）

### PLAN分類
以下の場合にタスクはPLANに分類されます：
- 視覚的確認が必要
- UX/UI判断が含まれる
- プレゼンテーション層（コンポーネント、レイアウト、アニメーション）

### DESIGN.md
以下を蓄積する機能別仕様書：
- 実装の決定事項
- 開発からの学び
- 発見されたパターン

## ライセンス

MIT
