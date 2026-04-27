# dashboard を tasks.json schemaVersion 3 専用に移行

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（Claude / Codex）を選択済みであること。

---

## 概要

ダッシュボード (Next.js / `dashboard/`) が受理する PLAN を v3 tasks.json (`schemaVersion === 3`) のみに絞り、v1/v2 と markdown-only PLAN を完全に非表示にする。型・API・loader・UI・テストを Gate 契約 (Goal/Constraints/AC) ベースの正規化形に刷新する。

## 背景

`.claude/skills/dev/spec` と `.claude/skills/dev/spec-run` を Gate 契約モデル (schemaVersion 3) に統一したことで、v3 tasks.json は **Gate 単位の Goal / Constraints / Acceptance Criteria** を正としたデータ構造になった。

一方 dashboard 側はまだ v2 シェイプ (`steps[]` / `step.review` / `todo.impl` / 単一 progress) に依存している:

- `lib/types.ts` の正規化 `PlanFile` が `Step{kind, review, reviewResult, reviewFixCount}` を保持
- `tasks-detail-todo.tsx` が `step.review` / `todo.impl` を直接描画
- `plan-card.tsx` / `plan-table.tsx` が `hasV2Tasks` フラグで UI 分岐
- `lib/plan-parser.ts` が markdown フォールバックとして v1/v2 PLAN にも対応

このまま v3 を流すと **schemaVersion 数値だけは通る (>= 2 ガード)** が、`gates[].goal` 等を loader が捨ててしまうため UI に Gate 契約が届かない。Gate 契約を表示するためには UI まで一気通貫で v3 専用化する必要がある。

## 設計決定事項

| #   | トピック | 決定 | 根拠 |
| --- | -------- | ---- | ---- |
| 1   | 互換性 | v1/v2 互換シムは作らない。v3 のみ受理 | Gate 契約 UI は v3 シェイプ前提。互換シムを残すと型・UI 双方に v2 想定が滞留する |
| 2   | フォールバック | markdown フォールバック (`lib/plan-parser.ts`) を完全撤去 | tasks.json が無い PLAN を表示すると v3 進捗指標 (gatesPassed/AC) を作れず、UI が破綻する |
| 3   | 表示対象 | tasks.json が schemaVersion 3 で取得できる PLAN のみ表示 | v1/v2 PLAN は API 422 で UI に届かない。リストにも出ない |
| 4   | 進捗指標 | `progress: { gatesPassed, gatesTotal, currentGate, currentGateAC: { passed, total } }` の二段表示 | Gate 通過と現 Gate 内 AC 進行を分離して見せる方が、ユーザーの「あと何で完了か」判断に直結する |
| 5   | UI 表示単位 | 詳細パネルは Gate ビュー、Todo は軽量サマリ | v3 では Goal / Constraints / AC が Gate 単位、Todo は粒度・影響範囲のみ。UI もこの構造を反映 |
| 6   | Step 概念 | UI / 型から Step を完全撤去 (`StepKind` / `Step.review*` 含む) | v3 には Step 階層がない。残すと型と実態がずれる |
| 7   | テストデータ | v2 fixture は全削除、v3 fixture に総入れ替え | 二重メンテを避け、v3 シェイプを単一の真実とする |
| 8   | API ガード | `app/api/plans/tasks/route.ts` は `schemaVersion === 3` のみ 200、それ以外は 422 | v2 シェイプを 422 にして UI 経路を完全に閉じる |
| 9   | レビュー表示 | Gate-level review を 3 状態で表示 (下表) | v3 では review が Gate 単位。`review: null` は仕様上の「未実施」状態なので空白ではなく状態バッジを出して "次に何をすべきか" を可視化する |
| 10  | リネーム規則 | `tryLoadV2` → `tryLoadV3`、`isV2TasksJson` → `isV3TasksJson`、`hasV2Tasks` → 撤去 | 名前と実態を一致させる。Boolean フラグは v3 only になれば不要 |

### Gate-level review の 3 状態 (決定 #9 詳細)

