---
name: dev:update-plan
description: |
  docs/PLAN 配下の tasks.json (v2) をダッシュボード互換フォーマットで安全に更新する。
  spec-run を経由しない部分的な変更（レビュー完了、ステータス変更等）に使う。
  更新後は自動的に validate + simulate + sync で整合性を保証する。

  Trigger: プランを更新, 計画書のステータス変更, レビュー完了にする, /dev:update-plan
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

# update-plan — 計画書の安全更新（v2）

`docs/PLAN` 配下の `tasks.json` (schemaVersion 2) を
ダッシュボード互換フォーマットで安全に更新するスキル。

**spec-run を経由しない部分的な変更**に使う。例:
- レビューが完了したので `reviewChecked: true` にしたい
- 特定の Todo の Review 結果を PASSED にしたい
- 特定の Step の `checked` を切り替えたい

更新後は必ず整合性チェック・spec.md 同期を行うため、
ダッシュボード表示が壊れることを防ぐ。

**v1 (spec.md マークダウンパース) は対象外。**

## トリガー

- `/dev:update-plan`
- 「プランを更新」「計画書のステータス変更」「レビュー完了にする」

## 参照ソース

更新の正として以下を参照する:

- `.claude/skills/dev/spec-run/SKILL.md` — status / progress の算出ルール
- `dashboard/lib/types.ts` — TasksJsonV2 型定義
- `.claude/skills/dev/spec/references/templates/tasks.template.json` — v2 テンプレート

## 実行フロー

### Step 1: 対象プランの特定

1. ユーザーがパスを指定している場合 → そのプラン
2. 指定がない場合 → `docs/PLAN/*/tasks.json` を Glob で一覧し、AskUserQuestion で対象を選択

### Step 2: 現在の tasks.json を Read

対象の `tasks.json` を全体 Read する。
合わせて `spec.md` も Read する（generated 領域とレビューステータスセクションの確認用）。

### Step 3: 更新内容の解釈

ユーザーの指示を解釈し、tasks.json に対する変更を特定する。
以下の操作パターンを認識する:

#### パターン一覧

| パターン | 変更内容 | 例 |
| --- | --- | --- |
| **Review 結果の記入** | `todos[].steps` の review step に `review: {result, fixCount, summary}` を設定 + `checked: true` | 「A1 のレビューを PASSED にして」 |
| **Step の checked 切り替え** | `todos[].steps[].checked` を `true/false` に設定 | 「B2 の IMPL を完了にして」 |
| **レビュー完了** | `reviewChecked: true` + spec.md のチェックボックスを `[x]` に | 「レビュー完了にして」 |
| **ステータス変更** | `status` の直接指定（非推奨・通常は自動算出） | 「ステータスを in-progress に」 |

#### 解釈時のルール

- **Todo ID (A1, B2 等) で対象を特定**する。title の部分一致は不可
- review step の更新時は、**必ず同一 Todo の impl step も `checked: true` であること**を確認する。
  impl が未完了なのに review を記入するのは不整合なので、AskUserQuestion で確認する
- `status` と `progress` は **自動算出** する。ユーザーが直接指定することはできない（Step 5 で再計算）

### Step 4: 変更の適用

Edit ツールで tasks.json に変更を適用する。

**Review 結果の記入例:**

変更前:
```json
{ "kind": "review", "title": "Step 2 — Review", "checked": false, "review": null }
```

変更後:
```json
{ "kind": "review", "title": "Step 2 — Review", "checked": true, "review": { "result": "PASSED", "fixCount": 0, "summary": "LGTM" } }
```

### Step 5: 整合性の再計算

変更適用後、status / progress を再計算して tasks.json に反映する。
算出ルールは spec-run SKILL.md と同じ:

```
total     = sum of all todos[].steps[].length
completed = count of all steps where checked == true
progress  = { completed, total }

status:
  - completed == 0                               → "not-started"
  - 0 < completed < total                        → "in-progress"
  - completed == total && reviewChecked == false → "in-review"
  - completed == total && reviewChecked == true  → "completed"
```

**fix-tasks-json スクリプトを使用:**

```bash
node .claude/skills/dev/fix-plan/scripts/fix-tasks-json.mjs docs/PLAN/{対象}/tasks.json
```

### Step 6: spec.md の同期

#### 6a: generated 領域の再同期

```bash
node .claude/skills/dev/spec-run/scripts/sync-spec-md.mjs docs/PLAN/{対象}/tasks.json
```

#### 6b: レビューステータスセクションの更新

`reviewChecked` が `true` になった場合、spec.md のレビュー完了チェックボックスを更新:

```
- [ ] **レビュー完了**  →  - [x] **レビュー完了**
```

`reviewChecked` が `false` に戻った場合は逆:
```
- [x] **レビュー完了**  →  - [ ] **レビュー完了**
```

### Step 7: 検証

更新後の整合性を検証:

```bash
# 構造 + 整合性チェック
node .claude/skills/dev/fix-plan/scripts/validate-tasks-json.mjs docs/PLAN/{対象}/tasks.json

# ダッシュボードと同じパース処理のローカル確認
npx tsx .claude/skills/dev/fix-plan/scripts/simulate-dashboard-parse.mjs docs/PLAN/{対象}
```

両方が PASS であることを確認する。

### Step 8: 結果の報告

```
✅ 更新完了: docs/PLAN/{対象}

変更内容:
- Todo {id} Review: PASSED (fixCount: 0, summary: "...")
- progress: {old} → {new}
- status: "{old}" → "{new}"
- spec.md generated 領域を再同期
- spec.md レビューチェックボックスを [x] に更新

validate: 20/20 PASS
simulate: エラーなし
```
