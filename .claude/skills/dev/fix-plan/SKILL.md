---
name: dev:fix-plan
description: |
  docs/PLAN 配下の計画書ファイル（tasks.json / spec.md）のフォーマット不整合や値の不備を検出・修正するスキル。
  AIの書き間違いで progress フィールドが文字列になっていたり、status が更新漏れしていたり、
  steps 構造が壊れていたりする問題を、テンプレートとパーサーを正として一括修復する。

  Trigger: 計画書が壊れた, プランの修正, 計画書のフォーマット直す, /dev:fix-plan, plan fix, plan broken
context: fork
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# fix-plan — 計画書ファイルのフォーマット修復

`docs/PLAN` 配下の計画書ファイル（`tasks.json` / `spec.md`）に生じた
フォーマット不整合や値の不備を検出・修正するスキル。

AI は様々な間違い方をする。本スキルは「特定のパターンだけ」を直すのではなく、
**テンプレートとパーサーの期待する構造を正** として現状を照合し、差分を修復する。

## トリガー

- `/dev:fix-plan`
- 「計画書が壊れた」「プランの修正」「計画書のフォーマット直す」
- ダッシュボードでプランのステータス・ステップ数・完了状態が正しく表示されないと気づいた時

## 正となる参照ソース

修復の正は以下の 3 つ。**必ず Read してから修復に取りかかること**。

| 参照ファイル | 役割 |
| --- | --- |
| `.claude/skills/dev/spec/references/templates/tasks.template.json` | tasks.json の完全なスキーマ (v2)。フィールド名・型・ネスト構造の正 |
| `dashboard/lib/types.ts` (`TasksJsonV2*` 型群) | ランタイムパーサーが期待する型定義。`progress` が `{completed, total}` の object であること等 |
| `.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs` | spec.md の generated 領域 (`<!-- generated:begin/end -->`) を tasks.json から再生成するスクリプト |

## 実行フロー

### Step 1: 対象プランの特定

1. ユーザーがパスを指定している場合 → そのプランを作業対象とする
2. 指定がない場合 → `docs/PLAN/*/tasks.json` を Glob で一覧し、AskUserQuestion で対象を選択

### Step 2: 正となる参照ソースを Read

上記 3 ファイルを必ず Read する。これにより Claude のコンテキストに「正しい構造」が載る。

### Step 3: 対象の tasks.json を診断

以下のチェック項目を順に検証する。**すべての結果をユーザーに報告してから修復に進む**。

#### A. 構造チェック（スキーマ適合性）

| # | チェック項目 | 期待値 | よくある崩れ方 |
|---|---|---|---|
| 1 | `schemaVersion` | `2` (number) | 欠落、文字列 `"2"` |
| 2 | トップレベルキー | `spec`, `status`, `reviewChecked`, `progress`, `preflight`, `gates`, `todos`, `metadata` がすべて存在 | キー欠落 |
| 3 | `progress` の型 | `{ completed: number, total: number }` (object) | `"20/20"` のような文字列、`{completed, total}` が number でない |
| 4 | `status` の値 | `"not-started"` \| `"in-progress"` \| `"in-review"` \| `"completed"` | 空文字、未定義値、更新漏れ |
| 5 | `reviewChecked` の型 | `boolean` | 文字列 `"true"`、欠落 |
| 6 | `spec` の必須フィールド | `slug`, `title`, `summary`, `createdDate`, `specPath` がすべて非空 | 空文字、欠落 |
| 7 | `preflight` の型 | 配列（要素なしでも `[]`） | `null`、欠落 |
| 8 | `gates` の各要素 | `id`, `title`, `description`, `dependencies` (配列), `passCondition` が存在 | フィールド欠落、dependencies が文字列 |
| 9 | `todos` の各要素 | `id`, `gate`, `title`, `description`, `tdd` (boolean), `dependencies` (配列), `affectedFiles` (配列), `impl` (非空文字列), `steps` (配列) が存在 | フィールド欠落、tdd が文字列、steps が空 |
| 10 | `todos[].steps` の各要素 | `kind` (`"impl"` \| `"review"`), `title` (非空), `checked` (boolean) が存在。review step には `review` フィールド (null or object) | kind 欠落、checked が文字列 |
| 11 | `metadata` | `createdAt`, `totalGates`, `totalTodos` が存在 | 欠落、totalGates/totalTodos が gates/todos の長さと不一致 |

#### B. 整合性チェック（値の正しさ）

