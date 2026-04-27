# tasks.json Schema v3

## 設計思想

v3 schema は **「Claude を有能なエンジニアとして委任する」** モデルに合わせて再設計された。

- **Goal / Constraints / Acceptance Criteria** を Gate 単位の契約として明示する
- **詳細な手順（impl）を捨て**、エンジニア（Claude / Codex）が自律的に実装方針を決められるようにする
- **Gate 単位で完了を判定**する（Todo 単位の Step 状態追跡を廃止）
- **Todo は契約の補助情報**（粒度の合意 / 影響範囲の明示）として残す

**v2 / v1 互換性は持たない。** 旧 schema の tasks.json は新規スキルでは扱わない。

## トップレベルフィールド

| フィールド | 型 | 目的 |
|---|---|---|
| `schemaVersion` | `3` (literal) | v3 schema の識別子 |
| `spec` | `Spec` | 仕様書のメタデータ |
| `status` | `PlanStatus` | 仕様書全体の進捗ステータス |
| `reviewChecked` | `boolean` | 人間レビュー完了フラグ |
| `preflight` | `Preflight[]` | 事前セットアップ項目 |
| `gates` | `Gate[]` | Gate 一覧（todos[] は各 Gate に内包される） |

> **`progress` / `metadata` は tasks.json に保持しない。** dashboard 側のローダー (`dashboard/lib/plan-json-loader.ts` の `computeProgress(gates)`) が `gates[]` から動的計算する。`status` のみ `/dev:spec-run` が更新する。

## spec オブジェクト

| フィールド | 型 | 説明 |
|---|---|---|
| `slug` | `string` | スラッグ（ディレクトリ名の一部） |
| `title` | `string` | 仕様書のタイトル |
| `summary` | `string` | 1-2 文の概要（dashboard カード用） |
| `createdDate` | `string` | 作成日（YYYY-MM-DD） |
| `specPath` | `string` | spec.md のパス（通常 `"spec.md"`） |

## status の算出ルール

`/dev:spec-run` が `gates[].acceptanceCriteria[].checked` / `gates[].passed` を更新する際、同一 Edit で `status` も再計算する（`progress` は tasks.json に保持しないため計算不要）。

```
status:
  - gates.length == 0                                                                  → "not-started"
  - gates.filter(g => g.passed).length == 0 && 全ての AC が checked: false             → "not-started"
  - 0 < gates.filter(g => g.passed).length < gates.length                              → "in-progress"
  - gates.filter(g => g.passed).length == gates.length && !reviewChecked               → "in-review"
  - gates.filter(g => g.passed).length == gates.length && reviewChecked                → "completed"
```

## preflight[] オブジェクト

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | `string` | Preflight ID（例: `"P1"`） |
| `title` | `string` | 短いタイトル |
| `command` | `string` | 自動実行コマンド（`manual: true` の場合は空文字） |
| `manual` | `boolean` | ユーザー手動操作必須なら `true` |
| `reason` | `string` | 抽出理由（`network` / `global-write` / `interactive`） |
| `ac` | `string` | 完了確認の Acceptance Criteria（例: `"pnpm list で @xxx が表示される"`） |
| `checked` | `boolean` | 実行完了フラグ |

## gates[] オブジェクト

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | `string` | Gate ID（例: `"A"`, `"B"`） |
| `title` | `string` | Gate のタイトル |
| `summary` | `string` | Gate の 1 行サマリ（dashboard カード用、空文字可） |
| `dependencies` | `string[]` | 依存する Gate の ID 一覧 |
| `goal` | `Goal` | この Gate のゴール（what + why） |
| `constraints` | `Constraints` | 守るべき制約（must / mustNot） |
| `acceptanceCriteria` | `AC[]` | 受け入れ基準のリスト |
| `todos` | `Todo[]` | この Gate に属する Todo 一覧 |
| `review` | `Review \| null` | Gate 単位のレビュー結果（未実施なら null） |
| `passed` | `boolean` | Gate 通過フラグ（全 AC checked + review.result === "PASSED" で true） |

### goal オブジェクト

| フィールド | 型 | 説明 |
|---|---|---|
| `what` | `string` | この Gate で何を達成するか（1-2 文） |
| `why` | `string` | なぜこの Gate が必要か / 設計上の意図 |

### constraints オブジェクト

| フィールド | 型 | 説明 |
|---|---|---|
| `must` | `string[]` | 必ず守るべき制約（採用技術・型契約・既存パターンとの整合等） |
| `mustNot` | `string[]` | やってはいけないこと（破壊的変更・スコープ外の編集等） |

### acceptanceCriteria[] オブジェクト

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | `string` | AC ID（例: `"A.AC1"`） |
| `description` | `string` | 検証可能な受け入れ基準。形式は自由（コマンド出力 / ブラウザ動作 / テスト結果 / 型チェック等、何でも可） |
| `checked` | `boolean` | この AC を満たしたかどうか |

**AC の書き方の指針**:

- 「実装したか」ではなく **「結果として何が成立しているか」** を書く
- 検証手段（コマンド・テスト・手動操作）が明確になっている
- タスクの種類により形式は自由（例: `"bun run type-check が 0 errors"`、`"GET /api/x が 200 を返す"`、`"ブラウザで /xxx を開くと表示される（手動）"`、`"bun test xxx が GREEN"`、`".env.example に NEW_KEY が記載されている"`）

