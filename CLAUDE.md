# CLAUDE.md

このリポジトリはClaude Codeによるストーリー駆動開発のための構造化されたアプローチを提供します：

## ユーザー確認には AskUserQuestion を使う

ユーザーに Yes/No の確認を求める場面（例: 「プッシュしますか？」「rebase してよいですか？」）では、テキストで問いかけるのではなく **AskUserQuestion ツール** を使うこと。ユーザーがワンクリックで回答でき、やりとりがスムーズになる。

## 利用可能なスキル

### 開発ワークフロー

| スキル             | 用途                                                                                                                                                                                                         |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **dev:epic**       | フィーチャー全体の設計・ストーリー分割。PLAN.md + plan.json を生成し、dev:story の上位レイヤーとして機能。各ストーリーに executionType（manual/developing/coding）を付与。Triggers: /dev:epic, フィーチャー計画, エピック作成 |
| **dev:story**      | ストーリーからTDD/E2E/TASK分岐付きタスクリスト（task-list.json）を生成。plan.json がある場合はそこからストーリーを選択。Triggers: /dev:story, ストーリーからタスク, タスク分解                                  |
| **dev:developing** | task-list.jsonのタスクを実行。workflowフィールド（tdd/e2e/task）に応じたワークフローで実装。planPath があれば全体計画を参照可能。Triggers: /dev:developing, 実装, 開発                                         |
| **dev:feedback**   | 実装完了後、学んだことをDESIGN.mdに蓄積し、スキル/ルールの自己改善を提案。PR作成まで実行。Triggers: /dev:feedback, 実装振り返り, フィードバック                                                              |

### アイデアワークフロー

| スキル           | 用途                                                                                                                                       |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **dev:ideation** | プロダクトアイデアをJTBD分析→競合調査→SLC仕様書に構造化。何を作るべきかを明確にする。Triggers: /dev:ideation, アイデア整理, プロダクト企画 |

### ユーティリティ

| スキル                   | 用途                                                                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **dev:agent-browser**    | agent-browser CLIでブラウザ検証をサブエージェント実行。E2Eテスト、UI確認、スクリーンショット取得。Triggers: agent-browser, ブラウザ検証, E2E確認 |
| **dev:opencode-check**   | opencode CLIの動作確認。インストール状態、runコマンド、モデル応答をチェック。Triggers: opencode動作確認, opencode check                          |
| **dev:cleanup-branches** | 不要なローカル・リモートブランチとworktreeを一括削除。Triggers: ブランチ整理, 不要ブランチ削除                                                   |

### メタスキル

| スキル                 | 用途                                                                                                                                                                                                              |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **meta-skill-creator** | スキルを作成・更新・プロンプト改善するためのメタスキル。collaborativeモードでユーザーと対話しながら共創し、orchestrateモードでタスクの実行エンジンを選択。Triggers: スキル作成, スキル更新, プロンプト改善        |
| **skill-refactorer**   | SKILL.mdの実行効率・コンテキスト効率を最適化するスキル。7ステップのリファクタリング手順（実行方式判定→ファイル配置→詳細分離→DRY化→LLM行動制御→構造化→不要削除）を適用。Triggers: スキル整理, SKILL.md圧縮, スキルリファクタ |
| **sync-skills**        | グローバルスキル一覧を参照している外部プロジェクトのCLAUDE.mdを最新状態に同期。Triggers: /sync-skills, スキル同期                                                                                                 |
| **setup-project**      | 指定プロジェクトにdot-claude-devの共通設定をセットアップ。シンボリックリンク作成、remote script コピー、.gitignore更新、settings.json作成まで一括実行。Triggers: /setup-project, セットアップ, プロジェクトにセットアップ |

## 利用可能なコマンド

| コマンド             | 説明                                                                         |
| -------------------- | ---------------------------------------------------------------------------- |
| `/dev:ideation`      | アイデアからプロダクト仕様書生成。JTBD分析→競合調査→SLC仕様                  |
| `/dev:epic`          | フィーチャー全体設計・ストーリー分割。PLAN.md + plan.json 生成               |
| `/dev:story`         | ストーリーからタスクリスト生成。dev:storyスキルを起動                        |
| `/dev:developing`    | タスクリストからラベルに応じたワークフローで実装。dev:developingスキルを起動 |
| `/dev:feedback`      | 実装完了後の振り返り。dev:feedbackスキルを起動してDESIGN.md更新と改善提案    |

## 開発ワークフロー

### ストーリー駆動開発フロー

```
0. /dev:epic 実行（任意、大きなフィーチャー向け）
   └── 要件入力 → PLAN.md + plan.json 生成（ストーリー一覧、executionType付き）

1. /dev:story 実行
   ├── plan.json あり → ストーリー選択 → タスク分解
   └── plan.json なし → ストーリー入力 → task-list.json生成（workflowフィールド付き）

2. dev:developing でタスク実行（planPath で全体計画を参照可能）
   ├── [TASK] EXEC → VERIFY → SPOT(+OpenCode)
   ├── [TDD] CYCLE(RED→GREEN→REFACTOR+OpenCode) → REVIEW(+OpenCode) → CHECK → SPOT(+OpenCode)
   └── [E2E] IMPL(UI実装) → AUTO(agent-browser検証, FIXループ最大3回) → CHECK → SPOT(+OpenCode)

3. /dev:feedback 実行
   ├── DESIGN.md更新 → パターン検出 → スキル/ルール改善提案
   └── PR作成（gh pr create）
```

### 主要コンセプト

- **TDD判定**: ビジネスロジック、API、データ処理 → 自動テスト可能
- **E2E判定**: UI/UX、視覚的要素、ユーザー操作フロー → agent-browser検証
- **TASK判定**: 設定、セットアップ、インフラ、ドキュメント → テスト不要・UI検証不要
- **DESIGN.md**: 機能別仕様書。実装で得た知見を蓄積
- **フィードバックループ**: 3回以上同じパターンが現れたらスキル/ルール化を検討

### 3分類の定義

| カテゴリ | 対象                           | ワークフロー                                             |
| -------- | ------------------------------ | -------------------------------------------------------- |
| **TDD**  | ロジック、バリデーション、計算 | CYCLE(+OpenCode)→REVIEW(+OpenCode)→CHECK→SPOT(+OpenCode) |
| **E2E**  | UIコンポーネント、レイアウト   | IMPL→AUTO→CHECK→SPOT(+OpenCode)                          |
| **TASK** | 設定、セットアップ、インフラ   | EXEC→VERIFY→SPOT(+OpenCode)                              |

### OpenCode呼び出しパターン

```bash
opencode run -m openai/gpt-5.3-codex "{prompt}" 2>&1
```
