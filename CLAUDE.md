# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Rules and Skills Structure

This repository provides a structured approach for Story-Driven Development with Claude Code:

- **Rules**: Located at `.claude/rules/`, these are automatically loaded based on file paths. Source of truth for project conventions.
- **Skills**: Located at `.claude/skills/`, these are manually invoked for specific workflows.
- **Commands**: Located at `.claude/commands/`, these are shortcuts to invoke skills.

## Available Rules

### Workflow Rules

| Rule | Applies To | Description |
|------|------------|-------------|
| **tdd-workflow** | `**/*.test.ts`, `**/*.spec.ts`, `**/*.test.tsx`, `**/*.spec.tsx` | TDD 6ステップワークフロー（RED→GREEN→REFACTOR→REVIEW→CHECK→COMMIT） |
| **plan-cycle** | `**/components/**/*.tsx`, `**/pages/**/*.tsx`, `**/views/**/*.php` | PLANサイクル（UI実装→agent-browser検証→品質チェック→コミット） |
| **tdd-plan-branching** | `**/TODO.md` | TDD/PLAN分岐判定ルール |

### Language Rules

| Rule | Applies To | Description |
|------|------------|-------------|
| **typescript/coding** | `**/*.ts`, `**/*.tsx` | TypeScriptコーディング規約。strict mode、Zod連携、Result型パターン |
| **typescript/testing** | `**/*.test.ts`, `**/*.spec.ts` | TypeScriptテスト規約。Vitest/Jest、Given-When-Then形式 |
| **react/coding** | `**/*.tsx`, `**/*.jsx` | Reactコーディング規約。関数コンポーネント、Hooks、React Hook Form + Zod |
| **react/testing** | `**/*.test.tsx`, `**/*.spec.tsx` | Reactテスト規約。React Testing Library、ユーザー視点テスト |
| **react/design** | `**/components/**/*.tsx` | Reactデザイン規約。Compound Components、アクセシビリティ |
| **javascript/coding** | `**/*.js`, `**/*.mjs` | JavaScriptコーディング規約。ES6+、async/await |
| **javascript/testing** | `**/*.test.js`, `**/*.spec.js` | JavaScriptテスト規約。Jest/Vitest |
| **php/coding** | `**/*.php` | PHPコーディング規約。PSR-12、strict_types |
| **php/testing** | `**/tests/**/*.php`, `**/*Test.php` | PHPテスト規約。PHPUnit/Pest |
| **python/coding** | `**/*.py` | Pythonコーディング規約。PEP 8、型ヒント、Pydantic |
| **python/testing** | `**/test_*.py`, `**/*_test.py` | Pythonテスト規約。pytest |
| **html-css/coding** | `**/*.html`, `**/*.css`, `**/*.scss` | HTML/CSSコーディング規約。セマンティックHTML、CSS変数、BEM |
| **html-css/testing** | `**/*.html`, `**/*.css` | HTML/CSSテスト規約。axe-core、Playwright視覚的回帰 |
| **html-css/design** | `**/*.html`, `**/*.css`, `**/components/**/*` | HTML/CSSデザイン規約。デザイントークン、アクセシビリティ |

## Available Skills

### Development Workflow (Big 3)

| Skill | Use Case |
|-------|----------|
| **dev:story-to-tasks** | ストーリーからTDD/PLAN分岐付きタスクリスト（TODO.md）を生成。Worktree作成後、最初に実行するスキル。Triggers: /dev:story, ストーリーからタスク, タスク分解 |
| **dev:developing** | TODO.mdのタスクを実行。TDD/PLANラベルに応じたワークフローで実装。TDDは6ステップ（RED→GREEN→REFACTOR→REVIEW→CHECK→COMMIT）、PLANはagent-browser検証付き |
| **dev:feedback** | 実装完了後、学んだことをDESIGN.mdに蓄積し、スキル/ルールの自己改善を提案。Triggers: /dev:feedback, 実装振り返り, フィードバック |

### Meta Skill

| Skill | Use Case |
|-------|----------|
| **meta-skill-creator** | スキルを作成・更新・プロンプト改善するためのメタスキル。collaborativeモードでユーザーと対話しながら共創し、orchestrateモードでタスクの実行エンジンを選択。Triggers: スキル作成, スキル更新, プロンプト改善 |

## Available Commands

| Command | Description |
|---------|-------------|
| `/dev:story` | ストーリーからタスクリスト生成。dev:story-to-tasksスキルを起動 |
| `/dev:feedback` | 実装完了後の振り返り。dev:feedbackスキルを起動してDESIGN.md更新と改善提案 |

## Development Workflow

### Story-Driven Development Flow

```
1. Worktree作成
   └── git worktree add -b feature/xxx

2. /dev:story 実行
   └── ストーリー入力 → TODO.md生成（TDD/PLANラベル付き）

3. dev:developing でタスク実行
   ├── [TDD] RED → GREEN → REFACTOR → REVIEW → CHECK → COMMIT
   └── [PLAN] UI実装 → agent-browser検証 → 品質チェック → COMMIT

4. /dev:feedback 実行
   └── DESIGN.md更新 → パターン検出 → スキル/ルール改善提案

5. PR作成 & マージ
```

### Key Concepts

- **TDD判定**: ビジネスロジック、API、データ処理 → 自動テスト可能
- **PLAN判定**: UI/UX、視覚的要素、ユーザー操作フロー → agent-browser検証
- **DESIGN.md**: 機能別仕様書。実装で得た知見を蓄積
- **フィードバックループ**: 3回以上同じパターンが現れたらスキル/ルール化を検討
