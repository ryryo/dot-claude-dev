# CLAUDE.md

このリポジトリはClaude Codeによるストーリー駆動開発のための構造化されたアプローチを提供します：

## ユーザー確認には AskUserQuestion を使う

ユーザーに Yes/No の確認を求める場面（例: 「プッシュしますか？」「rebase してよいですか？」）では、テキストで問いかけるのではなく **AskUserQuestion ツール** を使うこと。ユーザーがワンクリックで回答でき、やりとりがスムーズになる。

## 利用可能なスキル

### 開発ワークフロー（Big 3）

| スキル             | 用途                                                                                                                                                                                                     |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **dev:story**      | ストーリーからTDD/E2E/TASK分岐付きタスクリスト（task-list.json）を生成。ストーリー駆動開発の起点。Triggers: /dev:story, ストーリーからタスク, タスク分解                                                 |
| **dev:developing** | task-list.jsonのタスクを実行。workflowフィールド（tdd/e2e/task）に応じたワークフローで実装。TDDは4ステップ(CYCLE→REVIEW→CHECK→SPOT)、E2Eは3ステップ(CYCLE→CHECK→SPOT)、TASKは3ステップ(EXEC→VERIFY→SPOT) |
| **dev:feedback**   | 実装完了後、学んだことをDESIGN.mdに蓄積し、スキル/ルールの自己改善を提案。PR作成まで実行。Triggers: /dev:feedback, 実装振り返り, フィードバック                                                          |

### アイデアワークフロー

| スキル           | 用途                                                                                                                                       |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **dev:ideation** | プロダクトアイデアをJTBD分析→競合調査→SLC仕様書に構造化。何を作るべきかを明確にする。Triggers: /dev:ideation, アイデア整理, プロダクト企画 |

### ユーティリティ

| スキル                 | 用途                                                                                                                                 |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **agent-browser**      | ブラウザ操作を自動化。Webテスト、フォーム入力、スクリーンショット、データ抽出。Triggers: ブラウザ操作, Webテスト, スクリーンショット |
| **dev:opencode-check** | opencode CLIの動作確認。インストール状態、runコマンド、モデル応答をチェック。Triggers: opencode動作確認, opencode check              |

### メタスキル

| スキル                 | 用途                                                                                                                                                                                                              |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **meta-skill-creator** | スキルを作成・更新・プロンプト改善するためのメタスキル。collaborativeモードでユーザーと対話しながら共創し、orchestrateモードでタスクの実行エンジンを選択。Triggers: スキル作成, スキル更新, プロンプト改善        |
| **skill-refactorer**   | SKILL.mdを整理・圧縮するスキル。7つのリファクタリングパターン（圧縮・DRY化・LLM行動制御・ゲート条件・責務分離・廃止整理・構造化）をチェックリストとして適用。Triggers: スキル整理, SKILL.md圧縮, スキルリファクタ |

## 利用可能なコマンド

| コマンド          | 説明                                                                         |
| ----------------- | ---------------------------------------------------------------------------- |
| `/dev:ideation`   | アイデアからプロダクト仕様書生成。JTBD分析→競合調査→SLC仕様                  |
| `/dev:story`      | ストーリーからタスクリスト生成。dev:storyスキルを起動                        |
| `/dev:developing` | タスクリストからラベルに応じたワークフローで実装。dev:developingスキルを起動 |
| `/dev:feedback`   | 実装完了後の振り返り。dev:feedbackスキルを起動してDESIGN.md更新と改善提案    |

## テスト環境

### テストフレームワーク

| 言語/FW                   | テストフレームワーク           | 理由                                                |
| ------------------------- | ------------------------------ | --------------------------------------------------- |
| **TypeScript/JavaScript** | Vitest                         | 高速、ESM/TypeScriptネイティブ対応、Vite統合        |
| **React**                 | Vitest + React Testing Library | ユーザー視点のテスト、アクセシビリティ重視          |
| **PHP**                   | Pest                           | describe/it/expect構文でVitest/Jestと統一、モダンDX |

### テストファイル命名規則

テストファイルは必ず以下の命名規則に従うこと:

- TypeScript/JavaScript: `*.test.ts` / `*.test.tsx` / `*.spec.ts` / `*.spec.tsx`
- PHP: `tests/**/*Test.php`

この命名規則により、TDDワークフロールール（`tdd-workflow.md`）が自動適用されます。

## 開発ワークフロー

### ストーリー駆動開発フロー

```
1. /dev:story 実行
   └── ストーリー入力 → task-list.json生成（workflowフィールド付き）

2. dev:developing でタスク実行
   ├── [TASK] EXEC → VERIFY → SPOT(+OpenCode)
   ├── [TDD] CYCLE(RED→GREEN→REFACTOR+OpenCode) → REVIEW(+OpenCode) → CHECK → SPOT(+OpenCode)
   └── [E2E] CYCLE(UI実装→agent-browser検証) → CHECK → SPOT(+OpenCode)

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
| **E2E**  | UIコンポーネント、レイアウト   | CYCLE→CHECK→SPOT(+OpenCode)                              |
| **TASK** | 設定、セットアップ、インフラ   | EXEC→VERIFY→SPOT(+OpenCode)                              |

## OpenCode CLI協調

特定のエージェントはOpenCode CLIを使用して、実装バイアスを排除した客観的な分析を行います。

### OpenCode使用エージェント

| エージェント       | 用途                           | タイミング                            |
| ------------------ | ------------------------------ | ------------------------------------- |
| **plan-review**    | タスク分解の品質レビュー       | dev:story Step 4                      |
| **tdd-cycle**      | TDDリファクタリング分析        | dev:developing TDD CYCLE Phase 3      |
| **tdd-review**     | TDDレビュー分析                | dev:developing TDD REVIEW Step 2      |
| **spot-review**    | commit後の即時レビュー（検出） | dev:developing 各ワークフローCOMMIT後 |
| **review-analyze** | 実装後の品質チェック           | dev:feedback Step 1                   |
| **propose-manage** | トレードオフ分析・改善提案     | dev:feedback Step 3                   |

### OpenCode呼び出しパターン

```bash
opencode run -m openai/gpt-5.3-codex "{prompt}" 2>&1
```

### 言語プロトコル

- **OpenCodeへの質問**: 英語
- **ユーザーへの報告**: 日本語

### フォールバック

OpenCode CLIが利用不可の場合（環境変数 `USE_OPENCODE=false` またはコマンドエラー）:

- 従来のClaude opusベースの分析にフォールバック
- 各エージェントのチェックリストに基づいて手動分析