| 状態 | 判定式 | バッジ表示 |
| ---- | ------ | ---------- |
| 未レビュー | `review === null && AC.passed < AC.total` | グレーバッジ「未レビュー」+ 補足「Gate 完了後にレビューが入ります」 |
| レビュー待ち | `review === null && AC.passed === AC.total` | 黄色バッジ「レビュー待ち」 |
| レビュー済 | `review !== null` | result に応じた色バッジ (PASSED 緑 / FAILED 赤 / SKIPPED グレー) + summary + fixCount |

## アーキテクチャ詳細

### データフロー（実装後の最終形）

```
GitHub (raw tasks.json)
   ↓  fetchFileContent (lib/github.ts)
   ↓  isV3TasksJson  -- schemaVersion === 3 でなければ null
   ↓  tryLoadV3
   ↓
loadPlanFromTasksJson (lib/plan-json-loader.ts)
   ↓  v3 → 新 PlanFile (Gate 契約付き)
   ↓
PlanFile  -- gates[].{goal, constraints, acceptanceCriteria, review, passed}
          -- progress: { gatesPassed, gatesTotal, currentGate, currentGateAC }
   ↓
UI コンポーネント
   ├─ plan-card / plan-table       : Gate 進捗 + AC 進捗の二段表示
   ├─ kanban-board                 : status バケット (not-started/in-progress/in-review/completed)
   ├─ size-histogram               : gatesTotal ベース
   └─ plan-detail
        ├─ Gate ヘッダ              : Goal.what/why、MUST/MUST NOT、AC チェックリスト、Gate.review
        └─ tasks-detail-todo       : 軽量 Todo (依存 / affectedFiles / TDD バッジ)
```

### 新しい型構造（lib/types.ts）

```ts
// ===== v3 schema =====
export interface TasksJsonV3Spec { slug, title, summary, createdDate, specPath }
export interface TasksJsonV3Progress {
  gatesPassed: number
  gatesTotal: number
  currentGate: string | null
  currentGateAC: { passed: number; total: number }
}
export interface TasksJsonV3Preflight { id, title, command, manual, reason, ac, checked }
export interface TasksJsonV3AcceptanceCriteria { id, description, checked }
export interface TasksJsonV3Review { result: ReviewResult, fixCount: number, summary: string }
export interface TasksJsonV3Todo {
  id, gate, title, tdd: boolean, dependencies: string[],
  affectedFiles: { path, operation, summary }[]
}
export interface TasksJsonV3Gate {
  id, title, summary, dependencies: string[],
  goal: { what: string; why: string },
  constraints: { must: string[]; mustNot: string[] },
  acceptanceCriteria: TasksJsonV3AcceptanceCriteria[],
  todos: TasksJsonV3Todo[],
  review: TasksJsonV3Review | null,
  passed: boolean
}
export interface TasksJsonV3 {
  schemaVersion: 3,
  spec: TasksJsonV3Spec,
  status: PlanStatus,
  reviewChecked: boolean,
  progress: TasksJsonV3Progress,
  preflight: TasksJsonV3Preflight[],
  gates: TasksJsonV3Gate[],
  metadata: { createdAt, totalGates, totalTodos }
}

// ===== 正規化 PlanFile =====
export interface Todo {  // 軽量
  id: string
  title: string
  tdd: boolean
  dependencies: string[]
  affectedFiles: { path: string; operation: string; summary: string }[]
}
export interface Gate {
  id: string
  title: string
  summary: string
  dependencies: string[]
  goal: { what: string; why: string }
  constraints: { must: string[]; mustNot: string[] }
  acceptanceCriteria: { id: string; description: string; checked: boolean }[]
  todos: Todo[]
  review: { result: ReviewResult; fixCount: number; summary: string } | null
  passed: boolean
}
export interface PlanFile {
  filePath: string
  fileName: string
  projectName: string
  title: string
  createdDate: string | null
  reviewChecked: boolean
  status: PlanStatus
  gates: Gate[]
  todos: Todo[]  // gates から flatten した利便性プロパティ
  progress: {
    gatesPassed: number
    gatesTotal: number
    currentGate: string | null
    currentGateAC: { passed: number; total: number }
  }
  summary: string
  rawMarkdown: string  // 詳細表示で spec.md の本文を出すため保持
}
```

