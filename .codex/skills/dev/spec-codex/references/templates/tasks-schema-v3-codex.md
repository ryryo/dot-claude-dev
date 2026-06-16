# tasks.json Schema v3 for spec-codex

`tasks.json` は schema v3 を維持する。既存 dashboard は `schemaVersion === 3` と既存フィールドだけを読むため、Codex 追加情報は optional として扱う。

## Top Level

| フィールド | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `schemaVersion` | `3` | yes | v3 固定 |
| `spec` | `Spec` | yes | 仕様書メタデータ |
| `status` | `not-started \| in-progress \| in-review \| completed` | yes | PLAN 全体の状態 |
| `reviewChecked` | `boolean` | yes | 人間レビュー完了 |
| `preflight` | `Preflight[]` | yes | 実行前準備。なければ `[]` |
| `preDelegation` | `PreDelegation[]` | no | Preflight と並行して先行委任する作業。なければ省略または `[]` |
| `gates` | `Gate[]` | yes | Gate 契約 |
| `extensions` | `Extensions` | no | Codex optional 拡張 |

`progress` / `metadata` は保持しない。進捗は `gates[]` から計算する。

## Spec

| フィールド | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `slug` | `string` | yes | ディレクトリ名の slug |
| `title` | `string` | yes | PLAN タイトル |
| `summary` | `string` | yes | dashboard カード用の 1-2 文 |
| `createdDate` | `YYYY-MM-DD` | yes | 作成日 |
| `specPath` | `string` | yes | 通常は `spec.md` |

## Status

```text
gates.length == 0                                                            -> not-started
passed が 0 件、かつ全 AC が未 checked、かつ review/preflight 進捗もない     -> not-started
いずれかの AC が checked、review が記録済み、または 0 < passed < gates.length -> in-progress
passed == gates.length && !reviewChecked                                      -> in-review
passed == gates.length && reviewChecked                                       -> completed
```

## Preflight

| フィールド | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | `string` | yes | `P1` など |
| `title` | `string` | yes | 準備項目名 |
| `command` | `string` | yes | 自動実行コマンド。`manual: true` の場合は空文字可 |
| `manual` | `boolean` | yes | 人間操作必須なら `true` |
| `reason` | `network \| global-write \| interactive` | yes | 抽出理由 |
| `ac` | `string` | yes | 完了確認条件 |
| `checked` | `boolean` | yes | 実行済みか |

Preflight は network 必須、workspace 外書き込み、対話ログイン/OAuth のみ。ローカル生成、test、build、通常コマンドは Preflight にしない。

## PreDelegation

Preflight と並行して先行実行する委任作業。Gate の依存関係に関わらず**今すぐ投げられる**作業のみ。

| フィールド | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | `string` | yes | `D1` など |
| `title` | `string` | yes | 作業名 |
| `agent` | `string` | yes | 委任先。例: `cursor-agent` |
| `modelTier` | `"fast" \| "standard"` | no | Composer 2.5 tier。`fast` は `composer-2.5-fast`、`standard` は `composer-2.5` |
| `model` | `string` | yes | 使用モデル。例: `composer-2.5-fast` |
| `writeScope` | `string[]` | yes | 変更してよいファイル一覧 |
| `verification` | `string[]` | yes | 完了確認コマンド |
| `prompt` | `string` | yes | 詳細指示書（delegation-brief-template.md の形式） |
| `relatedGate` | `string` | yes | 結果を受け取る Gate id |
| `relatedTodo` | `string` | yes | 対応する Todo id |
| `done` | `boolean` | yes | 委任結果の回収が完了したか |

`preDelegation` に入れてよい作業の判断基準は [cursor-delegation-protocol.md](../cursor-delegation-protocol.md) を参照。

## Gate

