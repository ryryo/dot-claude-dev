# Dashboard で v2 tasks.json を構造化表示する

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

## Preflight（環境セットアップ）

> Codex / サブエージェントの sandbox 制限により、ネットワーク必須の処理を `/dev:spec-run` 実行時に Claude main session が先に実行する。詳細は `tasks.json` の `preflight` 配列を参照。

- [ ] **P1**: shadcn Accordion コンポーネントを dashboard に追加

---

## 概要

dashboard 上で v2 形式（`schemaVersion: 2`）の plan に対し、`tasks.json` の全構造（spec メタ / preflight / gates / todos / steps / review / impl）を整形表示する Sheet を追加する。v1 plan は既存挙動を変えない。

## 背景

- 現状の dashboard では v2 plan を読み込んでも、Gate / Todo / Step の **薄い表示用ビュー**（`PlanFile`）に変換する過程で `gates[].description` / `gates[].passCondition` / `todos[].description` / `impl` / `affectedFiles` / `relatedIssues` / `preflight` 等のリッチフィールドが破棄されている (`dashboard/lib/plan-json-loader.ts:50`)。
- ユーザーは Web 上で「タスク全体の実装手順」までブラウズしたいが、現状は GitHub の素の JSON ファイルを開くしかない。
- spec.md（既存 `FileText` モーダル）と並列に、tasks.json 専用の構造化ビューを提供することで、PLAN のレビュー体験を完結させる。

## 設計決定事項

| #   | トピック                | 決定                                                                                                       | 根拠                                                                                                                                          |
| --- | ----------------------- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | UI トリガー             | 既存 `FileText`（spec.md modal）の左隣に新規 `ListChecks` アイコンを追加。v2 plan の場合のみ表示する       | spec.md とタスク詳細を **両方** 視認可能にしたい。差し替えだと spec.md への導線を失う                                                         |
| 2   | データ転送方式          | 新規 API route `/api/plans/tasks` を設けて **lazy fetch**。クライアント側で簡易キャッシュ                  | tasks.json は最大 30KB 超。一覧 API に inline すると plan 数 × 30KB が初期 payload に乗る。lazy なら Sheet を開いた plan のみ通信             |
| 3   | キャッシュ              | コンポーネントローカルの `Map<key, TasksJsonV2>` で、同一 plan の再オープン時は再 fetch しない             | グローバルストア導入は過剰。Next.js の `fetch` 側 revalidate 300 秒も併用                                                                     |
| 4   | 表示構造                | 上から: Spec メタ → Preflight 一覧 → Gate アコーディオン → Gate 配下に Todo アコーディオン                 | tasks.json の階層構造そのままが最も理解しやすい                                                                                               |
| 5   | impl 表示               | Todo を展開した時のみ `react-markdown` で全文レンダリング                                                  | impl はサイズが大きい（数 KB / Todo）。閉じている間は描画コスト 0                                                                              |
| 6   | v1 互換                 | `PlanFile.hasV2Tasks: boolean` フラグを追加。v1 では false → 新アイコン非表示                              | 既存 v1 plan の挙動は **完全に維持**                                                                                                          |
| 7   | API パスとクエリ        | `GET /api/plans/tasks?owner={owner}&repo={repo}&slug={dirSlug}` で tasks.json を返す                       | `PlanFile.projectName` (`owner/repo`) と `filePath` (`docs/PLAN/{slug}/spec.md`) からクライアント側でクエリを組み立てられる                  |
| 8   | エラー UI               | fetch 失敗 / JSON parse 失敗 / 404 のいずれも「タスク詳細の取得に失敗しました」+ 再試行ボタンを Sheet 内に表示 | 開発者向け dashboard なので過度な UX 投資は不要、ただし沈黙はしない                                                                           |
| 9   | shadcn コンポーネント   | Sheet / Badge / ScrollArea / Skeleton は既存。Accordion のみ未導入のため Preflight P1 で `shadcn add accordion` を実行 | shadcn は CLI 経由で必要なものだけ追加する方針                                                                                                |
| 10  | TDD ラベル              | 全 Todo 非 TDD                                                                                              | 純粋ロジックは型追加程度。UI 中心のタスクなのでアサーション駆動になじまない                                                                   |

## アーキテクチャ詳細

### サーバー側データフロー（既存 + 追加）

```
[既存]
GET /api/plans?repos=...
  └─ fetchPlanFiles (lib/github.ts)
       ├─ tryLoadV2 → tasks.json + spec.md → loadPlanFromTasksJson → PlanFile (v2)
       └─ parsePlanFile (legacy) → PlanFile (v1)
  → PlanFile[]  ※ v2 でも tasksJsonRaw は破棄される

[追加]
GET /api/plans/tasks?owner=O&repo=R&slug=S
  └─ fetchFileContent('docs/PLAN/{S}/tasks.json')
       └─ JSON.parse → schemaVersion >= 2 を検証
  → TasksJsonV2 | { error: string }
```