`Step` / `StepKind` / `hasReview` / `reviewFilled` / `reviewResult` / `reviewFixCount` / `hasV2Tasks` は完全削除。

### API ガードの最終形

```ts
// app/api/plans/tasks/route.ts
if (
  typeof parsed !== 'object' ||
  parsed === null ||
  (parsed as { schemaVersion?: unknown }).schemaVersion !== 3
) {
  return NextResponse.json(
    { error: 'tasks.json must be schemaVersion 3' },
    { status: 422 },
  );
}
return NextResponse.json(parsed as TasksJsonV3);
```

### UI 表示形式（plan-detail.tsx の Gate ヘッダ抜粋）

```
Gate A: 型・API・loader を v3 化  [PASSED · fix 0]

Goal
  what — v3 tasks.json のみが API を通過し、新しい正規化 PlanFile (Gate 契約付き) として UI 層に届く土台を整える。
  why  — 後続 Gate (UI 刷新 / 進捗表示 / テスト) の前提は『型・API・loader が v3 のみ扱う』こと。

Constraints
  ✅ MUST
    - dashboard/lib/types.ts に TasksJsonV3* 型を追加
    - schemaVersion === 3 のみ受理
    - ...
  ❌ MUST NOT
    - TasksJsonV2 系を残す
    - ...

Acceptance Criteria  3 / 5
  [x] A.AC1 — grep ヒット 0
  [x] A.AC2 — vitest GREEN
  [ ] A.AC3 — ...

Review summary: 〜

Todos (5)
  - A1  TasksJsonV3* 型追加        [dashboard/lib/types.ts]
  - A2  PlanFile 刷新              [dashboard/lib/types.ts]
  - A3  [SIMPLE] API ガード        [route.ts]
  ...
```

### 進捗バー（plan-card.tsx の最終形）

```
Gate 2 / 4              [████████░░░░] 50%
現 Gate (B) AC 3 / 5    [██████░░░░░░] 60%
```

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
| -------- | -------- | ---- |
| dashboard/lib/types.ts | TasksJsonV2* 削除 / TasksJsonV3* 追加 / PlanFile を Gate 契約形に刷新 / Step・hasV2Tasks 撤去 | 全 UI / 全 lib に波及 |
| dashboard/lib/plan-json-loader.ts | TasksJsonV3 → 新 PlanFile 変換に書き換え。convertStep / hasV2Tasks 関連コードを削除 | API 経由の表示パス |
| dashboard/lib/github.ts | isV2TasksJson → isV3TasksJson、tryLoadV2 → tryLoadV3。markdown フォールバック呼び出し撤去 | PLAN リスト集約全般 |
| dashboard/app/api/plans/tasks/route.ts | schemaVersion === 3 のみ受理 | tasks 詳細 API |
| dashboard/app/api/plans/route.ts | markdown フォールバックパスを削除 | PLAN リスト API |
| dashboard/app/page.tsx | 集計ロジックを v3 PlanFile に対応 | ダッシュボードトップ |
| dashboard/components/plan-card.tsx | 進捗 UI を Gate/AC 二段に変更、hasV2Tasks 分岐撤去 | カードビュー |
| dashboard/components/plan-table.tsx | 進捗列を v3 形に変更、hasV2Tasks 分岐撤去 | テーブルビュー |
| dashboard/components/plan-detail.tsx | Gate 契約 UI (Goal/MUST/MUST NOT/AC/Review) に書き換え | PLAN 詳細パネル |
| dashboard/components/tasks-detail-todo.tsx | 軽量 Todo 表示に書き換え (step / impl 撤去) | Todo 詳細 |
| dashboard/components/tasks-detail-sheet.tsx | progress 表示を v3 形に | Sheet UI |
| dashboard/components/kanban-board.tsx | status 集計を v3 ルールに対応 | カンバンビュー |
| dashboard/components/size-histogram.tsx | bin を gatesTotal ベースに | ヒストグラム |
| dashboard/__tests__/plan-json-loader.test.ts | v3 fixture に総入れ替え | loader テスト |
| dashboard/__tests__/tasks-route.test.ts | schemaVersion === 3 only ルールで書き換え | API テスト |
| dashboard/__tests__/use-tasks-json.test.ts | モックを v3 シェイプに更新 | hook テスト |

