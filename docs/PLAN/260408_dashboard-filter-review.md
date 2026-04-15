# PLAN ダッシュボード改善 — 日付フィルター・レビューステータス・サイドバー修正

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

---

## 概要

PLAN ダッシュボードに 3 つの改善を加える: (1) ファイル名の YYMMDD から日付を解析し、プリセット + スライダーで期間フィルタリング、(2) サイドバーのパス表示の折り返し修正、(3) 人間レビュー完了を追跡するレビューステータス機構の導入。

## 背景

- **日付フィルター**: PLAN ファイルが蓄積すると古いファイルがノイズになる。デフォルト 1 ヶ月で最近の作業にフォーカスしたい
- **サイドバー**: プロジェクトパスが `break-all` で折り返され、`/Users/ryryo/dev/b\nase-ui-design` のように単語途中で改行されて見づらい
- **レビューステータス**: 現在、全 TODO 完了 → 即 `completed` だが、人間のレビューを経ていないものを区別したい。spec テンプレートにレビューセクションを追加し、全 TODO 完了 + レビュー未完了 → `in-review`、レビュー完了 → `completed` の流れにする

## 設計決定事項

| #   | トピック | 決定 | 根拠 |
| --- | -------- | ---- | ---- |
| 1   | 日付解析 | ファイル名の先頭 6 文字（YYMMDD）を `20YY-MM-DD` として解析 | 既存の命名規則を活用。追加メタデータ不要 |
| 2   | 日付フィルター UI | プリセットボタン（1 週間 / 1 ヶ月 / 3 ヶ月 / すべて）+ 日数スライダー | ユーザー要望。プリセットで素早く、スライダーで微調整 |
| 3   | デフォルト期間 | 1 ヶ月（30 日） | 直近の作業にフォーカスしつつ、十分な範囲をカバー |
| 4   | パス表示 | `break-all` → `truncate` に変更 | 単語途中での改行を防止。パスは hover で全表示 |
| 5   | レビューステータス | PLAN ファイル末尾に `## レビューステータス` セクションを追加 | 既存の TODO `[x]` とは独立した人間レビュー追跡 |
| 6   | 既存 PLAN の扱い | レビューセクションがないファイルは従来どおり（全 TODO 完了 = completed） | 後方互換性を維持。新規 PLAN のみ新ロジック |
| 7   | planCounts | 日付フィルター適用後の件数を表示 | フィルター前の件数だと実際の表示と乖離して混乱する。サイドバーのプロジェクト別バッジは「現在の日付フィルターで表示される件数」を示す（総数ではない） |

## アーキテクチャ詳細

### 日付解析

ファイル名パターン: `{YYMMDD}_{slug}.md` または `{YYMMDD}_{slug}/spec.md`

```typescript
// ファイル名の先頭6文字からDateを生成
function parseDateFromFileName(fileName: string): Date | null {
  const match = fileName.match(/^(\d{6})/);
  if (!match) return null;
  const [yy, mm, dd] = [match[1].slice(0, 2), match[1].slice(2, 4), match[1].slice(4, 6)];
  const date = new Date(2000 + Number(yy), Number(mm) - 1, Number(dd));
  return isNaN(date.getTime()) ? null : date;
}
```

`PlanFile` の `fileName` はファイルモードでは `260408_slug.md`、ディレクトリモードでは `spec.md` になる。ディレクトリモードでは `filePath` から親ディレクトリ名を取得して日付を解析する。

### 日付フィルター状態管理

```typescript
// page.tsx の state
const [filterDays, setFilterDays] = useState<number>(30); // 0 = すべて

// プリセット定義
const PRESETS = [
  { label: "1週間", days: 7 },
  { label: "1ヶ月", days: 30 },
  { label: "3ヶ月", days: 90 },
  { label: "すべて", days: 0 },
];

// フィルタリング
const filteredByDate = useMemo(() => {
  if (filterDays === 0) return plans;
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - filterDays);
  return plans.filter((plan) => {
    if (!plan.createdDate) return true; // 日付解析できないファイルは常に表示
    return new Date(plan.createdDate) >= cutoff;
  });
}, [plans, filterDays]);
```

