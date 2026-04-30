---
name: dev:spec-agent-run
description: |
  docs/PLAN/{YYMMDD}_{slug}/ の schema v3 仕様書を Gate 単位で実行します。
  Gate 契約 (Goal/Constraints/AC) に基づいて実装し、
  Acceptance Criteria ベースで tasks.json と spec.md を更新します。

  Trigger:
  spec-run, 仕様書を実行, 計画書の実行, docs/PLAN の実装
user-invocable: true
---

# spec-agent-run

`docs/PLAN/{YYMMDD}_{slug}/` の schema v3 仕様書を Gate 単位で実行する。実装手順は `spec.md` ではなく `tasks.json.gates[]` の Gate 契約を正とし、AC が成立したことをもって完了を判定する。

## 起動フロー

### ステップ 1: 仕様書の特定

対象が会話の文脈から明確な場合はステップ 2 へ進む。不明なら:

1. `docs/PLAN/*/spec.md` を検索し、更新日順で上位 5 件を提示する
2. ユーザーに対象を確認する
3. 同じディレクトリの `tasks.json` を対象 state file とする

### ステップ 2: schemaVersion 検証

`tasks.json` を読み、以下を確認する:

- `schemaVersion === 3`
- `gates[]` が配列
- `status` / `reviewChecked`
- `preflight[]` があれば各項目の `checked`

v3 でない、または `tasks.json` が存在しない場合は中断して理由を報告する。

### ステップ 3: 実行準備

`spec.md` と `tasks.json` を読み、以下を把握する:

- `gates[]` 全体（id, title, dependencies, goal, constraints, acceptanceCriteria, todos, review, passed）
- `preflight[]`
- `status` / `reviewChecked`
- `spec.md` の「参照すべきファイル」

### ステップ 4: worktree 選択

ユーザーが明示していない場合は「worktree を使うか」を確認する。推奨は「使わない」。

- **使わない**: 現在の cwd で直接作業する
- **使う**: [worktree-setup.md](references/worktree-setup.md) を読んでセットアップしてから Gate 実行へ進む

worktree を使う場合、以後の読み書き、検証、コミットは worktree 内で行う。

## Gate 通過条件

各 Gate について:

1. 全 Acceptance Criteria が `checked: true` であること
2. `gates[].review.result === "PASSED"`、または SKIPPED 適用条件を満たすこと
3. 上記が満たされたら `gates[].passed = true` を書き込み、`status` を再計算する

## 実行プロトコル

### Preflight

`preflight[]` が存在し、未チェック項目がある場合のみ実行する。

1. `manual: false` は `command` を実行する
2. `manual: true` はユーザーに作業完了を確認する
3. 各項目の `ac` が成立しているか確認する
4. 成立した項目だけ `preflight[].checked = true` にする
5. `tasks.json` 更新後、必ず `sync-spec-md.mjs` を実行する

### Step 1 — IMPL

各 Gate について以下を実行する。

1. `dependencies` の Gate がすべて `passed: true` であることを確認する
2. Gate 契約を読む:
   - `goal.what` / `goal.why`
   - `constraints.must` / `constraints.mustNot`
   - `acceptanceCriteria[]`
   - `todos[]`（id / title / affectedFiles / dependencies / tdd）
3. `tdd: true` の Todo がある場合は、先に失敗するテストまたは検証を置けるか判断し、置ける場合は TDD で進める
4. `[SIMPLE]` Todo は過剰な設計を避け、局所変更として処理する
5. ユーザー確認が必要な仕様の曖昧さが出た場合だけ止めて確認する

### Step 2 — VERIFY

AC とレビューを検証する。

#### AC 検証

- Gate の Acceptance Criteria を 1 件ずつ検証する
- コマンド、テスト、HTTP、ブラウザ確認、ファイル確認、モック検証など、AC の成立を確認できる手段を使う
- AC に明示された検証手段を優先する
- 環境制約やユーザー指定により明示手段を使えない場合、同等の検証で AC の本質条件を確認できるなら `checked: true` にしてよい
- 代替検証を使った場合は `review.summary` に検証範囲を明記する
- 同等検証で代替できない AC は未チェックのまま残す
- 実装中に AC が成立した場合は、Gate 全体の完了前でも `acceptanceCriteria[].checked = true` に更新してよい

