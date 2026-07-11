---
name: dev:spec-codex-run
description: |
  docs/PLAN/{YYMMDD}_{slug}/ の schema v3 仕様書を Codex で Gate 単位に実行する。
  tasks.json を正とし、Gate 契約 (Goal/Constraints/AC) に基づいて実装・検証・レビューを行う。

  Trigger:
  spec-codex-run, spec-run
user-invocable: true
---

# spec-codex-run

`tasks.json` を Single Source of Truth として Gate 単位に実行する。`spec.md` は背景と generated summary として扱う。既存 v3 PLAN は optional Codex 拡張がなくても実行できる。

## 起動フロー

### 1. 仕様書の特定

対象が会話の文脈から明確な場合はその PLAN を使う。不明な場合は `docs/PLAN/*/tasks.json` を更新日順で上位 5 件提示してユーザーに確認する。

### 2. 実行準備

`spec.md` と `tasks.json` を読み、`gates[]` 全体・`preflight[]`・`preDelegation[]`・`extensions.codex.delegationPolicy` を把握する。

### 3. Cursor Agent の使用確認

`tasks.json` に `preDelegation[]` が存在する場合、Cursor Agent への委任を使うかユーザーに確認する。使わない / `preDelegation[]` が空の場合は Codex 単独で全て実行する。

`docs/PLAN` 更新・Gate PASS 判定・最終統合・commit/push は常に main Codex が担う。

### 4. worktree の選択

ユーザーが明示していない場合は確認する。使う場合は [worktree-setup.md](references/worktree-setup.md) を読んでセットアップする。

---

## Gate 通過条件

Gate は実装完了を記録するチェックポイント。IMPL の実行順序は `dependencies[]` が制御し、Gate 通過はその事後確認として行う。

Gate を `passed: true` にできるのは、次を全て満たす場合だけ。

1. `dependencies` の全 Gate が `passed: true`
2. 全 `acceptanceCriteria` が `checked: true`
3. `review.result === "PASSED"` または SKIPPED 適用条件を満たす

---

## 実行プロトコル

### Preflight

`preflight[]` に未チェック項目がある場合のみ実行する。`manual: false` はコマンドを実行、`manual: true` はユーザーに完了確認する。`ac` が成立した項目だけ `checked: true` にして sync する。

### Pre-delegation

Cursor Agent を使う場合のみ実行する。Preflight の実行中に並行して進める。

1. `tasks.json` の `preDelegation[]` を読む
2. 各項目の `prompt`（詳細指示書）を確認し、不足があれば [delegation-brief-template.md](../spec-codex/references/delegation-brief-template.md) を Read して補完する
3. 各項目を cursor-agent CLI へ投げる

```bash
cursor-agent -p --mode ask --output-format text --workspace <workspace> --model <model> "<prompt>"
```

4. 委任結果は VERIFY フェーズで `relatedGate` / `relatedTodo` に対応する AC を検証する際に回収する。main Codex は結果を待たずに残りの Gate の IMPL を進める

### IMPL

Gate は「達成目標と検証条件の境界」であり、実行順序を定めるものではない。`dependencies[]` が空の Gate・Todo は他の完了を待たずに実行できる。実行順序は `dependencies[]` だけを制約として実行エージェントが自律的に判断する。

1. 全 Gate の `goal` / `constraints` / `acceptanceCriteria` / `todos` / `dependencies` を把握する
2. `dependencies[]` が空または全依存が解決済みの Gate・Todo から着手する
3. `tdd: true` の Todo は失敗するテストを先に書く
4. `[SIMPLE]` Todo は局所変更として処理する
5. `preDelegation[]` に切り出された作業は Pre-delegation 済みのためスキップする
6. 仕様の曖昧さが出た場合だけ止めてユーザーに確認する

### VERIFY

AC を 1 件ずつ検証する。AC に明示された検証手段（コマンド / テスト / HTTP / ブラウザ / ファイル確認）を優先する。同等代替した場合は `review.summary` に検証範囲を明記する。

**Codex review の使い分け:**

| タイミング               | コマンド                                                                                                     |
| ------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Gate 中の差分確認        | `codex review --uncommitted -`（stdin に Gate id / Goal / Constraints / AC / 対象ファイル / 除外差分を渡す） |
| 複数 Gate をまとめて確認 | `codex review --base <base>`                                                                                 |
| コミット単位の確認       | `codex review --commit <sha>`                                                                                |

P1 / blocker は FAIL。P2 は内容を精査して PASS / FAIL を判断する。P3 のみ、またはコメントなしなら PASS。`codex review` が使えない場合は自己レビューし、`review.summary` に `codex review unavailable` と明記する。

docs / config / comment のみの Gate、または `[SIMPLE]` 専用 Gate は `review.result = "SKIPPED"` でよい。

### FIX

FAIL の場合のみ同じ Gate 内で修正して再 VERIFY する。3 ラウンドで解消しなければユーザーに報告して判断を仰ぐ。

実行中に追加 Gate が必要になった場合は kind を付けて追加する。

| 状況                  | kind           |
| --------------------- | -------------- |
| 初期設計の漏れ        | `follow-up`    |
| review 由来の差分対応 | `review-fix`   |
| 実機確認・最終検証    | `verification` |

### UPDATE

`tasks.json` のみを更新する。`spec.md` generated 領域は直接編集しない。

更新対象: `acceptanceCriteria[].checked` / `review` / `passed` / `status`

更新後は必ず sync する。

```bash
bash .codex/skills/dev/spec-codex-run/scripts/sync.sh {YYMMDD}_{slug}
```

---

## status 算出ルール

```text
gates.length == 0                                                             -> not-started
passed が 0 件、かつ全 AC が未 checked、かつ review/preflight 進捗もない      -> not-started
いずれかの AC が checked、review が記録済み、または 0 < passed < gates.length -> in-progress
passed == gates.length && !reviewChecked                                       -> in-review
passed == gates.length && reviewChecked                                        -> completed
```

---

## 完了処理

全 Gate の `passed === true` を確認したら:

1. `status` が `in-review` になっていることを確認する
2. 未コミット変更があればコミットする
3. worktree を使っている場合は [worktree-teardown.md](references/worktree-teardown.md) を読んで実行する
4. `reviewChecked` の更新はユーザー確認後に行う

## References

- [worktree-setup.md](references/worktree-setup.md)
- [worktree-teardown.md](references/worktree-teardown.md)
- [scripts/sync.sh](scripts/sync.sh)
- [scripts/sync-spec-md.mjs](scripts/sync-spec-md.mjs)
- [scripts/setup-worktree.sh](scripts/setup-worktree.sh)
- [scripts/cleanup-worktree.sh](scripts/cleanup-worktree.sh)
- [../spec-codex/references/cursor-delegation-protocol.md](../spec-codex/references/cursor-delegation-protocol.md)
- [../spec-codex/references/delegation-brief-template.md](../spec-codex/references/delegation-brief-template.md)