### スライダー仕様

- 範囲: 7 〜 365 日（0 は「すべて」として別扱い）
- ステップ: 1 日
- プリセットボタンクリック時にスライダー値も連動
- スライダー操作時にプリセットのアクティブ状態も連動
- 「すべて」選択時はスライダーを非活性（disabled）にする

### レビューステータスセクション

spec テンプレートに追加するセクション:

```markdown
## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認
```

パーサーでの検出:

```typescript
const REVIEW_STATUS_PATTERN = /^## レビューステータス\s*\n[\s\S]*?- \[([ x])\] \*\*レビュー完了\*\*/m;
```

### ステータス判定ロジック変更

```typescript
function determineStatus(
  todos: TodoItem[],
  hasReviewSection: boolean,
  reviewChecked: boolean
): PlanStatus {
  // 1. TODO なし → not-started
  if (todos.length === 0) return 'not-started';

  // 2. 全 TODO 完了 → レビューセクションで分岐
  if (todos.every((todo) => todo.checked)) {
    if (hasReviewSection && !reviewChecked) return 'in-review';
    return 'completed'; // セクションなし or レビュー完了
  }

  // 3. 既存: 未完了 TODO に Review 記入あり → in-review
  if (todos.some((todo) => !todo.checked && todo.reviewFilled)) return 'in-review';

  // 4. 一部完了 → in-progress
  if (todos.some((todo) => todo.checked)) return 'in-progress';

  // 5. 全て未チェック → not-started
  return 'not-started';
}
```

### データフロー図

```
[PLAN ファイル]
  ↓ parsePlanFile()
[PlanFile { createdDate, reviewChecked, ... }]
  ↓ API /api/plans
[フロントエンド]
  ↓ プロジェクトフィルター (selectedProjects)
  ↓ 日付フィルター (filterDays)
[filteredPlans]
  ↓
[KanbanBoard]  [Stats]  [planCounts]
```

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
| -------- | -------- | ---- |
| `dashboard/lib/types.ts` | `PlanFile` に `createdDate: string \| null`, `reviewChecked: boolean` 追加 | 型定義のみ。全コンポーネントに影響 |
| `dashboard/lib/plan-parser.ts` | 日付解析関数追加、レビューセクション解析追加、`determineStatus` 更新 | パース結果が変わる |
| `dashboard/app/page.tsx` | `filterDays` state 追加、日付フィルタリングロジック、`DateFilter` 配置、`planCounts` を日付フィルター後に変更 | メインページ |
| `dashboard/components/project-filter.tsx` | パス表示を `break-all` → `truncate` + tooltip | サイドバー表示 |
| `dashboard/components/app-sidebar.tsx` | 日付フィルターセクション追加 | サイドバーレイアウト |
| `.claude/skills/dev/spec/references/templates/spec-template.md` | 末尾に「レビューステータス」セクション追加 | 今後の新規 PLAN に影響 |
| `.claude/skills/dev/spec/references/templates/spec-template-dir.md` | 同上 | ディレクトリモード PLAN に影響 |

### 新規作成ファイル

| ファイル | 内容 |
| -------- | ---- |
| `dashboard/components/date-filter.tsx` | 日付フィルターコンポーネント（プリセット + スライダー） |
| `dashboard/components/ui/slider.tsx` | shadcn/ui の Slider コンポーネント（未導入のため追加） |

### 変更しないファイル

| ファイル | 理由 |
| -------- | ---- |
| `dashboard/lib/project-scanner.ts` | ファイル収集ロジックは変更不要。日付解析は parser 側で実施 |
| `dashboard/components/kanban-board.tsx` | ステータスに基づく表示は変更不要 |
| `dashboard/components/plan-card.tsx` | カード表示は変更不要 |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
| -------- | ---- |
| `dashboard/lib/types.ts` | PlanFile 型定義の確認 |
| `dashboard/lib/plan-parser.ts` | 既存パーサーロジックの理解 |
| `dashboard/app/page.tsx` | フィルター統合先の確認 |
| `dashboard/components/project-filter.tsx` | パス表示修正箇所 |
| `dashboard/components/app-sidebar.tsx` | サイドバー構成の確認 |
| `.claude/skills/dev/spec/references/templates/spec-template.md` | テンプレート修正箇所 |
| `.claude/skills/dev/spec/references/templates/spec-template-dir.md` | テンプレート修正箇所 |