### 新規作成ファイル

なし（既存ファイルの修正のみ）。

### 削除するファイル

| ファイル | 理由 |
| -------- | ---- |
| dashboard/lib/plan-parser.ts | markdown フォールバック撤廃に伴い不要 |
| dashboard/__tests__/plan-parser.test.ts | parsePlanFile 削除に伴い不要 |
| dashboard/__tests__/plan-parser-hierarchy.test.ts | 同上 |
| dashboard/__tests__/plan-parser-summary.test.ts | 同上 |

### 変更しないファイル

| ファイル | 理由 |
| -------- | ---- |
| dashboard/lib/auth.ts / login-rate-limit.ts | 認証経路。今回のスコープ外 |
| dashboard/components/session-launcher-*.tsx | セッション起動 UI。tasks.json には依存しない |
| dashboard/components/app-sidebar.tsx / view-switcher.tsx / project-filter.tsx / date-filter.tsx / repo-selector.tsx | レイアウト・フィルタ系。Gate 契約構造には依存しない |
| dashboard/__tests__/auth.test.ts / github.test.ts / login-rate-limit.test.ts / plan-path.test.ts / plan-size.test.ts / types-contract.test.ts | tasks.json schema に依存しないテスト |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
| -------- | ---- |
| dashboard/lib/types.ts | 既存 v2 型定義の正確な構造把握 |
| dashboard/lib/plan-json-loader.ts | 既存 v2 → PlanFile 変換ロジック |
| dashboard/lib/plan-parser.ts | 撤去対象。撤去前に呼び出し箇所を把握 |
| dashboard/lib/github.ts | GitHub fetch + isV2TasksJson + markdown フォールバック呼び出し |
| dashboard/app/api/plans/tasks/route.ts | 既存 schemaVersion ガード |
| dashboard/app/api/plans/route.ts | PLAN リスト集約 API |
| dashboard/app/page.tsx | メインページ集約 |
| dashboard/components/plan-card.tsx | 既存進捗 UI / hasV2Tasks 分岐 |
| dashboard/components/plan-table.tsx | 既存テーブル UI |
| dashboard/components/plan-detail.tsx | 既存詳細パネル UI (Step 表示含む) |
| dashboard/components/tasks-detail-todo.tsx | 既存 Todo 詳細 UI (step.review / todo.impl 直接参照) |
| dashboard/components/tasks-detail-sheet.tsx | 既存 Sheet UI |
| dashboard/components/kanban-board.tsx | 既存カンバン UI |
| dashboard/components/size-histogram.tsx | 既存ヒストグラム UI |
| .claude/skills/dev/spec/references/templates/tasks-schema-v3.md | v3 schema 仕様 |
| .claude/skills/dev/spec/references/templates/tasks.template.json | v3 雛形 |

外部参照なし。

## タスクリスト

<!-- generated:begin -->
<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->
<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->

### 依存関係図

```
Gate A: 型・API・loader を v3 化
Gate B: リスト・カードの v3 進捗表示化（Gate A 完了後）
Gate C: 詳細パネルを Gate 契約 UI に刷新（Gate A 完了後）
Gate D: markdown フォールバック撤去とテスト総入れ替え（Gate A, B, C 完了後）
```

### Gate A: 型・API・loader を v3 化

> TasksJsonV3* 型を追加し v2 系を一掃。API ガードを schemaVersion === 3 に絞り、plan-json-loader を新 PlanFile 形に書き換える。

