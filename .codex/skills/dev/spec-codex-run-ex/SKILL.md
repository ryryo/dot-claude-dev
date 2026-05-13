---
name: dev:spec-codex-run
description: |
  docs/PLAN/{YYMMDD}_{slug}/ の schema v3 仕様書を Codex で Gate 単位に実行します。
  Gate 契約 (Goal/Constraints/AC) に基づいて実装し、Acceptance Criteria、
  Codex review、必要に応じた Cursor Agent 委任により tasks.json と spec.md を更新します。

  Trigger:
  spec-codex-run, spec-run, 仕様書を実行, 計画書の実行, docs/PLAN の実装
user-invocable: true
---

# spec-codex-run

`docs/PLAN/{YYMMDD}_{slug}/` の schema v3 仕様書を Codex で実行する。`tasks.json.gates[]` の Gate 契約を正とし、`spec.md` は背景と generated summary として扱う。既存 v3 PLAN は optional Codex 拡張がなくても実行できる。

## 起動フロー

### 1. 仕様書の特定

対象が会話の文脈から明確な場合はその PLAN を使う。不明なら:

1. `docs/PLAN/*/tasks.json` を検索し、更新日順で上位 5 件を提示する。
2. ユーザーに対象を確認する。
3. 同じディレクトリの `spec.md` を補助文書として読む。

### 2. schemaVersion 検証

`tasks.json` を読み、以下を確認する。

- `schemaVersion === 3`
- `gates[]` が配列
- `status` / `reviewChecked`
- `preflight[]` があれば各項目の `checked`

v3 でない、または `tasks.json` が存在しない場合は中断して理由を報告する。

### 3. 実行準備

`spec.md` と `tasks.json` を読み、以下を把握する。

- `gates[]` 全体: `id`, `title`, `kind`, `dependencies`, `goal`, `constraints`, `acceptanceCriteria`, `todos`, `review`, `passed`
- `todos[].delegation` があれば委任候補
- `extensions.codex.delegationPolicy` があれば Cursor Agent 方針
- `preflight[]`
- `spec.md` の参照資料

### 4. Cursor Agent 選択

Cursor Agent は都度選択とする。契約やログイン状態が変わるため、利用を前提にしない。

1. ユーザーが明示的に使わない場合は Codex 単独で進む。
2. 使う候補がある場合、次で利用可否を確認する。
   ```bash
   cursor-agent about
   cursor-agent models
   cursor-agent -p --mode ask --output-format text --workspace <workspace> "Respond with exactly: ok"
   ```
3. 未ログイン、契約なし、モデルなし、最小実行失敗なら Codex 単独へフォールバックする。
4. 使う場合も、`docs/PLAN` 更新、Gate PASS 判定、最終統合、commit/push は main Codex が保持する。

### 5. worktree 選択

ユーザーが明示していない場合は「worktree を使うか」を確認する。推奨は「使わない」。

- 使わない: 現在の cwd で直接作業する。
- 使う: [worktree-setup.md](references/worktree-setup.md) を読んでセットアップする。

worktree を使う場合、以後の読み書き、検証、コミットは worktree 内で行う。

## Gate 通過条件

Gate を `passed: true` にできるのは、次をすべて満たす場合だけ。

1. `dependencies` の全 Gate が `passed: true`。
2. 全 Acceptance Criteria が `checked: true`。
3. `review.result === "PASSED"`、または SKIPPED 適用条件を満たす。

未 passed dependency がある Gate は、AC と review が成立していても `passed: true` にしない。

## 実行プロトコル

### Preflight

`preflight[]` が存在し、未チェック項目がある場合のみ実行する。

1. `manual: false` は `command` を実行する。
2. `manual: true` はユーザーに作業完了を確認する。
3. 各項目の `ac` が成立しているか確認する。
4. 成立した項目だけ `preflight[].checked = true` にする。
5. 更新後、必ず `sync-spec-md.mjs` を実行する。

### Step 1 — IMPL

各 Gate について:

1. dependency の passed 状態を確認する。
2. Gate 契約を読む:
   - `goal.what` / `goal.why`
   - `constraints.must` / `constraints.mustNot`
   - `acceptanceCriteria[]`
   - `todos[]`
   - optional `kind` / `parallelizable` / `todos[].delegation`
