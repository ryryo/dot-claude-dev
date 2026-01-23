---
name: dev:developing
description: |
  TODO.mdのタスクを実行。TDD/E2E/TASKラベルに応じたワークフローで実装。
  Worktree内での独立した開発を支援。

  Trigger:
  dev:developing, /dev:developing, 実装, 開発, implementing, develop
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Task
  - AskUserQuestion
---

# 実装（dev:developing）

## 概要

TODO.mdのタスクを実行する。タスクのラベルに応じてTDDまたはE2Eワークフローを適用。

## 入力

- `docs/features/{feature-slug}/stories/{story-slug}/TODO.md`
- feature-slug, story-slug

## 出力

- 実装コード
- テストコード（TDDタスク）
- コミット

---

## Phase 0: ブランチ/Worktree チェック

実装開始前に、作業ブランチの状態を確認する。

```
現在のブランチを確認
    ├─ master/main → Worktree作成を促す
    └─ feature/* 等 → そのまま続行
```

### 0.1 ブランチ確認

```bash
git branch --show-current
```

### 0.2 master/main の場合: Worktree作成

```javascript
AskUserQuestion({
  questions: [{
    question: "現在 master/main ブランチです。Worktreeを作成しますか？",
    header: "Worktree",
    options: [
      { label: "作成する（推奨）", description: "Worktree（別ディレクトリ）で独立した開発環境を作成" },
      { label: "このまま続行", description: "master/main で直接作業（非推奨）" }
    ],
    multiSelect: false
  }]
})
```

**「作成する」を選択された場合**:

```javascript
// Worktreeのブランチ名をユーザーに確認
AskUserQuestion({
  questions: [{
    question: "Worktreeのブランチ名を入力してください（例: feature/user-auth）",
    header: "Worktree名",
    options: [
      { label: "feature/{story-slug}", description: "ストーリー名から機能ブランチを作成" },
      { label: "fix/{story-slug}", description: "ストーリー名から修正ブランチを作成" }
    ],
    multiSelect: false
  }]
})

// Worktree作成
// 配置: ../.worktrees/{project}/{branch}
// 例: ../.worktrees/dot-claude-dev/feature-user-auth
Bash({
  command: `
PROJECT_NAME=$(basename $(pwd))
BRANCH_NAME="{branch-name}"
WORKTREE_DIR="../.worktrees/$PROJECT_NAME/${BRANCH_NAME//\//-}"
mkdir -p $(dirname "$WORKTREE_DIR")
git worktree add -b "$BRANCH_NAME" "$WORKTREE_DIR"
`,
  description: "Worktreeを作成"
})
```

**作成後**:
- 新しいWorktreeディレクトリ（`../.worktrees/{project}/{branch}/`）に移動して作業を継続
- ユーザーに新しいパスを通知
- 例: `cd ../.worktrees/dot-claude-dev/feature-user-auth`

---

## ワークフロー分岐

```
TODO.mdを読み込み
    ↓
タスクのラベルを確認
    ├─ [TASK] → TASKワークフロー
    ├─ [TDD] → TDDワークフロー
    └─ [E2E] → E2Eワークフロー
```

**実行順序**: TASKタスクは通常、最初に実行（環境構築が必要なため）

---

## TASKワークフロー

`[TASK]` ラベル付きタスクに適用。設定/セットアップ/インフラ構築を実行。

```
[1/3] 実行（EXEC）
    → agents/task-execute.md [sonnet]
    → 設定ファイル作成、コマンド実行
        ↓
[2/3] 検証（VERIFY）
    → ファイル存在確認、ビルド確認
        ↓
[3/3] コミット（COMMIT）
    → agents/simple-add.md [haiku]
    → 軽量・高速なサブエージェントで実行
```

→ 詳細: [references/task-flow.md]

### TASKタスク実行

```javascript
// [EXEC] タスク実行
Task({
  description: "TASKタスク実行",
  prompt: `以下のTASKタスクを実行してください。
タスク: {task_name}
説明: {task_description}

1. 必要な設定ファイルを作成/編集
2. 必要なコマンドを実行
3. 結果を報告`,
  subagent_type: "general-purpose",
  model: "sonnet"
})
```

```javascript
// [VERIFY] 検証
Task({
  description: "TASK検証",
  prompt: `以下のTASKタスクの検証を行ってください。
タスク: {task_name}

検証内容:
- ファイル存在確認
- ビルド/コンパイル確認
- サービス起動確認（該当する場合）`,
  subagent_type: "general-purpose",
  model: "haiku"
})
```

```javascript
// [COMMIT] コミット
Task({
  description: "コミット",
  prompt: `変更をコミットしてください。
対象: {task_name}

変更内容:
- 設定ファイル
- インフラ構築結果

simple-addエージェントを使用して、適切なコミットメッセージで変更をコミットしてください。`,
  subagent_type: "simple-add",
  model: "haiku"
})
```

---

## TDDワークフロー

`[TDD]` ラベル付きタスクに適用。RED→GREEN→REFACTOR→SIMPLIFY→REVIEWサイクルを厳格に遵守。