## todos[] オブジェクト（軽量化版）

`todos[]` は **gate.todos[]** に内包される。トップレベルにフラットな todos 配列は持たない。

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | `string` | Todo ID（例: `"A1"`） |
| `gate` | `string` | 所属 Gate の ID（参照用、冗長） |
| `title` | `string` | Todo のタイトル（`[TDD]` ラベル可） |
| `tdd` | `boolean` | TDD で実装するかのヒント（`[TDD]` ラベル付与の根拠） |
| `dependencies` | `string[]` | 依存する Todo の ID 一覧 |
| `affectedFiles` | `AffectedFile[]` | 変更対象ファイル一覧 |

**v2 からの削除フィールド**:

- `description` — title に集約
- `impl` — Gate.goal / constraints / AC が代替（詳細手順を渡さないのがコンセプト）
- `relatedIssues` — 必要なら spec.md の「残存リスク」等に記載
- `steps[]` — Todo 単位の Step 追跡を廃止（Gate 単位の AC で完了を判定）

### affectedFiles[] オブジェクト

| フィールド | 型 | 説明 |
|---|---|---|
| `path` | `string` | リポジトリルートからの相対パス |
| `operation` | `"create" \| "modify" \| "delete"` | 操作種別 |
| `summary` | `string` | 1 行サマリ |

## review オブジェクト（Gate 単位）

`gates[].review` の構造（未実施は null）:

| フィールド | 型 | 説明 |
|---|---|---|
| `result` | `"PASSED" \| "FAILED" \| "SKIPPED" \| "IN_PROGRESS"` | レビュー結果 |
| `fixCount` | `number` | FIX ラウンド数 |
| `summary` | `string` | レビュー概要 |

## 更新責任者表

| フィールド | 更新責任者 | タイミング |
|---|---|---|
| `schemaVersion` | `/dev:spec` | 作成時のみ（不変） |
| `spec.*` | `/dev:spec` | 作成時 |
| `gates[].goal/constraints/acceptanceCriteria/todos` | `/dev:spec` | 作成時（構造変更時を除き不変） |
| `gates[].acceptanceCriteria[].checked` | `/dev:spec-run` | AC を満たしたタイミングで実装エージェント or main session が更新 |
| `gates[].review` | `/dev:spec-run` | Gate レビュー完了時 |
| `gates[].passed` | `/dev:spec-run` | 全 AC checked + review PASSED で `true` に |
| `preflight[].checked` | `/dev:spec-run` | Preflight 実行成功時 |
| `status` | `/dev:spec-run` | 上記いずれかの更新と同一 Edit で再計算 |
| `reviewChecked` | `/dev:spec-run` | 人間レビュー完了時 |

## サンプル完全版 JSON

1 Gate / 2 Todo の完成例:

```json
{
  "schemaVersion": 3,
  "spec": {
    "slug": "example-feature",
    "title": "サンプル機能",
    "summary": "ラベル付きアイテムを登録・検索できるようにする",
    "createdDate": "2026-04-27",
    "specPath": "spec.md"
  },
  "status": "in-progress",
  "reviewChecked": false,
  "preflight": [],
  "gates": [
    {
      "id": "A",
      "title": "データ層のセットアップ",
      "summary": "items テーブルとリポジトリ層",
      "dependencies": [],
      "goal": {
        "what": "items を CRUD できるリポジトリ層を整備する",
        "why": "後続の API 層がデータ操作を抽象化された関数経由で行えるようにし、テストとモック差し替えを容易にするため"
      },
      "constraints": {
        "must": [
          "drizzle-orm を使用する",
          "既存の db/schema/ ディレクトリの命名規則に従う",
          "全ての公開関数に型注釈を付ける"
        ],
        "mustNot": [
          "既存テーブルのスキーマを変更しない",
          "リポジトリ層から外部 API を呼び出さない"
        ]
      },
      "acceptanceCriteria": [
        { "id": "A.AC1", "description": "bun run type-check が 0 errors", "checked": true },
        { "id": "A.AC2", "description": "bun test db/repositories/items が GREEN", "checked": false },
        { "id": "A.AC3", "description": "drizzle-kit generate が migration を生成する", "checked": false }
      ],
      "todos": [
        {
          "id": "A1",
          "gate": "A",
          "title": "[TDD] items スキーマとリポジトリ",
          "tdd": true,
          "dependencies": [],
          "affectedFiles": [
            { "path": "db/schema/items.ts", "operation": "create", "summary": "items テーブル定義" },
            { "path": "db/repositories/items.ts", "operation": "create", "summary": "items リポジトリ" }
          ]
        },
        {
          "id": "A2",
          "gate": "A",
          "title": "migration の生成と検証",
          "tdd": false,
          "dependencies": ["A1"],
          "affectedFiles": [
            { "path": "db/migrations/", "operation": "create", "summary": "drizzle-kit が生成" }
          ]
        }
      ],
      "review": null,
      "passed": false
    }
  ]
}
```
