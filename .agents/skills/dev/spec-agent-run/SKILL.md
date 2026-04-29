---
name: spec-agent-run
description: Execute docs/PLAN/{YYMMDD}_{slug}/ schema v3 specs gate by gate, with optional git worktree isolation, AC-based verification, tasks.json state updates, and spec.md synchronization. Trigger: spec-run, 仕様書を実行, 計画書の実行, docs/PLAN の実装
---

# spec-agent-run

`docs/PLAN/{YYMMDD}_{slug}/` の schema v3 仕様書を Gate 単位で実行する。Acceptance Criteria を満たしたことを確認してから `tasks.json` と `spec.md` を更新する。

## Core Rules

- 対象は `tasks.json` の `schemaVersion === 3` のみ。
- 実装手順は `spec.md` ではなく `tasks.json.gates[]` の Gate 契約を正とする。
- Gate は依存順に 1 つずつ通す。未通過依存がある Gate には着手しない。
- `tasks.json` を更新したら、必ず `scripts/sync-spec-md.mjs` を実行する。
- ユーザー未指定なら、開始前に worktree を使うか確認する。推奨は「使わない」。

## Start Flow

### 1. Locate Spec

会話から対象 `docs/PLAN/{YYMMDD}_{slug}/spec.md` が明確ならそれを使う。不明なら:

1. `docs/PLAN/*/spec.md` を検索し、更新日順で上位 5 件を出す。
2. ユーザーに対象を確認する。
3. 同じディレクトリの `tasks.json` を対象 state file とする。

### 2. Validate State

`tasks.json` を読み、以下を確認する:

- `schemaVersion === 3`
- `gates[]` が配列
- `status` / `reviewChecked`
- `preflight[]` があれば各項目の `checked`

v3 でない、または `tasks.json` が存在しない場合は中断して理由を報告する。

### 3. Worktree Choice

ユーザーが明示していない場合は「worktree を使うか」を確認する。

- 使わない: 現在の cwd で直接作業する。
- 使う: [worktree-setup.md](references/worktree-setup.md) を読んでセットアップしてから Gate 実行へ進む。

worktree を使う場合、以後の読み書き、検証、コミットは worktree 内で行う。

### 4. Load Context

`spec.md` と `tasks.json` を読み、`spec.md` の「参照すべきファイル」に外部同梱資料があれば先に読む。コードベース内ファイルは Gate の `constraints` と `affectedFiles` に従って必要時に読む。

## Execution Loop

### Preflight

`preflight[]` が存在し、未チェック項目がある場合のみ実行する。

- `manual: false`: `command` を実行し、`ac` を確認する。
- `manual: true`: ユーザーに作業完了を確認し、`ac` を確認する。
- 成立した項目だけ `checked: true` にする。

Preflight 更新後は `tasks.json` を保存し、すぐ `node .agents/skills/dev/spec-agent-run/scripts/sync-spec-md.mjs <tasks-json-path>` を実行する。

### Gate Implementation

各 Gate について:

1. `dependencies` の Gate がすべて `passed: true` であることを確認する。
2. `goal`, `constraints`, `acceptanceCriteria`, `todos`, `affectedFiles` を読んで実装する。
3. `tdd: true` の Todo がある場合は、先に失敗するテストまたは検証を置けるか判断し、置ける場合は TDD で進める。
4. `[SIMPLE]` Todo は過剰な設計を避け、局所変更として処理する。
5. ユーザー確認が必要な仕様の曖昧さが出た場合だけ止めて確認する。

### Verification

Gate の Acceptance Criteria を 1 件ずつ検証する。コマンド、テスト、HTTP、ブラウザ確認、ファイル確認など、AC に書かれた方法を優先する。

レビュー判定:

- docs/config/comment only や `[SIMPLE]` 専用 Gate: `review.result = "SKIPPED"` でよい。
- 通常のコード変更: diff を読み、仕様適合、破壊的変更、テスト不足、既存パターン違反を自己レビューする。
- 高リスク変更で `codex review` が利用可能なら追加で使ってよい。ただし必須ではない。

未達 AC またはレビュー上の blocker があれば、同じ Gate 内で修正して再検証する。3 ラウンドで解消しなければ状況を報告してユーザー判断を仰ぐ。

### Update State

Gate が通ったら `tasks.json` だけを更新する。`spec.md` の generated 領域は直接編集しない。

更新対象:

- 該当 Gate の `acceptanceCriteria[].checked = true`
- 該当 Gate の `review = { result, fixCount, summary }`
- 該当 Gate の `passed = true`
- トップレベル `status`

`status` 算出:

```text
gates.length == 0                                                    -> not-started
passed が 0 件、かつ全 AC が未 checked                               -> not-started
0 < passed < gates.length                                             -> in-progress
passed == gates.length && !reviewChecked                              -> in-review
passed == gates.length && reviewChecked                               -> completed
```

更新後に必ず同期する:

```bash
node .agents/skills/dev/spec-agent-run/scripts/sync-spec-md.mjs docs/PLAN/{YYMMDD}_{slug}/tasks.json
```

## Completion

全 Gate の `passed === true` を確認したら:

1. `status` が `in-review` になっていることを確認する。
2. 未コミット変更があれば、ユーザーの意図と変更範囲に沿ってコミットする。
3. worktree を使っている場合は、ユーザーに「先にマージ」か「レビュー後にマージ」か確認する。
4. マージする場合は [worktree-teardown.md](references/worktree-teardown.md) を読んで実行する。
5. `spec.md` に未チェックの `レビュー完了` があり、ユーザーが確認済みなら `spec.md` の authored 領域と `tasks.json.reviewChecked` を更新し、再同期する。

## References

- [worktree-setup.md](references/worktree-setup.md) - optional worktree setup
- [worktree-teardown.md](references/worktree-teardown.md) - optional merge and cleanup
- [scripts/sync-spec-md.mjs](scripts/sync-spec-md.mjs) - regenerate `spec.md` generated section from `tasks.json`
- [scripts/setup-worktree.sh](scripts/setup-worktree.sh) - create or reuse `.worktrees/{slug}`
- [scripts/cleanup-worktree.sh](scripts/cleanup-worktree.sh) - remove merged worktree and feature branch