```
[1/8] テスト作成（RED）
    → agents/tdd-write-test.md [sonnet]
    → テスト実行して失敗を確認
    → コミット（テストのみ）
        ↓
[2/8] 実装（GREEN）
    → agents/tdd-implement.md [sonnet]
    → テスト実行して成功を確認
    → ⚠️ テストは絶対に変更しない（仕様のブレ防止）
    → 通常2〜4周で収束
        ↓
[3/8] リファクタリング（REFACTOR）
    → agents/tdd-refactor.md [opus]
    → 構造的改善（単一責任、重複排除、複雑度低減）
    → テスト実行して成功を確認
        ↓
[4/8] コード整理（SIMPLIFY）
    → code-simplifierエージェント [sonnet]
    → 明瞭性・一貫性・保守性の向上
    → テスト実行して成功を確認
        ↓
[5/8] セルフレビュー（REVIEW）【過剰適合・抜け道チェック】
    → 「この実装、テストに過剰適合してない？抜け道ない？」
    → 過剰適合: テストケースだけに最適化されていないか
    → 抜け道: テストをすり抜ける不具合・エッジケースがないか
    → 問題あれば[2/8]に戻って修正
        ↓
[6/8] 品質チェック（CHECK）
    → lint/format/build
        ↓
[7/8] テスト資産の管理
    → テストコードの長期的価値を評価
    → 長期保持 or 簡素化/削除を判断
    → メンテナンスコスト最小化
        ↓
[8/8] コミット（COMMIT）
    → agents/simple-add.md [haiku]
    → 実装とテスト資産管理の結果をコミット
    → 軽量・高速なサブエージェントで実行
```

→ 詳細: [references/tdd-flow.md]

### TDDタスク実行

```javascript
// [RED] テスト作成
Task({
  description: "テスト作成",
  prompt: `以下のタスクのテストを作成してください。
タスク: {task_name}
説明: {task_description}
入力: {input}
出力: {output}

テストのみ作成し、実装は書かないでください。
テストを実行して失敗することを確認してください。`,
  subagent_type: "general-purpose",
  model: "sonnet"
})
```

```javascript
// [GREEN] 実装（t_wada式TDD: YAGNI・Baby steps）
Task({
  description: "実装",
  prompt: `【YAGNI・Baby steps】今あるテストを通すためだけのコードを書いてください。

タスク: {task_name}

## 実装戦略（順に検討）

1. **仮実装（Fake It）**: まずハードコードで通す
   - 例: return "expected_value" でテストを通す
   - 最速でグリーンにする

2. **三角測量**: テストが2つ以上あれば一般化を検討
   - 複数のテストを通すために必要な最小の一般化のみ

3. **明白な実装**: 自明な場合のみ直接実装
   - 迷ったら仮実装から始める

## 禁止事項（YAGNI）

- ❌ テストを変更しない
- ❌ 将来必要「かもしれない」コードを書かない
- ❌ 今のテストに関係ない機能を追加しない
- ❌ 「ついでに」のリファクタリング（REFACTORフェーズで行う）

## 合言葉

「今のテストを通す → 次のテストを追加 → また通す」
このサイクルを小さく回す。`,
  subagent_type: "general-purpose",
  model: "sonnet"
})
```

```javascript
// [REFACTOR] リファクタリング
Task({
  description: "リファクタリング",
  prompt: `コード品質を改善してください。
対象: {task_name}

チェックリスト:
- 単一責任原則
- 重複排除
- 命名改善
- 複雑度低減

重要: テストが成功し続けることを確認`,
  subagent_type: "general-purpose",
  model: "opus"
})
```

```javascript
// [SIMPLIFY] コード整理
Task({
  description: "コード整理",
  prompt: `code-simplifierエージェントを使ってコードを整理してください。
対象: {task_name}

明瞭性・一貫性・保守性を向上させます。
リファクタリング完了後のコード整理として実行。

重要: テストが成功し続けることを確認`,
  subagent_type: "code-simplifier",
  model: "sonnet"
})
```

```javascript
// [REVIEW] セルフレビュー（過剰適合・抜け道チェック）
Task({
  description: "セルフレビュー",
  prompt: `実装をレビューしてください。
対象: {task_name}

実装ファイル: {implementation_file}
テストファイル: {test_file}

過剰適合・抜け道チェックを実施してください。`,
  subagent_type: "tdd-review",
  model: "opus"
})
```

```javascript
// [CHECK] 品質チェック
Task({
  description: "品質チェック",
  prompt: `品質チェック（lint/format/build）を実行してください。

結果を簡潔に報告してください。`,
  subagent_type: "quality-check",
  model: "haiku"
})
```

```javascript
// [MANAGE] テスト資産の管理
Task({
  description: "テスト資産の管理",
  prompt: `以下のテストファイルを評価してください。

対象テストファイル: {test_file}
実装ファイル: {implementation_file}