**Goal**: v3 tasks.json のみが API を通過し、新しい正規化 PlanFile (Gate 契約付き) として UI 層に届く土台を整える。 — 後続 Gate (UI 刷新 / 進捗表示 / テスト) の前提は『型・API・loader が v3 のみ扱う』こと。最初に流入経路を絞ることで、UI 側で v2 シェイプを意識する必要がなくなる。

**Constraints**:
- ✅ MUST: dashboard/lib/types.ts に TasksJsonV3 / TasksJsonV3Spec / TasksJsonV3Progress / TasksJsonV3Preflight / TasksJsonV3Gate / TasksJsonV3Todo / TasksJsonV3AcceptanceCriteria / TasksJsonV3Review 型を定義する
- ✅ MUST: schemaVersion 3 のみ受理する API ガードに変更する (app/api/plans/tasks/route.ts)
- ✅ MUST: lib/github.ts の isV2TasksJson / tryLoadV2 を isV3TasksJson / tryLoadV3 にリネームし schemaVersion === 3 のみ通す
- ✅ MUST: plan-json-loader が v3 入力から新 PlanFile (gates[].goal/constraints/acceptanceCriteria/review/passed を保持) を生成する
- ✅ MUST: PlanFile.progress を { gatesPassed, gatesTotal, currentGate, currentGateAC: { passed, total } } 形に変更する
- ✅ MUST: Step / StepKind / hasReview / reviewFilled / reviewResult / reviewFixCount 等の旧 Step 概念を PlanFile から撤去する
- ✅ MUST: hasV2Tasks フラグを PlanFile から完全に削除する
- ❌ MUST NOT: TasksJsonV2 / TasksJsonV2Spec / TasksJsonV2Step / TasksJsonV2Todo / TasksJsonV2Gate 等の v2 型を残す
- ❌ MUST NOT: schemaVersion < 3 を受理する分岐を残す
- ❌ MUST NOT: v2 シェイプへの暗黙的な変換シムを追加する
- ❌ MUST NOT: 後続 Gate を待たずに UI コンポーネント (plan-card / plan-detail / tasks-detail-todo 等) を編集する

**Acceptance Criteria**:
- [x] **A.AC1**: `grep -r "TasksJsonV2" dashboard/` のヒット数が 0
- [x] **A.AC2**: `vitest run dashboard/__tests__/tasks-route.test.ts` が GREEN で、schemaVersion 1/2 入力に対し 422 を返すケースを含む
- [x] **A.AC3**: `vitest run dashboard/__tests__/plan-json-loader.test.ts` が GREEN で、v3 fixture 入力に対し PlanFile.gates[0] に goal/constraints/acceptanceCriteria/review/passed が含まれることを検証している
- [x] **A.AC4**: `cd dashboard && bun run lint` が 0 errors
- [x] **A.AC5**: `grep -r "hasV2Tasks" dashboard/` のヒット数が 0

**Todos** (5):
- **A1**: TasksJsonV3* 型を追加し TasksJsonV2* を削除 — `dashboard/lib/types.ts`
- **A2**: 正規化 PlanFile を Gate 契約ベースに刷新 — `dashboard/lib/types.ts`
- **A3**: [SIMPLE] API ガードを schemaVersion === 3 に変更 — `dashboard/app/api/plans/tasks/route.ts`
- **A4**: github.ts の loader を v3 名前空間にリネーム — `dashboard/lib/github.ts`
- **A5**: [TDD] plan-json-loader を v3 → 新 PlanFile 変換に書き換え — `dashboard/lib/plan-json-loader.ts`, `dashboard/__tests__/plan-json-loader.test.ts`

**Review**: ✅ PASSED — v3 型・API ガード・loader の刷新を完了。grep TasksJsonV2 / hasV2Tasks 0 hits、tasks-route.test.ts 9件、plan-json-loader.test.ts 7件 GREEN、lint 0 errors。Gate A スコープ堅持のため UI は最小コンパイル fix のみ

### Gate B: リスト・カードの v3 進捗表示化

