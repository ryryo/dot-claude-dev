# Dashboard Table View — 規模軸ビュー切替の追加

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

---

## 概要

既存の Kanban ビューに加え、同じ `PlanFile[]` データを **Table 形式 + 規模ヒストグラム + プロジェクトグルーピング** で表示する第 2 ビューを追加し、タブで切り替え可能にする。「軽いタスクからサクサク」「重いタスクをじっくり」という規模ベースの作業判断を支援することがゴール。

## 背景

現状の Kanban カードでは、各 Plan の **規模感（残作業のボリューム）が視覚的に伝わらない** ため、「レビュー待ちの軽いものを片付けたい」「今は重いものに集中したい」という日次の作業選択がしづらい。深掘り（dev:dig 結果）でも、プロジェクト横断俯瞰の弱さと並ぶ二大ペインとして特定された。

ビュー切替は手段で、本命は **規模を一目で把握できる体験** を提供すること。Table カラムの規模 + 規模昇順ヒストグラムで「サクッと終わる候補」を即座に発見でき、同時にプロジェクトでグルーピングできるようにする。

## 設計決定事項

| #   | トピック | 決定 | 根拠 |
| --- | -------- | ---- | ---- |
| 1   | UI 構成 | Kanban / Table のタブ式切替（同一ページ内） | 1 ページ内、状態維持しやすい、個人作業向き |
| 2   | 第 2 ビュー本命 | Plan 行 → Gate 行展開可能な Table | Plan 単位の一覧性 + 必要時に Gate 進捗も見える |
| 3   | 規模指標 | `getPlanSize(plan) = gates.length + todos.length`（全体規模、完了含む） | データから即計算可能、シンプル、進捗とは独立した「Planの重さ」を表す |
| 4   | 規模ビン分類 | S(1-3) / M(4-7) / L(8-15) / XL(16+) | 4 ビンで「軽い／中／重い／巨大」を覚えやすく区別 |
| 5   | Table 実装 | **TanStack Table v8** を導入 | ソート・フィルタ・展開・グルーピングを標準 API で提供。25KB 程度の依存追加は許容 |
| 6   | レビュー情報カラム | **Table には含めない** | Table は規模・進捗に集中。レビュー詳細は展開 Gate 行 / PlanDetail で見る |
| 7   | ヒストグラム連動 | バークリックでその規模ビンだけに絞り込み（再クリックで解除、単一選択トグル） | 状態管理シンプル、ワンクリックで Quick Wins セクション化 |
| 8   | プロジェクトグルーピング | **両ビューに ON/OFF トグル**（横断的関心事） | 1 プロジェクトに限らず複数 Repo を選んだ時の必須機能 |
| 9   | Kanban グルーピング表示 | 横スイムレーン（Project 行 × Status 列のグリッド） | 既存 4 列を保ったまま 2 軸化、Plan 位置が両軸で読める |
| 10  | ビュー間の状態 | **同期しない（全独立）** | 実装シンプル、選択状態の混乱回避 |
| 11  | グルーピング状態の永続化 | **保存しない（セッション内のみ）** | リロードで Kanban + グルーピング OFF にリセット。実装最シンプル |
| 12  | 想定ユーザー | 自分のみ（個人作業用） | 共有・SEO 要件は不要、URL 同期も不要 |

## アーキテクチャ詳細

### 全体構成

```
app/page.tsx (Home)
├─ DashboardLayout
│   ├─ AppSidebar (filterContent / dateFilterContent / statsContent)
│   └─ <main>
│       ├─ ヘッダー（タイトル + バッジ）
│       ├─ <ViewSwitcher activeView onViewChange />        ← Gate A
│       ├─ <GroupingToggle enabled onToggle label="…" />   ← Gate D
│       ├─ activeView === "kanban" ? (
│       │     <KanbanBoard plans groupByProject={enabled} />  ← 既存 + Gate D
│       │   ) : (
│       │     <>
│       │       <SizeHistogram plans activeBin onBinClick />  ← Gate C
│       │       <PlanTable plans groupByProject sizeBinFilter />  ← Gate B/D
│       │     </>
│       │   )
```

