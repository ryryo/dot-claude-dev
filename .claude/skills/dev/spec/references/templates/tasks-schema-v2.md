# tasks.json Schema v2

## 概要

v2 schema は spec.md ↔ tasks.json の二重管理問題を解消するために導入された。

**v1 からの主な変更点**:

- トップレベルに `schemaVersion: 2`, `status`, `reviewChecked`, `progress` を追加
- `spec` に `summary`, `createdDate` を追加
- `gates[]` に `description` を追加
- `todos[]` に `description`, `steps[]` を追加
- `todos[].status` を削除（`steps[].checked` の集計に置き換え）
- シングルモード廃止（全て ディレクトリモードで出力）

## トップレベルフィールド

| フィールド | 型 | 目的 | 初期値 |
|---|---|---|---|
| `schemaVersion` | `2` (literal) | v2 schema の識別子 | `2` |
| `spec` | `TasksJsonV2Spec` | 仕様書のメタデータ | — |
| `status` | `PlanStatus` | 仕様書全体の進捗ステータス | `"not-started"` |
| `reviewChecked` | `boolean` | 人間レビュー完了フラグ | `false` |
| `progress` | `{ completed, total }` | 進捗数値 | `{ completed: 0, total: 0 }` |
| `preflight` | `TasksJsonV2Preflight[]` | 事前セットアップ項目 | `[]` |
| `gates` | `TasksJsonV2Gate[]` | Gate 一覧 | — |
| `todos` | `TasksJsonV2Todo[]` | Todo 一覧（全 Gate 分の flat list） | — |
| `metadata` | `TasksJsonV2Metadata` | メタ情報 | — |

## spec オブジェクト

| フィールド | 型 | 説明 |
|---|---|---|
| `slug` | `string` | 仕様書のスラッグ（ディレクトリ名の一部） |
| `title` | `string` | 仕様書のタイトル |
| `summary` | `string` | 1-2 文の概要（dashboard カード表示用） |
| `createdDate` | `string` | 作成日（YYYY-MM-DD 形式） |
| `specPath` | `string` | spec.md のパス（通常 `"spec.md"`） |

## status / progress の算出ルール

```
total     = sum of all todos[].steps[].length
completed = count of all steps where checked == true
progress  = { completed, total }

status:
  - total == 0                                   → "not-started"
  - completed == 0                               → "not-started"
  - 0 < completed < total                        → "in-progress"
  - completed == total && reviewChecked == false → "in-review"
  - completed == total && reviewChecked == true  → "completed"
```

**更新責任**: `/dev:spec-run` が `steps[].checked` を更新する際、同一 Edit で `status` と `progress` も再計算して書き込む。

## gates[] オブジェクト

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | `string` | Gate ID（例: `"A"`, `"B"`） |
| `title` | `string` | Gate のタイトル |
| `description` | `string` | Gate の説明（dashboard カード表示用、空文字可） |
| `dependencies` | `string[]` | 依存する Gate の ID 一覧 |
| `passCondition` | `string` | Gate 通過条件の説明 |

## todos[] オブジェクト

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | `string` | Todo ID（例: `"A1"`, `"B2"`） |
| `gate` | `string` | 所属する Gate の ID |
| `title` | `string` | Todo のタイトル（`[TDD]` ラベル含む） |
| `description` | `string` | dashboard カード表示用の 1 行サマリ |
| `tdd` | `boolean` | TDD で実装するかどうか |
| `dependencies` | `string[]` | 依存する Todo の ID 一覧 |
| `affectedFiles` | `TasksJsonV2AffectedFile[]` | 変更対象ファイル一覧 |
| `impl` | `string` | 実装エージェント用の長文手順 |
| `relatedIssues` | `string[]` | 関連 Issue 番号 |
| `steps` | `TasksJsonV2Step[]` | 各 Todo 固定 2 要素（impl + review） |

`description` と `impl` の違い: `description` は dashboard カード表示用の 1 行サマリ、`impl` は実装エージェント用の長文手順。

## steps[] オブジェクト

各 Todo の `steps[]` は固定 2 要素:

1. `{ kind: "impl", title: "Step 1 — IMPL", checked: false }`
2. `{ kind: "review", title: "Step 2 — Review", checked: false, review: null }`