### クライアント側コンポーネント階層

```
PlanCard / PlanTable
 ├─ FileText icon (既存 spec.md modal)
 ├─ ListChecks icon (新規, hasV2Tasks のみ表示) ── click ──┐
 │                                                          ▼
 │                                              TasksDetailSheet (新規)
 │                                                ├─ useTasksJson(owner, repo, slug)
 │                                                ├─ Spec メタ section
 │                                                ├─ Preflight section (preflight.length > 0)
 │                                                └─ Gate Accordion (× gates.length)
 │                                                     └─ Todo Accordion (× gate todos.length)
 │                                                          ├─ description
 │                                                          ├─ affectedFiles table
 │                                                          ├─ steps list
 │                                                          ├─ review summary (if exists)
 │                                                          └─ impl markdown (展開時のみ)
 └─ ChevronDown (既存)
```

### 型定義の追加

`dashboard/lib/types.ts`:

```typescript
export interface PlanFile {
  // 既存フィールド ...
  hasV2Tasks: boolean;  // 新規追加
}
```

### lazy fetch フックの仕様

`dashboard/lib/use-tasks-json.ts`:

```typescript
type State =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: TasksJsonV2 }
  | { status: 'error'; message: string };

// モジュールスコープのキャッシュ（タブ内永続）
const cache = new Map<string, TasksJsonV2>();

export function useTasksJson(args: {
  owner: string;
  repo: string;
  slug: string;
  enabled: boolean;  // Sheet が開いていない時は false
}): { state: State; reload: () => void };
```

### 新 API route の仕様

`dashboard/app/api/plans/tasks/route.ts`:

- `GET /api/plans/tasks?owner=X&repo=Y&slug=Z` で受ける
- 必須クエリのいずれかが欠ければ 400
- `slug` は英数字 + `_` + `-` のみ許可（path traversal 防止のホワイトリスト）
- `fetchFileContent(owner, repo, 'docs/PLAN/{slug}/tasks.json')` で取得
- `JSON.parse` 後 `schemaVersion >= 2` を検証。NG なら 422
- 成功時は `TasksJsonV2` をそのまま返す
- 認証は既存 `/api/plans` と同じ仕組みを踏襲（`getHeaders()` → `GITHUB_TOKEN`）

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル                                  | 変更内容                                                                                  | 影響                                                                                      |
| ----------------------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `dashboard/lib/types.ts`                  | `PlanFile` に `hasV2Tasks: boolean` 追加                                                  | 既存 PlanFile を返すコード全てに初期化が必要                                              |
| `dashboard/lib/plan-json-loader.ts`       | v2 由来の PlanFile に `hasV2Tasks: true` を設定                                           | 影響範囲限定                                                                              |
| `dashboard/lib/plan-parser.ts`            | v1 由来の PlanFile に `hasV2Tasks: false` を設定                                          | 影響範囲限定                                                                              |
| `dashboard/lib/github.ts`                 | （変更なしで済むはずだが、ヘルパー追加検討）                                              | -                                                                                         |
| `dashboard/components/plan-card.tsx`      | `hasV2Tasks` が true のとき `ListChecks` アイコン + `TasksDetailSheet` 起動を追加         | v1 plan は見た目変化なし                                                                  |
| `dashboard/components/plan-table.tsx`     | actions セルに同上のアイコンを追加                                                        | v1 plan は見た目変化なし                                                                  |
| `dashboard/__tests__/plan-json-loader.test.ts` | `hasV2Tasks: true` の検証アサーションを追加                                          | テスト緑                                                                                  |

### 新規作成ファイル

| ファイル                                                | 内容                                                                              |
| ------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `dashboard/app/api/plans/tasks/route.ts`                | tasks.json を lazy 取得する API ハンドラ                                          |
| `dashboard/lib/use-tasks-json.ts`                       | クライアントサイド lazy fetch + キャッシュフック                                  |
| `dashboard/components/tasks-detail-sheet.tsx`           | Sheet 全体（メタ / Preflight / Gate Accordion 骨格）                              |
| `dashboard/components/tasks-detail-todo.tsx`            | Todo Accordion 1 件分（description / affectedFiles / steps / review / impl）      |
| `dashboard/__tests__/use-tasks-json.test.ts`            | フックの fetch・キャッシュ・エラー挙動の単体テスト                                |
| `dashboard/__tests__/tasks-route.test.ts`               | 新 API route のクエリ検証・schemaVersion 検証の単体テスト                         |

### 変更しないファイル