3. `tdd: true` の Todo は、先に失敗するテストまたは検証を置けるか判断する。
4. `[SIMPLE]` Todo は過剰な設計を避け、局所変更として処理する。
5. Cursor Agent へ委任する場合は、`.codex/skills/dev/spec-codex/references/delegation-brief-template.md` の形式で詳細プロンプトを作り、write scope と禁止事項を必ず含める。
6. ユーザー確認が必要な仕様の曖昧さが出た場合だけ止めて確認する。

### Step 2 — VERIFY

#### AC 検証

- Gate の AC を 1 件ずつ検証する。
- コマンド、テスト、HTTP、ブラウザ確認、ファイル確認、モック検証など、AC の成立を確認できる手段を使う。
- AC に明示された検証手段を優先する。
- 同等検証で代替した場合は `review.summary` に検証範囲を明記する。
- 同等検証で代替できない AC は未チェックのまま残す。

#### Review 判定

- docs/config/comment only や `[SIMPLE]` 専用 Gate は `review.result = "SKIPPED"` でよい。
- 通常のコード変更は Codex review を使う。
- Gate 中レビュー: `codex review --uncommitted -`
  - 標準入力に Gate id、仕様ファイルパス、Goal、Constraints、AC、対象ファイル、除外したい無関係差分を含める。
- 最終レビュー: `codex review --base <base>`
  - 複数 Gate をまとめて確認する。
- コミット単位レビュー: `codex review --commit <sha>`
  - 必要なら Gate 契約を標準入力で補足する。
- P1 / blocker は FAIL。P2 は内容を精査して PASS / FAIL を判断する。コメントなし、または P3 のみなら PASS としてよい。
- `codex review` が使えない場合は自己レビューし、`review.summary` に `codex review unavailable` と明記する。

### Step 3 — FIX

FAIL の場合のみ同じ Gate 内で修正して再 VERIFY する。3 ラウンドで解消しなければ状況を報告してユーザー判断を仰ぐ。

実行中に新しい作業 Gate が必要になった場合:

- 初期設計の漏れや追加調査は `kind: "follow-up"`。
- review 由来の差分対応は `kind: "review-fix"`。
- 実機確認や最終検証は `kind: "verification"`。
- 追加 Gate も依存関係と AC を持たせ、`status` を再計算する。

### Step 4 — UPDATE

`tasks.json` のみを更新する。`spec.md` の generated 領域は直接編集しない。

更新対象:

1. 成立した `acceptanceCriteria[].checked = true`
2. 該当 Gate の `review = { result, fixCount, summary }`
3. Gate 通過条件を満たす場合のみ `passed = true`
4. トップレベル `status`

更新後に必ず同期する。

```bash
node .codex/skills/dev/spec-codex-run/scripts/sync-spec-md.mjs docs/PLAN/{YYMMDD}_{slug}/tasks.json
```

## status の算出ルール

```text
gates.length == 0                                                            -> not-started
passed が 0 件、かつ全 AC が未 checked、かつ review/preflight 進捗もない     -> not-started
いずれかの AC が checked、review が記録済み、または 0 < passed < gates.length -> in-progress
passed == gates.length && !reviewChecked                                      -> in-review
passed == gates.length && reviewChecked                                       -> completed
```

## 完了処理

全 Gate の `passed === true` を確認したら:

1. `status` が `in-review` になっていることを確認する。
2. 未コミット変更があれば、ユーザーの意図と変更範囲に沿ってコミットする。
3. worktree を使っている場合は、ユーザーに「先にマージ」か「レビュー後にマージ」か確認する。
4. マージする場合は [worktree-teardown.md](references/worktree-teardown.md) を読んで実行する。
5. `spec.md` に未チェックの `レビュー完了` があり、ユーザーが確認済みなら authored 領域と `tasks.json.reviewChecked` を更新し、再同期する。

## 参照

- [worktree-setup.md](references/worktree-setup.md)
- [worktree-teardown.md](references/worktree-teardown.md)
- [scripts/sync-spec-md.mjs](scripts/sync-spec-md.mjs)
- [scripts/setup-worktree.sh](scripts/setup-worktree.sh)
- [scripts/cleanup-worktree.sh](scripts/cleanup-worktree.sh)
- `.codex/skills/dev/spec-codex/references/cursor-delegation-protocol.md`
- `.codex/skills/dev/spec-codex/references/delegation-brief-template.md`