| # | チェック項目 | 検証方法 |
|---|---|---|
| 12 | `progress.total` = 全 Todo の steps 総数 | `todos.reduce((sum, t) => sum + t.steps.length, 0)` と一致するか |
| 13 | `progress.completed` = 全 Todo の checked steps 総数 | `todos.reduce((sum, t) => sum + t.steps.filter(s => s.checked).length, 0)` と一致するか |
| 14 | `metadata.totalGates` = `gates.length` | 数値が一致するか |
| 15 | `metadata.totalTodos` = `todos.length` | 数値が一致するか |
| 16 | `status` の妥当性 | 全 step checked → `"completed"`、全 step unchecked → `"not-started"`、それ以外 → `"in-progress"` or `"in-review"` |
| 17 | `reviewChecked` の妥当性 | `status === "completed"` かつ spec.md のレビュー行が `[x]` なら `true`、それ以外は現状維持 |
| 18 | 全 Todo の `gate` 値が `gates[].id` に存在するか | 孤立した gate 参照がないか |
| 19 | 全 Todo の `dependencies` の ID が他 Todo の `id` に存在するか | 解決不能な依存がないか |

#### C. spec.md との同期チェック

| # | チェック項目 |
|---|---|
| 20 | `<!-- generated:begin -->` ... `<!-- generated:end -->` マーカーが存在するか |
| 21 | generated 領域の内容が tasks.json の現在値と一致するか（`sync-spec-md.mjs` を dry-run で比較） |

### Step 4: 診断結果の報告

以下の形式で全チェック結果をユーザーに提示する:

```
## 診断結果: docs/PLAN/260415_dashboard-claude-web-trigger

### 構造チェック
- ✅ #1 schemaVersion: 2
- ✅ #2 トップレベルキー: 全て存在
- ❌ #3 progress の型: "20/20" (string) → 期待: {completed, total} (object)
- ✅ #4 status: "in-progress" (※ただし整合性チェック #16 で要修正)
- ...

### 整合性チェック
- ❌ #12 progress.total: 記載 20, 実際 20 → OK
- ❌ #13 progress.completed: 記載 "20/20" は不正, 実際 20 → 修正必要
- ❌ #16 status: 記載 "in-progress", 全step完了している → "completed" にすべき
- ...

### 同期チェック
- ✅ #20 generated markers: 存在する
- ❌ #21 generated 領域: 不一致 (status更新後に要再同期)

### サマリー: 5件の問題を検出
```

### Step 5: 修復の実行

AskUserQuestion で「検出した問題をすべて修復してよいか」を確認。

承認されたら以下を実行:

1. **tasks.json の修復** — Edit で各問題を修正
   - 構造チェックの不備: テンプレートに合うようフィールド・型を修正
   - 整合性チェックの不備: `progress`, `metadata`, `status`, `reviewChecked` を実際の値から再計算して設定
2. **spec.md の再同期** — `sync-spec-md.mjs` を実行
   ```bash
   node .claude/skills/dev/spec-run/scripts/sync-spec-md.mjs docs/PLAN/{対象パス}/tasks.json
   ```
3. **spec.md レビューチェックボックス** — tasks.json の `reviewChecked` が `true` になった場合、spec.md 内の `- [ ] **レビュー完了**` を `- [x] **レビュー完了**` に更新（逆も同様）

### Step 6: 修復結果の確認

1. 修復後の tasks.json を再度 Read し、Step 3 の全チェックを再実行して問題ゼロであることを確認
2. 残存問題があれば追加で報告・修復
3. 最終サマリーを報告:

```
✅ 修復完了: docs/PLAN/260415_dashboard-claude-web-trigger

修正内容:
- progress: "20/20" (string) → {completed: 20, total: 20} (object)
- status: "in-progress" → "completed"
- reviewChecked: false → true
- spec.md generated 領域を再同期
- spec.md レビューチェックボックスを [x] に更新

全 21 チェック項目: PASS
```

## 典型的な崩れ方の例（あくまで一例）

以下はこれまでに観測されたパターン。本スキルはこれらに限定されず、テンプレートとの差分として包括的に修復する。

| パターン | 現象 | 根本原因 |
| --- | --- | --- |
| progress が文字列 | `"progress": "20/20"` | AI がテンプレートの `{completed, total}` を誤読して文字列で出力 |
| status 更新漏れ | 全タスク完了なのに `"status": "in-progress"` | spec-run の完了時に status を書き戻さなかった |
| reviewChecked 更新漏れ | レビュー済みなのに `false` | spec.md のチェックボックスと tasks.json が同期していない |
| steps 構造崩れ | `steps: []` または steps なし | 古いスキーマ (v1) から変換漏れ |
| progress 数値不一致 | `progress.total: 20` が実際は 16 steps | 手動で todo を追加・削除した後に progress を更新していない |
| metadata 不整合 | `totalTodos: 10` が実際は 8 | todo 追加・削除後に metadata を更新していない |

## 参照

- `.claude/skills/dev/spec/references/templates/tasks.template.json` — tasks.json v2 の正しいテンプレート
- `dashboard/lib/types.ts` — ランタイムが期待する `TasksJsonV2` 型定義
- `.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs` — spec.md generated 領域の再生成スクリプト
- `.claude/skills/dev/spec/SKILL.md` — 計画書作成スキル（フォーマットの一次情報源）