| フィールド | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | `string` | yes | `A`, `B` など |
| `title` | `string` | yes | Gate名 |
| `summary` | `string` | yes | 1行サマリ |
| `kind` | `implementation \| follow-up \| review-fix \| verification` | no | Codex分類 |
| `dependencies` | `string[]` | yes | 依存 Gate ID。空なら他 Gate の完了を待たずに実行できる |
| `goal` | `{ what: string, why: string }` | yes | 達成内容と意図 |
| `constraints` | `{ must: string[], mustNot: string[] }` | yes | 守る制約 |
| `acceptanceCriteria` | `AcceptanceCriteria[]` | yes | 検証可能な完了条件 |
| `todos` | `Todo[]` | yes | 軽量Todo |
| `review` | `Review \| null` | yes | Gate review結果 |
| `passed` | `boolean` | yes | Gate通過状態 |

`passed: true` にできるのは、全依存 Gate が passed、全 AC が checked、review が `PASSED` または `SKIPPED` のときだけ。

## AcceptanceCriteria

| フィールド | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | `string` | yes | `A.AC1` など |
| `description` | `string` | yes | 検証可能な状態記述 |
| `checked` | `boolean` | yes | 成立確認済みか |

AC は「実装した」ではなく「結果として何が成立しているか」を書く。検証手段はコマンド、テスト、HTTP、ブラウザ、ファイル確認、手動確認のいずれでもよい。

## Todo

| フィールド | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `id` | `string` | yes | `A1` など |
| `gate` | `string` | yes | 所属 Gate ID |
| `title` | `string` | yes | Todo名。`[TDD]`, `[SIMPLE]` ラベル可 |
| `tdd` | `boolean` | yes | TDD候補 |
| `dependencies` | `string[]` | yes | 依存 Todo ID。空なら他 Todo の完了を待たずに実行できる |
| `affectedFiles` | `AffectedFile[]` | yes | 影響ファイル |

Todo に `impl` や詳細な実装手順本文を持たせない。実行順序は `dependencies` から実行エージェントが自律的に判断する。

## AffectedFile

| フィールド | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `path` | `string` | yes | リポジトリルートからの相対パス |
| `operation` | `create \| modify \| delete` | yes | 操作種別 |
| `summary` | `string` | yes | 変更内容の短い説明 |

## Review

| フィールド | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `result` | `PASSED \| FAILED \| SKIPPED \| IN_PROGRESS` | yes | Gate review 結果 |
| `fixCount` | `number` | yes | FIX ラウンド数 |
| `summary` | `string` | yes | レビュー概要 |

## Extensions

```json
{
  "extensions": {
    "codex": {
      "diagramPlan": [],
      "delegationPolicy": {
        "stateOwner": "main-codex",
        "cursorAgent": "ask-each-run",
        "defaultCursorModelTier": "fast",
        "defaultCursorModel": "composer-2.5-fast",
        "cursorModelByTier": {
          "standard": "composer-2.5",
          "fast": "composer-2.5-fast"
        }
      }
    }
  }
}
```

## Update Ownership

| フィールド | 更新者 | タイミング |
| --- | --- | --- |
| `schemaVersion` | `spec-codex` | 作成時のみ |
| `spec.*` | `spec-codex` | 作成時 |
| `preflight[]` | `spec-codex` | 作成時 |
| `preDelegation[]` | `spec-codex` | 作成時 |
| `gates[].goal/constraints/acceptanceCriteria/todos` | `spec-codex` | 作成時 |
| `extensions.codex` | `spec-codex` | 作成時 |
| `preflight[].checked` | `spec-codex-run` | Preflight 完了時 |
| `preDelegation[].done` | `spec-codex-run` | 委任結果の回収完了時 |
| `gates[].acceptanceCriteria[].checked` | `spec-codex-run` | AC 成立確認時 |
| `gates[].review` | `spec-codex-run` | Gate review 完了時 |
| `gates[].passed` | `spec-codex-run` | Gate 通過条件成立時 |
| `status` | `spec-codex-run` | Gate / Preflight 更新時 |
| `reviewChecked` | `spec-codex-run` | 人間レビュー完了時 |

Cursor Agent や subagent は `docs/PLAN` を更新しない。必要な状態更新は main Codex が確認してから行う。