| フィールド | 型 | 説明 |
|---|---|---|
| `kind` | `"impl" \| "review"` | ステップの種類 |
| `title` | `string` | ステップのタイトル |
| `checked` | `boolean` | 完了フラグ |
| `review` | `TasksJsonV2Review \| null` | review kind のときのみ。未記入時は `null` |

## review オブジェクト

`steps[].review` の構造（`kind === "review"` のときのみ存在）:

| フィールド | 型 | 説明 |
|---|---|---|
| `result` | `"PASSED" \| "FAILED" \| "SKIPPED" \| "IN_PROGRESS"` | レビュー結果 |
| `fixCount` | `number` | FIX ラウンド数 |
| `summary` | `string` | レビュー概要 |

## 更新責任者表

| フィールド | 更新責任者 | タイミング |
|---|---|---|
| `schemaVersion` | `/dev:spec` | 作成時のみ（以降不変） |
| `spec.slug`/`title`/`summary` | `/dev:spec` | 作成時 |
| `spec.createdDate` | `/dev:spec` | 作成時 |
| `status` | `/dev:spec-run` | 各 Step 更新時に再計算 |
| `reviewChecked` | `/dev:spec-run` | 人間レビュー完了時 |
| `progress` | `/dev:spec-run` | 各 Step 更新時に再計算 |
| `gates[]` | `/dev:spec` | 作成時（構造変更時を除き不変） |
| `todos[].steps[].checked` | `/dev:spec-run` | IMPL / Review 完了時 |
| `todos[].steps[].review` | `/dev:spec-run` | Review 完了時 |

## サンプル完全版 JSON

1 Gate / 2 Todo の完成例:

```json
{
  "schemaVersion": 2,
  "spec": {
    "slug": "example-feature",
    "title": "サンプル機能",
    "summary": "ラベル付きアイテムを登録・検索できるようにする",
    "createdDate": "2026-04-12",
    "specPath": "spec.md"
  },
  "status": "in-progress",
  "reviewChecked": false,
  "progress": { "completed": 2, "total": 4 },
  "preflight": [],
  "gates": [
    {
      "id": "A",
      "title": "データ層のセットアップ",
      "description": "スキーマ・リポジトリ層の整備",
      "dependencies": [],
      "passCondition": "全 Review 結果記入欄が埋まり、総合判定が PASS であること"
    }
  ],
  "todos": [
    {
      "id": "A1",
      "gate": "A",
      "title": "[TDD] スキーマ定義とマイグレーション",
      "description": "items テーブルを定義し migration を生成",
      "tdd": true,
      "dependencies": [],
      "affectedFiles": [
        { "path": "db/schema/items.ts", "operation": "create", "summary": "items テーブル定義" }
      ],
      "impl": "items テーブルを drizzle-orm で定義し migration を生成する",
      "relatedIssues": [],
      "steps": [
        { "kind": "impl", "title": "Step 1 — IMPL", "checked": true },
        {
          "kind": "review",
          "title": "Step 2 — Review",
          "checked": true,
          "review": { "result": "PASSED", "fixCount": 0, "summary": "スキーマ整合性 OK" }
        }
      ]
    },
    {
      "id": "A2",
      "gate": "A",
      "title": "リポジトリ層の実装",
      "description": "CRUD 操作を提供するリポジトリ関数",
      "tdd": false,
      "dependencies": ["A1"],
      "affectedFiles": [
        { "path": "db/repositories/items.ts", "operation": "create", "summary": "items リポジトリ" }
      ],
      "impl": "items テーブルに対する CRUD 関数を実装する",
      "relatedIssues": [],
      "steps": [
        { "kind": "impl", "title": "Step 1 — IMPL", "checked": false },
        { "kind": "review", "title": "Step 2 — Review", "checked": false, "review": null }
      ]
    }
  ],
  "metadata": {
    "createdAt": "2026-04-12T00:00:00Z",
    "totalGates": 1,
    "totalTodos": 2
  }
}
```

## v1 からの移行ガイド

既存の v1 tasks.json（`schemaVersion` 未定義）は `plan-parser.ts` でレガシー読み込みされるため、移行は不要。新規の `/dev:spec` 出力のみ v2 形式となる。