### データ構造

新規ヘルパー（`dashboard/lib/plan-size.ts`、純粋関数）:

```ts
export type SizeBin = 'S' | 'M' | 'L' | 'XL';

export interface PlanSize {
  gateCount: number;  // plan.gates.length
  todoCount: number;  // plan.todos.length
  total: number;      // gateCount + todoCount
}

/** Plan の全体規模を返す。完了状態は考慮しない */
export function getPlanSize(plan: PlanFile): PlanSize;

/** 規模 total を S/M/L/XL のビンに分類 */
export function getSizeBin(total: number): SizeBin;
// total <= 3   → 'S'
// total <= 7   → 'M'
// total <= 15  → 'L'
// total >= 16  → 'XL'

/** Plan 配列を規模ビンごとに集計 */
export function getSizeHistogram(plans: PlanFile[]): Record<SizeBin, number>;
```

### ViewType

```ts
type ViewType = 'kanban' | 'table';
// page.tsx: const [activeView, setActiveView] = useState<ViewType>('kanban');
```

### Table カラム定義

`PlanTable`（`dashboard/components/plan-table.tsx`）の TanStack Table カラム:

| カラム ID | ヘッダー | アクセサ | ソート | 表示 |
| --------- | -------- | -------- | ------ | ---- |
| `expander` | – | – | – | Plan 行展開アイコン |
| `projectName` | プロジェクト | `plan.projectName` | ✓ | Badge |
| `title` | PLAN | `plan.title` | ✓ | テキスト（line-clamp-1） |
| `status` | ステータス | `plan.status` | ✓ | ステータスバッジ（既存 status カラー） |
| `size` | 規模 | `getPlanSize(plan).total` | ✓（デフォルト昇順表示可） | 数値 + 細い水平バー |
| `progress` | 進捗 | `plan.progress.percentage` | ✓ | 数値 + 既存プログレスバー風 |
| `createdDate` | 作成日 | `plan.createdDate` | ✓ | YYYY-MM-DD or `–` |
| `actions` | – | – | – | 全文表示ボタン（PlanMarkdownModal を開く） |

#### 展開行（Gate 行）

`getRowCanExpand: () => true` で全 Plan 行を展開可能化。展開時に `renderSubComponent` で `plan.gates` をテーブル状にレンダリング:

| Gate ID | Gate タイトル | Todo 進捗 |
|---------|--------------|----------|
| Gate A  | 基盤         | 2/3       |
| Gate B  | …            | 0/4       |

Gate ヘッダー名のクリックは行わず、詳細を見たい場合は別カラムの「全文表示」ボタンで既存の `PlanMarkdownModal` を開く。

### グルーピング適用

#### Table 側

`groupByProject === true` の時、行データを `projectName` でグループ化。TanStack Table の `getGroupedRowModel` を使い、グループヘッダー行（プロジェクト名 + 件数）を表示。グループ内ソートは規模カラムが優先。

#### Kanban 側

`KanbanBoard` に `groupByProject` prop を追加。`true` の時:

```
            未着手    進行中    レビュー  完了
Project A  | □ □    | ■      | □       | ■ ■  |
Project B  | □      | ■ ■   | □ □    |       |
Project C  |        | ■      |          | ■    |
```

- 既存の 4 列レイアウトを保持しつつ、行を Project 単位で分割
- Project ごとに `plansByStatus` を再計算
- 既存の縮小表示・カード展開ロジックは維持
- Project 数 ≥ 5 の場合は縦スクロール想定（`overflow-y-auto` + `max-h`）

### ヒストグラム連動