> PLAN リスト系コンポーネント (plan-card / plan-table / size-histogram) と app/page.tsx の集計を、新しい progress 形 (Gate X/Y + 現 Gate AC m/n) に対応させる。

**Goal**: ユーザーが PLAN 一覧で『Gate 進捗 + 現 Gate AC 進捗』を一目で把握できる UI に変更する。 — v2 まで単一の completed/total しか持たなかった進捗指標が v3 で 2 段になったため、UI が片方しか見ないと『あと 1 Gate なのに表示は 50%』のような誤解が生じる。

**Constraints**:
- ✅ MUST: plan-card.tsx / plan-table.tsx の進捗表示を gatesPassed/gatesTotal + currentGateAC.passed/total の二段に変更する
- ✅ MUST: app/page.tsx の集計ロジックが新しい PlanFile 型を扱えるようにする
- ✅ MUST: size-histogram.tsx の bin が gatesTotal ベースで描画される
- ✅ MUST: hasV2Tasks に依存していた条件分岐を撤去する (UI からこのフラグへの参照をゼロにする)
- ❌ MUST NOT: progress.completed / progress.total への参照を新コードに残す
- ❌ MUST NOT: Gate 詳細パネル (plan-detail / tasks-detail-todo) の刷新を Gate B のスコープに混ぜる
- ❌ MUST NOT: v2 シェイプ用の表示分岐を残す

**Acceptance Criteria**:
- [x] **B.AC1**: `grep -rn "hasV2Tasks\|progress\.completed\|progress\.total" dashboard/components dashboard/app` のヒット数が 0
- [x] **B.AC2**: `cd dashboard && bun run lint` が 0 errors
- [x] **B.AC3**: `cd dashboard && npm run dev` 後にダッシュボードを開くと、PLAN カードに 'Gate 2/5 · AC 3/4' のような二段進捗が表示される (手動)
- [x] **B.AC4**: PLAN テーブルビュー (`/?view=table`) でも同等の Gate/AC 二段表示が出る (手動)
- [x] **B.AC5**: サイズヒストグラムが gatesTotal の値で集計され表示される (手動)

**Todos** (4):
- **B1**: plan-card.tsx の進捗表示を Gate ベース二段に変更 — `dashboard/components/plan-card.tsx`
- **B2**: plan-table.tsx の進捗列を Gate ベース二段に変更 — `dashboard/components/plan-table.tsx`
- **B3**: app/page.tsx の集計ロジックを v3 PlanFile に対応 — `dashboard/app/page.tsx`
- **B4**: [SIMPLE] size-histogram.tsx を gatesTotal ベースに変更 — `dashboard/components/size-histogram.tsx`

**Review**: ✅ PASSED — plan-card / plan-table を二段進捗 (Gate + 現Gate AC) に刷新、app/page.tsx の集計に AC 進捗追加。size-histogram は plan-size.ts 経由で gates ベース集計を継承。grep hasV2Tasks/progress.completed/progress.total 0 hits、lint 0 errors、vitest 53/53 GREEN、サイドバーで「Gate 進捗」「現 Gate AC 進捗」並列表示をブラウザ確認。

### Gate C: 詳細パネルを Gate 契約 UI に刷新

> plan-detail / tasks-detail-todo / tasks-detail-sheet を Gate ごとの Goal/Constraints/AC/Review 表示と軽量 Todo 表示に作り変える。kanban の status 集計も v3 に揃える。

**Goal**: Gate 詳細を開いたときに、Goal (what/why) / MUST / MUST NOT / AC チェックリスト / Gate-level review が見え、Todo は影響ファイル・依存・TDD バッジだけの軽量表示になる UI を提供する。 — v3 の中核は『Gate 契約』なので、ユーザーが進捗確認・レビュー判断・委任のいずれを行うときも Gate ビューが基点になる必要がある。