長期的価値を評価し、保持/簡素化/削除を判断してください。`,
  subagent_type: "test-asset-management",
  model: "sonnet"
})
```

```javascript
// [COMMIT] コミット
Task({
  description: "コミット",
  prompt: `変更をコミットしてください。
対象: {task_name}

変更内容:
- 実装コード
- リファクタリング結果
- コード整理結果
- テスト資産管理の結果

simple-addエージェントを使用して、適切なコミットメッセージで変更をコミットしてください。`,
  subagent_type: "simple-add",
  model: "haiku"
})
```

---

## E2Eワークフロー

`[E2E]` ラベル付きタスクに適用。agent-browserで操作フロー検証。

```
[1/4] UI実装
    → agents/e2e-implement.md [sonnet]
    → コンポーネント作成
        ↓
[2/4] agent-browser検証（ループ）
    → agents/e2e-verify.md [haiku]
    → 操作フロー検証
    → 問題あれば修正→再検証
        ↓
[3/4] 品質チェック
    → lint/format/build
        ↓
[4/4] コミット（COMMIT）
    → agents/simple-add.md [haiku]
    → 軽量・高速なサブエージェントで実行
```

→ 詳細: [references/e2e-flow.md]

### E2Eタスク実行

```javascript
// [IMPL] UI実装
Task({
  description: "UI実装",
  prompt: `UIコンポーネントを実装してください。
タスク: {task_name}
説明: {task_description}

コンポーネント設計:
- Props定義
- イベントハンドラ
- スタイリング`,
  subagent_type: "general-purpose",
  model: "sonnet"
})
```

```javascript
// [AUTO] agent-browser検証
Task({
  description: "agent-browser検証",
  prompt: `MCP agent-browserで操作フローを検証してください。

検証手順:
1. tabs_context_mcp でタブ情報取得
2. tabs_create_mcp で新規タブ作成
3. navigate で開発サーバーに遷移
4. find で要素検索
5. computer/form_input で操作実行
6. read_page で結果確認
7. スクリーンショット取得

期待する動作:
{expected_behavior}`,
  subagent_type: "general-purpose",
  model: "haiku"
})
```

```javascript
// [COMMIT] コミット
Task({
  description: "コミット",
  prompt: `変更をコミットしてください。
対象: {task_name}

変更内容:
- UIコンポーネント実装
- agent-browser検証結果

simple-addエージェントを使用して、適切なコミットメッセージで変更をコミットしてください。`,
  subagent_type: "simple-add",
  model: "haiku"
})
```

---

## 共通サブエージェント

TDD/E2E/TASKワークフローで共通して使用するサブエージェント：

### test-runner (haiku)
- **用途**: テスト実行と結果報告
- **使用場面**: RED/GREEN/REFACTOR/SIMPLIFYの各ステップ
- **効果**: トークン消費を抑え、高速にテスト結果を取得

### quality-check (haiku)
- **用途**: lint/format/build実行
- **使用場面**: TDD/E2E/TASKの品質チェックステップ
- **効果**: 自動修正と簡潔な報告で効率化

### test-asset-management (sonnet)
- **用途**: テスト資産の長期価値評価
- **使用場面**: TDDのMANAGEステップ
- **効果**: メンテナンスコスト最小化

### tdd-review (opus)
- **用途**: 過剰適合・抜け道チェック
- **使用場面**: TDDのREVIEWステップ
- **効果**: 高品質な実装を保証

### simple-add (haiku)
- **用途**: Git commit自動化
- **使用場面**: 全ワークフローのCOMMITステップ
- **効果**: 軽量・高速なコミット処理

---

## TODO.md更新

タスク完了時にTODO.mdを更新:

```javascript
Edit({
  file_path: "docs/features/{feature-slug}/stories/{story-slug}/TODO.md",
  old_string: "- [ ] [TDD][GREEN] validateEmail の実装",
  new_string: "- [x] [TDD][GREEN] validateEmail の実装"
})
```

---

## フェーズ完了確認

```javascript
AskUserQuestion({
  questions: [{
    question: "フェーズが完了しました。次のフェーズに進みますか？",
    header: "フェーズ完了",
    options: [
      { label: "承認", description: "次のフェーズに進む" }
    ],
    multiSelect: false
  }]
})
```

---

## 完了条件

- [ ] すべてのTASKタスクが完了（EXEC→VERIFY）
- [ ] すべてのTDDタスクが完了（RED→GREEN→REFACTOR）
- [ ] すべてのE2Eタスクが完了（IMPL→AUTO）
- [ ] 全テストが成功
- [ ] 品質チェックが通過
- [ ] TODO.mdが全て完了マーク

## 関連スキル

- **dev:story**: タスクリスト生成（TDD/E2E/TASK分類）
- **dev:feedback**: 実装後のフィードバック

## 参照ルール

- TDD/E2E/TASK分岐: `.claude/rules/workflow/workflow-branching.md`
- TDDワークフロー: `.claude/rules/workflow/tdd-workflow.md`
- E2Eサイクル: `.claude/rules/workflow/e2e-cycle.md`