| ファイル                                | 理由                                                                       |
| --------------------------------------- | -------------------------------------------------------------------------- |
| `dashboard/lib/plan-size.ts`            | 進捗算出にしか使われていない                                               |
| `dashboard/components/plan-detail.tsx`  | カード展開時の既存ビュー。今回の Sheet とは独立                            |
| `dashboard/components/plan-markdown-modal.tsx` | spec.md 表示用。tasks.json 表示には別コンポーネントを用意                |
| `.claude/skills/dev/spec/...`           | テンプレート / スキーマは v2 で確定済み                                    |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル                                              | 目的                                                                          |
| ----------------------------------------------------- | ----------------------------------------------------------------------------- |
| `dashboard/lib/types.ts`                              | `TasksJsonV2*` 型と `PlanFile` 型の定義                                       |
| `dashboard/lib/github.ts`                             | `tryLoadV2` の流れ、`fetchFileContent` の使い方、`getHeaders` の token 規約   |
| `dashboard/lib/plan-json-loader.ts`                   | v2 → PlanFile 変換のロジック                                                  |
| `dashboard/lib/plan-parser.ts`                        | v1 → PlanFile 変換のロジック（`hasV2Tasks: false` の埋め込みポイント）        |
| `dashboard/components/plan-card.tsx`                  | 新アイコン追加箇所、既存 `FileText` ボタンとの並べ方                          |
| `dashboard/components/plan-table.tsx`                 | テーブル actions セルでの追加                                                 |
| `dashboard/components/plan-markdown-modal.tsx`        | Sheet レイアウトの既存パターン（参考実装）                                    |
| `dashboard/app/api/plans/route.ts`                    | 新 API route の認証パターンの雛形                                             |
| `dashboard/components/ui/sheet.tsx`                   | shadcn Sheet コンポーネント                                                   |
| `dashboard/components/ui/accordion.tsx`               | shadcn Accordion コンポーネント（Preflight P1 で追加されるファイル）         |
| `docs/PLAN/260412_spec-dashboard-format-v2/spec.md`   | v2 schema の経緯と全体像                                                      |
| `docs/PLAN/260412_spec-dashboard-format-v2/tasks.json` | サンプル v2 JSON                                                              |

## タスクリスト

<!-- generated:begin -->
<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->
<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->

### 依存関係図

```
Gate A: バックエンド基盤
Gate B: UI コンポーネント（Gate A 完了後）
Gate C: 結線・検証（Gate B 完了後）
```

### Gate A: バックエンド基盤

> 型定義・PlanFile への v2 識別フラグ追加・新 API route 実装

- [ ] **A1**: PlanFile に hasV2Tasks フラグを追加
  > **Review A1**: _未記入_
- [ ] **A2**: v2 / v1 ローダーで hasV2Tasks を初期化
  > **Review A2**: _未記入_
- [ ] **A3**: /api/plans/tasks API route を新規実装
  > **Review A3**: _未記入_

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: UI コンポーネント

> lazy fetch フックと TasksDetailSheet / TasksDetailTodo を実装

- [ ] **B1**: useTasksJson カスタムフックを実装
  > **Review B1**: _未記入_
- [ ] **B2**: TasksDetailSheet コンポーネント（メタ・Preflight・Gate 骨格）
  > **Review B2**: _未記入_
- [ ] **B3**: TasksDetailTodo サブコンポーネント（Todo 詳細・impl markdown）
  > **Review B3**: _未記入_

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate C: 結線・検証

> PlanCard / PlanTable への結線と E2E 動作確認

- [ ] **C1**: PlanCard / PlanTable に ListChecks アイコンと Sheet 起動を結線
  > **Review C1**: _未記入_
- [ ] **C2**: ローカル dev サーバーで v2 plan の Sheet 表示を E2E 確認
  > **Review C2**: _未記入_

**Gate C 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

<!-- generated:end -->

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク                                                                                       | 影響                                                                | 緩和策                                                                                                       |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| GitHub Contents API のレート制限（authenticated 5,000 req/h）に lazy fetch 分が追加で乗る   | 連続して大量の plan を開いた場合に rate limit ヒットの可能性        | 本 API 内の `fetch` でも `next: { revalidate: 300 }` を付け、Next.js のキャッシュに乗せる                    |
| 巨大な impl markdown を持つ Todo を多数同時展開すると DOM 描画が重くなる可能性               | UX 劣化                                                             | Accordion はデフォルト closed。展開時のみ markdown 描画                                                      |
| `slug` クエリの path traversal                                                               | リポジトリ内任意ファイルが読まれる                                  | サーバー側で `^[A-Za-z0-9_-]+$` ホワイトリスト検証。NG は 400                                                |
| v2 schema が将来 v3 に進化した場合                                                           | hasV2Tasks の意味が曖昧になる                                       | 当面は schemaVersion>=2 を真とする。v3 導入時にフラグ名・分岐見直し                                          |