**Constraints**:
- ✅ MUST: plan-detail.tsx で各 Gate に Goal.what / Goal.why が表示される
- ✅ MUST: plan-detail.tsx で MUST / MUST NOT が箇条書きで表示される
- ✅ MUST: plan-detail.tsx で AC が checkbox 形式 (id + description + checked 状態) で表示される
- ✅ MUST: plan-detail.tsx で Gate.review (PASSED/FAILED/SKIPPED + summary + fixCount) が表示される
- ✅ MUST: plan-detail.tsx で gate.review が null の場合、AC 充足度に応じて「未レビュー」(AC.passed < AC.total) または「レビュー待ち」(AC.passed === AC.total) のプレースホルダバッジを表示する
- ✅ MUST: tasks-detail-todo.tsx は軽量 Todo 表示 (依存・affectedFiles・TDD バッジ) のみで構成する
- ✅ MUST: tasks-detail-sheet.tsx の進捗表示を v3 progress 形に揃える
- ✅ MUST: kanban-board.tsx の status バケット計算が v3 PlanFile (gatesPassed/gatesTotal/reviewChecked) で正しく動く
- ❌ MUST NOT: step.review / step.kind / step.reviewResult / step.reviewFixCount への参照を残す
- ❌ MUST NOT: todo.steps[] / todo.impl の表示ロジックを残す
- ❌ MUST NOT: Markdown / react-markdown を Todo 詳細で使う (impl 撤廃に伴い不要)
- ❌ MUST NOT: Gate B のスコープに含まれるリスト系コンポーネントを変更する

**Acceptance Criteria**:
- [x] **C.AC1**: `grep -rn "step\.review\|step\.kind\|todo\.steps\|todo\.impl" dashboard/components` のヒット数が 0
- [x] **C.AC2**: `cd dashboard && bun run lint` が 0 errors
- [x] **C.AC3**: PLAN 詳細を開くと各 Gate に Goal (what/why) / MUST / MUST NOT / AC チェックリスト / Review (PASSED/FAILED/SKIPPED) が描画される (手動 / npm run dev)
- [x] **C.AC4**: Todo 詳細 (Sheet) で Todo は依存・affectedFiles・TDD バッジのみ表示され、step リスト/impl 表示が存在しない (手動)
- [x] **C.AC5**: kanban ビュー (`/?view=kanban`) で 'not-started / in-progress / in-review / completed' の各列に PLAN が正しく振り分けられる (手動)
- [x] **C.AC6**: review === null の Gate のうち AC 未充足のものには「未レビュー」バッジ、AC 全充足のものには「レビュー待ち」バッジが描画される。review !== null の Gate には result + summary が描画される (手動)

**Todos** (4):
- **C1**: plan-detail.tsx を Gate 契約 UI に書き換え — `dashboard/components/plan-detail.tsx`
- **C2**: tasks-detail-todo.tsx を軽量 Todo 表示に書き換え — `dashboard/components/tasks-detail-todo.tsx`
- **C3**: [SIMPLE] tasks-detail-sheet.tsx の進捗を v3 形に — `dashboard/components/tasks-detail-sheet.tsx`
- **C4**: kanban-board.tsx の status 集計を v3 ルールに対応 — `dashboard/components/kanban-board.tsx`

**Review**: ✅ PASSED — plan-detail を Gate-contract UI (Goal what/why、MUST/MUST NOT 箇条書き、AC チェックリスト、Review セクション + ヘッダ 3-state バッジ) に書き換え。tasks-detail-todo / tasks-detail-sheet / kanban-board は Gate A の最小 fix でそれぞれ TasksJsonV3Todo / v3 progress / plan.status 直接フィルタに切り替わり済み。grep step.review/step.kind/todo.steps/todo.impl 0 hits、lint 0 errors、vitest 53/53 GREEN。

### Gate D: markdown フォールバック撤去とテスト総入れ替え

> lib/plan-parser.ts と関連テスト 3 ファイルを削除し、残テストを v3 シェイプに更新。最終的に lint/build/vitest が GREEN になることを確認する。

**Goal**: v1/v2 markdown PLAN の表示経路を絶ち、テストスイートが v3 シェイプを保証する状態にする。 — Gate A〜C で UI/API/loader を v3 化しても、markdown フォールバックが残っていると v1/v2 PLAN が裏口経由で UI に届く可能性がある。テスト側も v2 fixture が残ると CI で偽陰性 / 偽陽性が発生する。