```ts
// PlanTable 内
const [sizeBinFilter, setSizeBinFilter] = useState<SizeBin | null>(null);
const filteredPlans = sizeBinFilter
  ? plans.filter(p => getSizeBin(getPlanSize(p).total) === sizeBinFilter)
  : plans;

// SizeHistogram
<SizeHistogram
  plans={plans}                        // 全 Plan（フィルタ前）で集計
  activeBin={sizeBinFilter}
  onBinClick={(bin) =>
    setSizeBinFilter(prev => prev === bin ? null : bin)
  }
/>
```

ヒストグラムは Plan 数を Y 軸とした 4 本（S/M/L/XL）の棒グラフ。アクティブなビンはハイライト + 解除バッジを Table 上部に表示。

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
| -------- | -------- | ---- |
| `dashboard/app/page.tsx` | `activeView` ステート追加、`ViewSwitcher` / `GroupingToggle` / `PlanTable` / `SizeHistogram` を組み込み | 中 |
| `dashboard/components/kanban-board.tsx` | `groupByProject` prop 追加。横スイムレーン分岐ロジック | 中（既存 UI に影響しないようガード） |
| `dashboard/package.json` | `@tanstack/react-table` 依存追加 | 小 |

### 新規作成ファイル

| ファイル | 内容 |
| -------- | ---- |
| `dashboard/lib/plan-size.ts` | `getPlanSize` / `getSizeBin` / `getSizeHistogram` ヘルパー（純粋関数） |
| `dashboard/components/view-switcher.tsx` | Kanban / Table タブ切替 UI |
| `dashboard/components/grouping-toggle.tsx` | "Project でグループ化" トグルスイッチ |
| `dashboard/components/plan-table.tsx` | TanStack Table ベースの Plan 一覧 + Gate 展開 + グルーピング対応 |
| `dashboard/components/size-histogram.tsx` | 規模ビン棒グラフ（クリックでフィルタ） |
| `dashboard/__tests__/plan-size.test.ts` | `getPlanSize` / `getSizeBin` / `getSizeHistogram` のユニットテスト |

### 変更しないファイル

| ファイル | 理由 |
| -------- | ---- |
| `dashboard/components/plan-card.tsx` | Kanban ビューでそのまま使う。グルーピング対応は KanbanBoard 側で完結 |
| `dashboard/components/plan-detail.tsx` | 既存の階層表示を再利用（モーダルで表示） |
| `dashboard/components/plan-markdown-modal.tsx` | 全文表示は既存モーダルを再利用 |
| `dashboard/lib/plan-parser.ts` / `dashboard/lib/types.ts` | 型変更不要。`PlanFile` の既存フィールドのみ使用 |
| `dashboard/components/dashboard-layout.tsx` / `app-sidebar.tsx` | サイドバー構成は維持。フィルター類はそのまま |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
| -------- | ---- |
| `dashboard/lib/types.ts` | `PlanFile` / `PlanStatus` / `Gate` / `Todo` / `Step` の型定義 |
| `dashboard/components/kanban-board.tsx` | 既存 Kanban の構造と縮小表示ロジック。スイムレーン化の出発点 |
| `dashboard/components/plan-card.tsx` | カード UI。Table の行スタイル参考 |
| `dashboard/components/plan-detail.tsx` | Gate→Todo→Step 階層表示。Table の Gate 展開行で進捗集計を参考 |
| `dashboard/app/page.tsx` | フィルター・stats 構成。新規ビュー組み込み箇所 |
| `dashboard/DESIGN.md` | カラー、タイポグラフィ、密度方針 |
| `dashboard/components/ui/` | shadcn コンポーネント一覧（badge, card, separator, scroll-area 等を再利用） |
| `dashboard/__tests__/plan-parser.test.ts` | Vitest の書き方リファレンス |

## タスクリスト

> **実装詳細は `tasks.json` を参照。** このセクションは進捗管理と Review 記録用。

### 依存関係図

