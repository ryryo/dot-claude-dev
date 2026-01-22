# CLAUDE.md

このファイルはClaude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## ルールとスキルの構造

このリポジトリはClaude Codeによるストーリー駆動開発のための構造化されたアプローチを提供します：

- **ルール**: `.claude/rules/` に配置。ファイルパスに基づいて自動的に読み込まれます。プロジェクト規約の情報源。
- **スキル**: `.claude/skills/` に配置。特定のワークフローで手動で呼び出します。
- **コマンド**: `.claude/commands/` に配置。スキルを呼び出すためのショートカット。

## 利用可能なルール

### ワークフロールール

| ルール | 適用対象 | 説明 |
|--------|----------|------|
| **tdd-workflow** | `**/*.test.ts`, `**/*.spec.ts`, `**/*.test.tsx`, `**/*.spec.tsx` | TDD 6ステップワークフロー（RED→GREEN→REFACTOR→REVIEW→CHECK→COMMIT） |
| **e2e-cycle** | `**/components/**/*.tsx`, `**/pages/**/*.tsx`, `**/views/**/*.php` | E2Eサイクル（UI実装→agent-browser検証→品質チェック→コミット） |
| **workflow-branching** | `**/TODO.md` | TDD/E2E/TASK分岐判定ルール |

### 言語別ルール

| ルール | 適用対象 | 説明 |
|--------|----------|------|
| **typescript/coding** | `**/*.ts`, `**/*.tsx` | TypeScriptコーディング規約。strict mode、Zod連携、Result型パターン |
| **typescript/testing** | `**/*.test.ts`, `**/*.spec.ts` | TypeScriptテスト規約。Vitest、Given-When-Then形式 |
| **react/coding** | `**/*.tsx`, `**/*.jsx` | Reactコーディング規約。関数コンポーネント、Hooks、React Hook Form + Zod |
| **react/testing** | `**/*.test.tsx`, `**/*.spec.tsx` | Reactテスト規約。Vitest、React Testing Library、ユーザー視点テスト |
| **react/design** | `**/components/**/*.tsx` | Reactデザイン規約。Compound Components、アクセシビリティ |
| **javascript/coding** | `**/*.js`, `**/*.mjs` | JavaScriptコーディング規約。ES6+、async/await |
| **javascript/testing** | `**/*.test.js`, `**/*.spec.js` | JavaScriptテスト規約。Vitest |
| **php/coding** | `**/*.php` | PHPコーディング規約。PSR-12、strict_types |
| **php/testing** | `**/tests/**/*.php`, `**/*Test.php` | PHPテスト規約。Pest |
| **python/coding** | `**/*.py` | Pythonコーディング規約。PEP 8、型ヒント、Pydantic |
| **python/testing** | `**/test_*.py`, `**/*_test.py` | Pythonテスト規約。pytest |
| **html-css/coding** | `**/*.html`, `**/*.css`, `**/*.scss` | HTML/CSSコーディング規約。セマンティックHTML、CSS変数、BEM |
| **html-css/testing** | `**/*.html`, `**/*.css` | HTML/CSSテスト規約。axe-core、Playwright視覚的回帰 |
| **html-css/design** | `**/*.html`, `**/*.css`, `**/components/**/*` | HTML/CSSデザイン規約。デザイントークン、アクセシビリティ |

## 利用可能なスキル

### 開発ワークフロー（Big 3）

| スキル | 用途 |
|--------|------|
| **dev:story-to-tasks** | ストーリーからTDD/E2E/TASK分岐付きタスクリスト（TODO.md）を生成。Worktree作成後、最初に実行するスキル。Triggers: /dev:story, ストーリーからタスク, タスク分解 |
| **dev:developing** | TODO.mdのタスクを実行。TDD/E2E/TASKラベルに応じたワークフローで実装。TDDは6ステップ、E2Eはagent-browser検証付き、TASKはEXEC→VERIFY→COMMIT |
| **dev:feedback** | 実装完了後、学んだことをDESIGN.mdに蓄積し、スキル/ルールの自己改善を提案。Triggers: /dev:feedback, 実装振り返り, フィードバック |

### メタスキル

| スキル | 用途 |
|--------|------|
| **meta-skill-creator** | スキルを作成・更新・プロンプト改善するためのメタスキル。collaborativeモードでユーザーと対話しながら共創し、orchestrateモードでタスクの実行エンジンを選択。Triggers: スキル作成, スキル更新, プロンプト改善 |

## 利用可能なコマンド

| コマンド | 説明 |
|----------|------|
| `/dev:story` | ストーリーからタスクリスト生成。dev:story-to-tasksスキルを起動 |
| `/dev:feedback` | 実装完了後の振り返り。dev:feedbackスキルを起動してDESIGN.md更新と改善提案 |

## テスト環境

### テストフレームワーク

| 言語/FW | テストフレームワーク | 理由 |
|---------|---------------------|------|
| **TypeScript/JavaScript** | Vitest | 高速、ESM/TypeScriptネイティブ対応、Vite統合 |
| **React** | Vitest + React Testing Library | ユーザー視点のテスト、アクセシビリティ重視 |
| **PHP** | Pest | describe/it/expect構文でVitest/Jestと統一、モダンDX |


### テストファイル命名規則

テストファイルは必ず以下の命名規則に従うこと:

- TypeScript/JavaScript: `*.test.ts` / `*.test.tsx` / `*.spec.ts` / `*.spec.tsx`
- PHP: `tests/**/*Test.php`

この命名規則により、TDDワークフロールール（`tdd-workflow.md`）が自動適用されます。

## 開発ワークフロー

### ストーリー駆動開発フロー

```
1. Worktree作成
   └── git worktree add -b feature/xxx

2. /dev:story 実行
   └── ストーリー入力 → TODO.md生成（TDD/E2E/TASKラベル付き）

3. dev:developing でタスク実行
   ├── [TASK] EXEC → VERIFY → COMMIT
   ├── [TDD] RED → GREEN → REFACTOR → REVIEW → CHECK → COMMIT
   └── [E2E] UI実装 → agent-browser検証 → 品質チェック → COMMIT

4. /dev:feedback 実行
   └── DESIGN.md更新 → パターン検出 → スキル/ルール改善提案

5. PR作成 & マージ
```

### 主要コンセプト

- **TDD判定**: ビジネスロジック、API、データ処理 → 自動テスト可能
- **E2E判定**: UI/UX、視覚的要素、ユーザー操作フロー → agent-browser検証
- **TASK判定**: 設定、セットアップ、インフラ、ドキュメント → テスト不要・UI検証不要
- **DESIGN.md**: 機能別仕様書。実装で得た知見を蓄積
- **フィードバックループ**: 3回以上同じパターンが現れたらスキル/ルール化を検討

### 3分類の定義

| カテゴリ | 対象 | ワークフロー |
|----------|------|--------------|
| **TDD** | ロジック、バリデーション、計算 | RED→GREEN→REFACTOR→REVIEW→CHECK→COMMIT |
| **E2E** | UIコンポーネント、レイアウト | IMPL→AUTO→CHECK→COMMIT |
| **TASK** | 設定、セットアップ、インフラ | EXEC→VERIFY→COMMIT |