## タスクリスト

### 依存関係図

```
Gate A: バックエンド（パーサー・テンプレート）
├── Todo A1: 型定義 & 日付解析
├── Todo A2: レビューステータス解析 & ステータス判定更新
└── Todo A3: spec テンプレートにレビューセクション追加

Gate B: フロントエンド UI（Gate A 完了後）
├── Todo B1: サイドバーパス表示修正
├── Todo B2: DateFilter コンポーネント作成
└── Todo B3: page.tsx & AppSidebar に日付フィルター統合
```

### Gate A: バックエンド（パーサー・テンプレート）

- [ ] **Step 1 — IMPL: 型定義 & 日付解析**
  - **対象**: `dashboard/lib/types.ts`, `dashboard/lib/plan-parser.ts`
  - **内容**: `PlanFile` に `createdDate: string | null` と `reviewChecked: boolean` を追加。`parsePlanFile` 内で `fileName`（ファイルモード）または `filePath` の親ディレクトリ名（ディレクトリモード）から YYMMDD を解析し、`20YY-MM-DD` 形式の文字列として `createdDate` に格納する
  - **実装詳細**:
    - `parseDateFromFileName(fileName: string): string | null` 関数を追加
    - 正規表現 `/^(\d{6})/` でファイル名先頭 6 文字をマッチ
    - ディレクトリモードでは `filePath` から `basename(dirname(filePath))` で親ディレクトリ名を取得
    - Date の妥当性チェック（`isNaN` ガード）
  - **[TDD]**: あり — `parseDateFromFileName` は純粋関数で入出力が明確
  - **依存**: なし

- [ ] **Step 2 — Review A1**
  > **Review A1**:

- [ ] **Step 3 — IMPL: レビューステータス解析 & ステータス判定更新**
  - **対象**: `dashboard/lib/plan-parser.ts`
  - **内容**: `## レビューステータス` セクションを検出し、`- [x] **レビュー完了**` のチェック状態を `reviewChecked` として返す。`determineStatus` を更新して、全 TODO 完了時にレビューセクションの有無で `in-review` / `completed` を分岐
  - **実装詳細**:
    - `REVIEW_STATUS_PATTERN = /^## レビューステータス\s*\n[\s\S]*?- \[([ x])\] \*\*レビュー完了\*\*/m`
    - `parsePlanFile` 内で `content.match(REVIEW_STATUS_PATTERN)` を実行
    - `reviewChecked`: マッチなし → `false`（ただしセクション自体がないことを区別）
    - `determineStatus` 更新:
      - 全 TODO チェック済み + レビューセクションあり + レビュー未完了 → `in-review`
      - 全 TODO チェック済み + レビューセクションあり + レビュー完了 → `completed`
      - 全 TODO チェック済み + レビューセクションなし → `completed`（後方互換）
    - `hasReviewSection: boolean` を内部判定に使用（型に追加不要、`determineStatus` の引数として渡す）
    - `determineStatus` の新シグネチャ: `determineStatus(todos: TodoItem[], hasReviewSection: boolean, reviewChecked: boolean): PlanStatus`（疑似コードはアーキテクチャ詳細セクション参照）
  - **[TDD]**: あり — `determineStatus` は純粋関数
  - **依存**: Todo A1

- [ ] **Step 4 — Review A2**
  > **Review A2**:

- [ ] **Step 5 — IMPL: spec テンプレートにレビューセクション追加**
  - **対象**: `.claude/skills/dev/spec/references/templates/spec-template.md`, `.claude/skills/dev/spec/references/templates/spec-template-dir.md`
  - **内容**: 両テンプレートの `## 残存リスク` セクションの直前に `## レビューステータス` セクションを追加
  - **実装詳細**:
    ```markdown
    ## レビューステータス

    - [ ] **レビュー完了** — 人間による最終確認
    ```
  - **依存**: なし