```
Gate A: 基盤
├── Todo A1 [TDD] getPlanSize ヘルパー
├── Todo A2 [TDD] getSizeBin ヘルパー
└── Todo A3 ViewSwitcher コンポーネント

Gate B: Tableビュー本体（Gate A 完了後）
├── Todo B1 TanStack Table 導入 + 土台
├── Todo B2 Plan 行レンダリング（カラム + 規模バー + ソート）
├── Todo B3 Gate 展開行
└── Todo B4 全文表示ボタン（既存モーダル接続）

Gate C: 規模ヒストグラム（Gate A 完了後）
├── Todo C1 [TDD] getSizeHistogram ヘルパー
├── Todo C2 SizeHistogram コンポーネント
└── Todo C3 Table ↔ ヒストグラム連動フィルタ

Gate D: プロジェクトグルーピング（Gate A 完了後、B/C と並行可）
├── Todo D1 GroupingToggle コンポーネント
├── Todo D2 KanbanBoard 横スイムレーン対応
└── Todo D3 PlanTable プロジェクトグルーピング対応

Gate E: 統合（Gate B/C/D 完了後）
├── Todo E1 page.tsx で全体統合
└── Todo E2 動作確認 + ビューごとの状態独立検証
```

### Gate A: 基盤

- [ ] **Todo A1** [TDD]: `getPlanSize` ヘルパー実装
  > **Review A1**:

- [ ] **Todo A2** [TDD]: `getSizeBin` ヘルパー実装
  > **Review A2**:

- [ ] **Todo A3**: ViewSwitcher コンポーネント
  > **Review A3**:

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: Tableビュー本体

- [ ] **Todo B1**: TanStack Table v8 導入 + PlanTable 土台
  > **Review B1**:

- [ ] **Todo B2**: Plan 行レンダリング（カラム + 規模バー + ソート）
  > **Review B2**:

- [ ] **Todo B3**: Gate 展開行
  > **Review B3**:

- [ ] **Todo B4**: 全文表示ボタン（PlanMarkdownModal 接続）
  > **Review B4**:

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate C: 規模ヒストグラム

- [ ] **Todo C1** [TDD]: `getSizeHistogram` ヘルパー実装
  > **Review C1**:

- [ ] **Todo C2**: SizeHistogram コンポーネント
  > **Review C2**:

- [ ] **Todo C3**: Table ↔ ヒストグラム連動フィルタ
  > **Review C3**:

**Gate C 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate D: プロジェクトグルーピング

- [ ] **Todo D1**: GroupingToggle コンポーネント
  > **Review D1**:

- [ ] **Todo D2**: KanbanBoard 横スイムレーン対応
  > **Review D2**:

- [ ] **Todo D3**: PlanTable プロジェクトグルーピング対応
  > **Review D3**:

**Gate D 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate E: 統合

- [ ] **Todo E1**: page.tsx で全体統合（state + レイアウト）
  > **Review E1**:

- [ ] **Todo E2**: 動作確認 + ビュー独立性の検証
  > **Review E2**:

**Gate E 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
| ------ | ---- | ------ |
| TanStack Table v8 + React 19 の互換性 | Gate B が破綻する可能性 | Todo B1 で動作確認・必要なら `--legacy-peer-deps` を許容 |
| 横スイムレーン化で Project 数増加時に縦スクロールが煩雑 | Kanban の体験劣化 | Todo D2 で `max-h-[calc(100vh-200px)] overflow-y-auto` を Project 行ラッパに付与 |
| 規模ビン境界（3/7/15/16+）が実データに合わない | Quick Wins セクションが機能不全 | Todo A2 のテストでサンプル Plan を流して手動確認、必要なら境界値調整 |
| ヒストグラムフィルタ + 既存日付/Repo フィルタの組み合わせで結果ゼロ | UX 混乱 | PlanTable 空状態に「規模フィルタを解除」ボタンを表示 |
| TanStack Table の bundle size 増（~25KB） | 初回ロード遅延 | Next.js のコード分割が効くため許容範囲。計測は不要 |