**Constraints**:
- ✅ MUST: dashboard/lib/plan-parser.ts を削除する
- ✅ MUST: dashboard/__tests__/plan-parser.test.ts / plan-parser-hierarchy.test.ts / plan-parser-summary.test.ts を削除する
- ✅ MUST: dashboard/__tests__/tasks-route.test.ts を schemaVersion === 3 only の検証に更新する
- ✅ MUST: dashboard/__tests__/use-tasks-json.test.ts のモックを v3 シェイプに更新する
- ✅ MUST: lib/github.ts と app/api/plans/route.ts から markdown フォールバック呼び出しを撤去する (fetch 失敗 = その PLAN は除外)
- ❌ MUST NOT: markdown フォールバックの間接的な復活経路を残す
- ❌ MUST NOT: v2 fixture をテストデータとして残す
- ❌ MUST NOT: skipped/todo にしてテストを通す (削除すべきテストは削除する)

**Acceptance Criteria**:
- [ ] **D.AC1**: `test -f dashboard/lib/plan-parser.ts` が exit 1 (= ファイルが存在しない)
- [ ] **D.AC2**: `ls dashboard/__tests__/plan-parser*.test.ts 2>/dev/null | wc -l` が 0
- [ ] **D.AC3**: `cd dashboard && bun run test` (vitest) が全 GREEN
- [ ] **D.AC4**: `cd dashboard && bun run lint` が 0 errors
- [ ] **D.AC5**: `cd dashboard && bun run build` が成功
- [ ] **D.AC6**: ダッシュボードを起動 (`bun run dev`) し、v3 tasks.json を持つ PLAN のみが一覧に出る (v1/v2/markdown-only PLAN は表示されない / 手動)

**Todos** (5):
- **D1**: lib/plan-parser.ts を削除しフォールバック呼び出しを撤去 — `dashboard/lib/plan-parser.ts`, `dashboard/lib/github.ts` ほか
- **D2**: [SIMPLE] plan-parser*.test.ts (3 ファイル) を削除 — `dashboard/__tests__/plan-parser.test.ts`, `dashboard/__tests__/plan-parser-hierarchy.test.ts` ほか
- **D3**: [TDD] tasks-route.test.ts を schemaVersion === 3 only に書き換え — `dashboard/__tests__/tasks-route.test.ts`
- **D4**: [TDD] use-tasks-json.test.ts のモックを v3 シェイプに更新 — `dashboard/__tests__/use-tasks-json.test.ts`
- **D5**: lint / vitest / build を全 GREEN にする

**Review**: _未記入_

<!-- generated:end -->

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
| ------ | ---- | ------ |
| 既存環境に v1/v2 PLAN が大量に残っており、移行後にダッシュボードから消える | 旧 PLAN 履歴が見えなくなる | v3 移行は不可逆として明示。必要なら旧 PLAN は GitHub 上で直接閲覧する運用を案内 |
| markdown フォールバック撤去後、tasks.json があっても schemaVersion が 3 未満の PLAN は API 422 で見えなくなる | 移行直後に一覧が一時的にスカスカになる可能性 | 既存 v2 PLAN を v3 へアップグレードする手順は範囲外。今回はあくまで「v3 のみ表示」を目的とする |
| Gate 契約 UI 描画に伴い、Gate / Goal / Constraints の文字量が多い PLAN ではカード詳細の縦スクロールが伸びる | UX 上の長文化 | 詳細パネル側 (Gate C) で AccordionItem や折り畳みを活用してコンパクトに表示する |
| Gate-level review が未記入 (review: null) の Gate は UI 表示が空白になる | レビュー前の Gate で表示崩れ | C1 で 3 状態バッジ (未レビュー / レビュー待ち / レビュー済) を実装。判定は AC 充足度との組み合わせ。詳細は設計決定 #9 の表参照 |