- [ ] **Step 6 — Review A3**
  > **Review A3**:

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: フロントエンド UI

- [ ] **Step 1 — IMPL: サイドバーパス表示修正**
  - **対象**: `dashboard/components/project-filter.tsx`
  - **内容**: プロジェクトパスの表示を `break-all` から `truncate` に変更し、tooltip でフルパスを表示
  - **実装詳細**:
    - 70 行目付近の `<p className="text-muted-foreground break-all text-xs">` を `<p className="text-muted-foreground truncate text-xs" title={project.path}>` に変更
    - `title` 属性でホバー時にフルパスを表示（shadcn Tooltip は過剰なのでネイティブ title で十分）
  - **依存**: なし

- [ ] **Step 2 — Review B1**
  > **Review B1**:

- [ ] **Step 3 — IMPL: DateFilter コンポーネント作成**
  - **対象**: `dashboard/components/date-filter.tsx`（新規）, `dashboard/components/ui/slider.tsx`（新規）
  - **内容**: プリセットボタン（1 週間 / 1 ヶ月 / 3 ヶ月 / すべて）+ 日数スライダーのフィルターコンポーネントを作成
  - **実装詳細**:
    - `npx shadcn@latest add slider` で Slider コンポーネントを追加
    - `DateFilter` コンポーネントの props: `{ days: number; onChange: (days: number) => void }`
    - プリセットボタンは `Button` variant="outline" で横並び、アクティブなプリセットは variant="default"
    - スライダー: range 7-365, step 1。`days === 0`（すべて）の場合は disabled
    - プリセットクリック → `onChange(preset.days)` → スライダー値も連動
    - スライダー操作 → `onChange(sliderValue)` → プリセットのアクティブ状態も連動
    - スライダー下部に現在の日数を表示（例: 「過去 30 日間」「すべての期間」）
  - **依存**: なし

- [ ] **Step 4 — Review B2**
  > **Review B2**:

- [ ] **Step 5 — IMPL: page.tsx & AppSidebar に日付フィルター統合**
  - **対象**: `dashboard/app/page.tsx`, `dashboard/components/app-sidebar.tsx`, `dashboard/components/dashboard-layout.tsx`
  - **内容**: `filterDays` state を追加し、プロジェクトフィルター → 日付フィルターの順でフィルタリング。AppSidebar に DateFilter セクションを追加
  - **実装詳細**:
    - `page.tsx`:
      - `const [filterDays, setFilterDays] = useState<number>(30)` 追加
      - `filteredPlans` の算出を 2 段階に: まずプロジェクト、次に日付
      - `planCounts` も日付フィルター適用後の値に変更（表示件数と実際の件数を一致させる）
      - `dateFilterContent` を作成し `DashboardLayout` に渡す
    - `app-sidebar.tsx`:
      - `dateFilterContent` props を追加
      - フィルターセクション内で `filterContent`（プロジェクト）の上に `dateFilterContent`（日付）を配置
    - `dashboard-layout.tsx`:
      - `dateFilterContent` props を `AppSidebar` に中継
  - **依存**: Todo B2（DateFilter コンポーネント）、Gate A（createdDate フィールド）

- [ ] **Step 6 — Review B3**
  > **Review B3**:

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

## レビューステータス

- [x] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
| ------ | ---- | ------ |
| YYMMDD 以外の命名の PLAN ファイル | 日付フィルターで除外されない（常に表示） | `createdDate: null` を常に表示扱いにすることで対処済み |
| 既存 PLAN にレビューセクションを遡及追加する作業 | 既存ファイルは従来どおり動作するので緊急性は低い | 必要に応じて手動追加。一括変換スクリプトは不要 |
| スライダーのパフォーマンス | 高速なドラッグでリレンダリングが多発する可能性 | PLAN 数が数百程度なので問題にならない見込み |