#### レビュー判定

- docs/config/comment only や `[SIMPLE]` 専用 Gate は `review.result = "SKIPPED"` でよい
- 通常のコード変更は Codex のコードレビュー機能を使う
- Gate 実行中のレビューは、該当 Gate の Goal / Constraints / Acceptance Criteria / 対象ファイル / 対象 diff を絞って `codex review` の標準入力プロンプト方式で依頼する
- `codex review --uncommitted` は、複数 Gate をまとめてレビューする最終確認や、変更範囲がその Gate だけに限定されていることが明らかな場合に限って使う
- コミット済み差分をレビューする場合は `codex review --commit <sha>` を使う。ただし Gate 契約に照らす必要がある場合は、コミット SHA に加えて対象 Gate 仕様を標準入力で明示する
- レビュープロンプトには最低限、対象 Gate id、仕様ファイルパス、対象ファイル、判定してほしい観点、除外したい無関係差分を含める
- `codex review` の結果に P1 / blocker があれば FAIL。P2 は内容を精査して PASS / FAIL を判断する。コメントなし、または P3 のみなら PASS としてよい
- `codex review` が利用できない環境では、diff を読み、仕様適合、破壊的変更、テスト不足、既存パターン違反を自己レビューする。その場合は `review.summary` に `codex review unavailable` と代替レビューであることを明記する

結果判定:

- 全 AC checked + review PASSED/SKIPPED → Gate PASS
- 未 checked AC あり、またはレビュー上の blocker あり → FAIL として修正へ

### Step 3 — FIX

FAIL の場合のみ、同じ Gate 内で修正して再 VERIFY する。3 ラウンドで解消しなければ状況を報告してユーザー判断を仰ぐ。

### Step 4 — UPDATE

`tasks.json` のみを更新する。`spec.md` の generated 領域は直接編集しない。

更新対象:

1. 成立した `acceptanceCriteria[].checked = true`
2. 該当 Gate の `review = { result, fixCount, summary }`
3. 全 AC checked + `review.result` が PASSED/SKIPPED なら `passed = true`
4. トップレベル `status`

Todo 単位の `checked` は schema v3 の標準ではない。Todo の完了は対応する AC の成立で記録する。

### status の算出ルール

```text
gates.length == 0                                                                  -> not-started
passed が 0 件、かつ全 AC が未 checked、かつ review/preflight 進捗もない           -> not-started
いずれかの AC が checked、review が記録済み、または 0 < passed < gates.length       -> in-progress
passed == gates.length && !reviewChecked                                            -> in-review
passed == gates.length && reviewChecked                                             -> completed
```

更新後に必ず同期する:

```bash
node .codex/skills/dev/spec-agent-run/scripts/sync-spec-md.mjs docs/PLAN/{YYMMDD}_{slug}/tasks.json
```

## 完了処理

全 Gate の `passed === true` を確認したら:

1. `status` が `in-review` になっていることを確認する
2. 未コミット変更があれば、ユーザーの意図と変更範囲に沿ってコミットする
3. worktree を使っている場合は、ユーザーに「先にマージ」か「レビュー後にマージ」か確認する
4. マージする場合は [worktree-teardown.md](references/worktree-teardown.md) を読んで実行する
5. `spec.md` に未チェックの `レビュー完了` があり、ユーザーが確認済みなら `spec.md` の authored 領域と `tasks.json.reviewChecked` を更新し、再同期する

## 参照

- [worktree-setup.md](references/worktree-setup.md) - optional worktree setup
- [worktree-teardown.md](references/worktree-teardown.md) - optional merge and cleanup
- [scripts/sync-spec-md.mjs](scripts/sync-spec-md.mjs) - regenerate `spec.md` generated section from `tasks.json`
- [scripts/setup-worktree.sh](scripts/setup-worktree.sh) - create or reuse `.worktrees/{slug}`
- [scripts/cleanup-worktree.sh](scripts/cleanup-worktree.sh) - remove merged worktree and feature branch
