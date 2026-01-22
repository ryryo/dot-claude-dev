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
      { label: "feature/{story-slug}", description: "Worktree: ../feature/{story-slug}/ に作成" },
      { label: "fix/{story-slug}", description: "Worktree: ../fix/{story-slug}/ に作成" }
    ],
    multiSelect: false
  }]
})

// Worktree作成
Bash({
  command: "git worktree add -b {branch-name} ../{branch-name}",
  description: "Worktreeを作成"
})
```

**作成後**:
- 新しいWorktreeディレクトリに移動して作業を継続
- ユーザーに新しいパスを通知

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
[3/3] コミット
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

---

## TDDワークフロー

`[TDD]` ラベル付きタスクに適用。RED→GREEN→REFACTORサイクルを厳格に遵守。

```
[1/6] テスト作成（RED）
    → agents/tdd-write-test.md [sonnet]
    → テスト実行して失敗を確認
    → コミット（テストのみ）
        ↓
[2/6] 実装（GREEN）
    → agents/tdd-implement.md [sonnet]
    → テスト実行して成功を確認
    → ⚠️ テストは絶対に変更しない（仕様のブレ防止）
    → 通常2〜4周で収束
        ↓
[3/6] リファクタリング
    → agents/tdd-refactor.md [opus]
    → テスト実行して成功を確認
        ↓
[4/6] セルフレビュー【過剰適合・抜け道チェック】
    → 「この実装、テストに過剰適合してない？抜け道ない？」
    → 過剰適合: テストケースだけに最適化されていないか
    → 抜け道: テストをすり抜ける不具合・エッジケースがないか
    → 問題あれば[2/6]に戻って修正
        ↓
[5/6] 品質チェック
    → lint/format/build
        ↓
[6/6] コミット
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
// [GREEN] 実装
Task({
  description: "実装",
  prompt: `テストを通す最小限の実装を行ってください。
タスク: {task_name}

重要:
- テストは変更しない
- 最小限の実装のみ
- 将来の要件を先取りしない`,
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
// [REVIEW] セルフレビュー（過剰適合・抜け道チェック）
Task({
  description: "セルフレビュー",
  prompt: `実装をレビューしてください。
対象: {task_name}

チェックリスト:
1. 過剰適合チェック:
   - テストケースだけに最適化された実装になっていないか？
   - テスト以外のケースでも正しく動作するか？

2. 抜け道チェック:
   - テストをすり抜ける不具合やエッジケースがないか？
   - 境界値、null/undefined、空配列などを考慮したか？

3. コード品質:
   - 読みやすく保守しやすいか？
   - プロジェクト規約に準拠しているか？

問題があれば指摘し、修正案を提示してください。`,
  subagent_type: "general-purpose",
  model: "opus"
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
[4/4] コミット
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

---

## テスト実行（サブエージェント）

トークン消費を抑えるため、テスト実行はサブエージェントに委譲。

```javascript
Task({
  description: "テスト実行",
  prompt: `プロジェクトのテストを実行し、結果を報告してください。

テストコマンド: npm test / cargo test / pytest など

報告形式:
- 全テスト成功: "SUCCESS: X tests passed"
- 失敗あり: "FAILED:" + 失敗したテスト名とエラーのみ`,
  subagent_type: "general-purpose",
  model: "haiku"
})
```

---

## セルフレビュー

フェーズ完了時にコード品質をチェック。

```javascript
Task({
  description: "セルフレビュー",
  prompt: `変更されたファイルをレビューしてください。

レビュー観点:
1. TDD/テスト品質
2. コード品質（可読性、命名、複雑度）
3. セキュリティ
4. 設計原則

報告形式:
- 問題なし: "PASSED"
- 問題あり: "ISSUES:" + Critical/Warningのみ`,
  subagent_type: "Explore",
  model: "opus"
})
```

---

## 品質チェック

```bash
npm run lint && npm run format && npm run build
# または
cargo clippy && cargo fmt && cargo build
# または
flake8 && black . && pytest
```

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
