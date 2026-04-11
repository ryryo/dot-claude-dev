# 看板カード展開時の Step 詳細表示（Gate → Todo → Step 3階層化）

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

---

## 概要

看板カード展開時に PLAN の `#### Todo N:` (h4) 階層を復活させ、Gate → Todo → Step の3階層で表示する。各 Step には `- **内容**:` サブ箇条書きから抽出した1行説明を添え、Review Step は `[PASSED · FIX 1回]` 等の結果ラベル + 1行要約を表示する。デフォルトは Gate・Todo とも全 open、アコーディオンで畳むこともできる。

## 背景

現状のカード展開では `Step 1 — IMPL` / `Step 2 — Review A1` というラベルだけが縦に並び、以下2点の欠落によって Step の概要を掴めない:

1. **親 Todo コンテキスト消失**: パーサー (`dashboard/lib/plan-parser.ts:37`) が `gates.flatMap((gate) => gate.todos)` で Step をフラット化し、`#### Todo N: {タイトル}` (h4) の親グルーピングを完全に捨てている。同じ「Step 1 — IMPL」が複数並んでもどの Todo に属するか判別できない。
2. **Step 本文の欠落**: パーサー (`TODO_PATTERN = /^- \[([ x])\] \*\*(.+?)\*\*/gm`) はチェックボックス行の太字ラベルしか拾わず、続くサブ箇条書き (`- **内容**:` 等) を無視している。

これを Gate → Todo → Step の3階層復活 + Step ごとの1行説明 + Review 結果表示で解決する。

## 設計決定事項

| #   | トピック              | 決定                                                                                         | 根拠                                                                                     |
| --- | --------------------- | -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| 1   | 表示階層              | Gate → Todo → Step の3階層復活                                                               | 親 Todo 文脈と Step 詳細の両方が得られる                                                 |
| 2   | Step 説明ソース       | `- **内容**:` サブ箇条書きから1行取得                                                        | `内容` フィールドは「何をやるか」を最も簡潔に表現するため                                |
| 3   | 説明フォールバック順  | `内容` → `実装詳細` → `対象` → Step直下最初の bullet テキスト                                | 古い PLAN や手書き PLAN でも何かしら表示されるように                                     |
| 4   | Review Step 表示      | 結果ラベル `[PASSED · FIX 1回]` + 1行要約。書式不一致時は `[Review済]` にフォールバック      | IMPL と情報量を対称にし、レビュー要点を一目で把握可能                                    |
| 5   | Review パース粒度     | 結果語（正規表現で厳密抽出）+ 要約（1行目 `—` 以降 or 2行目の `-` bullet、commit hash 除外） | 書式ブレ3パターン以上に耐える                                                            |
| 6   | 折りたたみ UX         | Gate・Todo ともアコーディオン維持、**デフォルト全 open**、現行の Gate 排他制御は廃止         | 一覧性最大化しつつユーザーが畳める                                                       |
| 7   | データモデル命名      | `TodoItem` → `Step` にリネーム + `Todo { title, steps: Step[] }` を新規                      | 正しいメンタルモデル（現 `TodoItem` は Step の実体）                                     |
| 8   | 進捗表示レベル        | カード全体進捗バー（既存維持）+ Todo ヘッダ `(2/2 完了)`                                     | 「どの Todo が残っているか」が最小ノイズで見える                                         |
| 9   | 非テンプレ PLAN 対応  | `#### Todo N:` h4 見出しを持たない PLAN は、Gate 直下の各 bullet を1 Todo = 1 Step に変換    | 既存テスト (`plan-parser.test.ts`) のフラット形式 PLAN も破綻させない                    |
| 10  | 進捗計算定義          | `progress.total/completed` は **Step 単位カウント**（Todo は checkbox を持たない派生値）     | 現行カード全体進捗バーの意味を温存                                                       |

## アーキテクチャ詳細

### データモデル（`dashboard/lib/types.ts`）

```typescript
export type PlanStatus = 'not-started' | 'in-progress' | 'in-review' | 'completed';
export type StepKind = 'impl' | 'review';
export type ReviewResult = 'PASSED' | 'FAILED' | 'SKIPPED' | 'IN_PROGRESS';

export interface Step {
  title: string;              // 例: "Step 1 — IMPL", "Step 2 — Review A1"
  checked: boolean;           // チェックボックス状態
  kind: StepKind;             // 'impl' or 'review'
  description: string;        // 1行説明（IMPL: 内容フィールド / Review: blockquote 要約）
  hasReview: boolean;         // Review blockquote が存在するか（Review Step のみ）
  reviewFilled: boolean;      // Review blockquote に内容が記入されているか
  reviewResult: ReviewResult | null; // Review 結果ラベル（Review Step のみ）
  reviewFixCount: number | null;     // "FIX N 回" の回数（Review Step のみ、なければ 0）
}

export interface Todo {
  title: string;              // 例: "PlanFile 型に summary と rawMarkdown フィールドを追加"
  steps: Step[];
}

export interface Gate {
  id: string;                 // 例: "Gate A"
  title: string;              // 例: "データ層（型 + パーサー + テスト）"
  todos: Todo[];
}

export interface PlanFile {
  filePath: string;
  fileName: string;
  projectName: string;
  title: string;
  createdDate: string | null;
  reviewChecked: boolean;
  status: PlanStatus;
  gates: Gate[];
  todos: Todo[];              // ★破壊的変更: Step[] → Todo[]
  progress: {
    total: number;            // Step 単位
    completed: number;        // Step 単位
    percentage: number;
  };
  summary: string;
  rawMarkdown: string;
}
```

### データフロー

```
GitHub API → fetchFileContent() → content(生md)
  → parsePlanFile(content, ...)
    → parseGates(content)
      → 各 Gate セクションで parseGateTodos(section)
        → if h4 `#### Todo N:` 見出しあり:
            各 h4 セクションで Todo を構築、内部の bullet で parseSteps
          else:
            各 bullet を 1 Todo (1 Step を内包) に変換（フォールバック）
        → parseSteps(stepContent)
          → bullet label から Step.title / kind 判定
          → extractStepDescription(stepBlock) でフォールバックチェーン実行
          → Review Step なら parseReviewBlockquote(stepBlock) で結果+要約抽出
    → PlanFile.todos = gates.flatMap((gate) => gate.todos)
    → progress.total/completed は全 Step をフラット展開して計算
```

### パース詳細

#### h4 Todo 見出しの検出

```typescript
const H4_TODO_PATTERN = /^####\s+(?:Todo\s+\d+:?\s*)?(.+)$/gm;
// '#### Todo 1: PlanFile 型に...' → title: "PlanFile 型に..."
// '#### PlanFile 型に...' (Todo接頭辞なし) → title: "PlanFile 型に..."
```

Gate セクション内を `maskCodeFences` した上で h4 を探す。h4 が1つも無ければフォールバックレイアウト（各 bullet を 1 Todo = 1 Step）。

#### Step 種別の判定

```typescript
const STEP_IMPL_PATTERN = /^Step\s+\d+\s*[—–-]\s*IMPL\b/;
const STEP_REVIEW_PATTERN = /^Step\s+\d+\s*[—–-]\s*Review\b/;
```

`- [x] **Step 1 — IMPL**` のラベル部分にマッチさせ kind を決定。どちらにも該当しなければ `kind: 'impl'` をデフォルト。

#### Step 説明の抽出（フォールバックチェーン）

```typescript
function extractStepDescription(stepBlock: string): string {
  // 1. - **内容**: xxx
  const contentMatch = stepBlock.match(/^\s*-\s*\*\*内容\*\*[:：]\s*(.+)$/m);
  if (contentMatch) return stripMarkdown(contentMatch[1]).trim();

  // 2. - **実装詳細**: xxx（最初の1文まで）
  const implMatch = stepBlock.match(/^\s*-\s*\*\*実装詳細\*\*[:：]\s*(.+)$/m);
  if (implMatch) return firstSentence(stripMarkdown(implMatch[1]));

  // 3. - **対象**: xxx
  const targetMatch = stepBlock.match(/^\s*-\s*\*\*対象\*\*[:：]\s*(.+)$/m);
  if (targetMatch) return stripMarkdown(targetMatch[1]).trim();

  // 4. Step 直下の最初の bullet テキスト（ラベル行を除く）
  const firstBulletMatch = stepBlock.match(/^\s*-\s+(?!\*\*(?:内容|実装詳細|対象|依存|\[TDD\])\*\*)(.+)$/m);
  if (firstBulletMatch) return stripMarkdown(firstBulletMatch[1]).trim();

  return '';
}
```

#### Review blockquote のパース

3パターン以上の書式ブレに対応:

```
> **Review A1**: ⏭️ SKIPPED (型定義のみ、ロジック変更なし) — commit a05e43f
> **Review A2**: ✅ PASSED (FIX 1回) — commits a05e43f, d57675a
> - 初回レビューで [P2] コードブロック内 `##` 誤検出を指摘 → `maskCodeFences` 追加で修正
> - 再レビュー: regression なし
> **Review B1**: ✅ PASSED — `@tailwindcss/typography ^0.5.19`, `react-markdown ^10.1.0` を追加
```

```typescript
const REVIEW_FIRST_LINE_PATTERN = /^>\s*\*\*Review\s+[\w\d]+\*\*[:：]\s*(.+)$/m;
const REVIEW_STATUS_PATTERN = /(PASSED|FAILED|SKIPPED|IN[_\s-]?PROGRESS)/i;
const REVIEW_FIX_COUNT_PATTERN = /FIX\s*(\d+)\s*回/;
const COMMIT_HASH_PATTERN = /\b(?:commit|commits)\s+[0-9a-f,\s]+/gi;

function parseReviewBlockquote(stepBlock: string): {
  hasReview: boolean;
  reviewFilled: boolean;
  reviewResult: ReviewResult | null;
  reviewFixCount: number | null;
  summary: string;
} {
  const firstLineMatch = stepBlock.match(REVIEW_FIRST_LINE_PATTERN);
  if (!firstLineMatch) {
    return { hasReview: false, reviewFilled: false, reviewResult: null, reviewFixCount: null, summary: '' };
  }

  const firstLineBody = firstLineMatch[1];
  const isEmpty = firstLineBody.trim() === '';
  if (isEmpty) {
    return { hasReview: true, reviewFilled: false, reviewResult: null, reviewFixCount: null, summary: '' };
  }

  // 結果語抽出
  const statusMatch = firstLineBody.match(REVIEW_STATUS_PATTERN);
  const reviewResult = (statusMatch?.[1]?.toUpperCase().replace(/[\s-]/g, '_') ?? null) as ReviewResult | null;

  // FIX回数
  const fixMatch = firstLineBody.match(REVIEW_FIX_COUNT_PATTERN);
  const reviewFixCount = fixMatch ? parseInt(fixMatch[1], 10) : null;

  // 要約抽出（優先度: 1行目の — 以降 → 2行目の `- ` bullet）
  let summary = '';
  const emdashIdx = firstLineBody.search(/\s[—–-]\s/);
  if (emdashIdx >= 0) {
    summary = firstLineBody.slice(emdashIdx + 2).trim();
  }
  if (!summary) {
    // blockquote 2行目以降の最初の `- ` bullet
    const secondLineBullet = stepBlock.match(/^>\s*-\s+(.+)$/m);
    if (secondLineBullet) summary = secondLineBullet[1].trim();
  }

  // commit hash 除去
  summary = summary.replace(COMMIT_HASH_PATTERN, '').replace(/\s{2,}/g, ' ').replace(/[\s—–-]+$/, '').trim();
  summary = stripMarkdown(summary);

  return {
    hasReview: true,
    reviewFilled: true,
    reviewResult,
    reviewFixCount,
    summary,
  };
}
```

### UI 構造（`dashboard/components/plan-detail.tsx`）

```
<div className="space-y-3">
  {summary && <p>{summary}</p><Separator />}

  {gates.map(gate => (
    <div key={gate.id} className="rounded-xl border">
      <Collapsible defaultOpen> {/* ★ 排他制御廃止 */}
        <CollapsibleTrigger>
          <h3>{gate.title}</h3>  {/* Gate ヘッダに進捗は出さない */}
          <ChevronDown />
        </CollapsibleTrigger>
        <CollapsibleContent>
          {gate.todos.map(todo => (
            <Collapsible defaultOpen key={todo.title}>
              <CollapsibleTrigger>
                <h4>{todo.title}</h4>
                <span>({completedSteps}/{todo.steps.length} 完了)</span>
                <ChevronDown />
              </CollapsibleTrigger>
              <CollapsibleContent>
                {todo.steps.map(step => (
                  <StepRow step={step} />
                ))}
              </CollapsibleContent>
            </Collapsible>
          ))}
        </CollapsibleContent>
      </Collapsible>
    </div>
  ))}
</div>
```

`StepRow` コンポーネントの骨格:

```tsx
function StepRow({ step }: { step: Step }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-lg bg-muted/30 px-3 py-2">
      <div className="flex min-w-0 flex-col gap-1">
        <div className="flex items-center gap-2">
          {step.checked ? <Check className="text-primary size-4" /> : <Circle className="text-muted-foreground size-4" />}
          <span className="text-sm font-medium">{step.title}</span>
        </div>
        {step.description && (
          <p className="text-muted-foreground text-xs pl-6 line-clamp-2">{step.description}</p>
        )}
      </div>
      {step.kind === 'review' && step.hasReview && step.reviewFilled && (
        <Badge variant="secondary" className="shrink-0">
          {step.reviewResult ?? 'Review済'}
          {step.reviewFixCount && step.reviewFixCount > 0 ? ` · FIX ${step.reviewFixCount}回` : ''}
        </Badge>
      )}
    </div>
  )
}
```

### 進捗計算の仕様

```typescript
function calculateProgress(todos: Todo[]): { total, completed, percentage } {
  const allSteps = todos.flatMap((todo) => todo.steps);
  const total = allSteps.length;
  const completed = allSteps.filter((step) => step.checked).length;
  return { total, completed, percentage: total === 0 ? 0 : Math.round((completed / total) * 100) };
}
```

Todo ヘッダの進捗 `(2/2 完了)` は UI 側で `todo.steps.filter((s) => s.checked).length` で計算。

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル                                          | 変更内容                                                                                                                              | 影響                                                                          |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `dashboard/lib/types.ts`                          | `TodoItem` を削除し `Step` / `Todo` 型を新設。`Gate.todos: Todo[]`、`PlanFile.todos: Todo[]` に変更                                   | 破壊的。`plan-parser.ts` / `plan-detail.tsx` / 2つのテストがすべて影響        |
| `dashboard/lib/plan-parser.ts`                    | h4 Todo パース、Step 詳細抽出、Review blockquote パース、フォールバックレイアウト、`parsePlanFile` 返り値を新構造に刷新               | PlanFile.gates/todos の構造が変わる。型経由で全下流に伝搬                     |
| `dashboard/components/plan-detail.tsx`            | Gate → Todo → Step の3階層アコーディオンに再構築。排他制御廃止、デフォルト全 open、Todo ヘッダに進捗、Step に description 表示       | `openGateId` state 廃止。`Collapsible` を2階層入れ子                          |
| `dashboard/__tests__/plan-parser.test.ts`         | 既存テストを新データ構造に書き直し（`result.todos` が `Todo[]` に、ネスト検証を追加）                                                 | 全テストケースの `expected` オブジェクトが変わる                              |
| `dashboard/__tests__/plan-parser-summary.test.ts` | rawMarkdown / summary テストはそのままでも通る可能性があるが、型変更で `result.todos` を参照している箇所があれば調整                  | 軽微（summary/rawMarkdown は新構造に依存しない）                              |

### 新規作成ファイル

| ファイル                                         | 内容                                                                                          |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| `dashboard/__tests__/plan-parser-hierarchy.test.ts` | 新規: h4 Todo パース、Step description フォールバック、Review blockquote パースの単体テスト |

### 変更しないファイル

| ファイル                                   | 理由                                                                                                      |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `dashboard/lib/github.ts`                  | マークダウン取得のみ。パーサーに渡すだけなので無影響                                                      |
| `dashboard/app/api/plans/route.ts`         | `parsePlanFile` の返り値をそのまま返す。型は自動的に新構造になる                                          |
| `dashboard/components/plan-card.tsx`       | 参照するのは `plan.title` / `plan.progress` / `plan.summary` / `plan.rawMarkdown` のみ。ネスト構造に触れない |
| `dashboard/components/plan-markdown-modal.tsx` | rawMarkdown しか使わない                                                                              |
| `dashboard/components/kanban-board.tsx`    | `plan.progress` しか見ない                                                                                |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル                                          | 目的                                                                         |
| ------------------------------------------------- | ---------------------------------------------------------------------------- |
| `dashboard/lib/plan-parser.ts`                    | 既存パース処理（`parseGates` / `parseTodos` / `maskCodeFences` / `stripMarkdown`）とパターン定義を理解 |
| `dashboard/lib/types.ts`                          | 現在の型定義を確認し破壊的変更の影響範囲を把握                               |
| `dashboard/components/plan-detail.tsx`            | 現在のアコーディオン構造（`openGateId` state / `Collapsible`）を理解         |
| `dashboard/__tests__/plan-parser.test.ts`         | 既存テストの形式（フラット bullet PLAN）と新形式へのマイグレ対象を把握       |
| `dashboard/__tests__/plan-parser-summary.test.ts` | summary/rawMarkdown テストを壊さないための制約を理解                         |
| `docs/PLAN/260410_kanban-card-detail.md`          | h4 Todo + Step サブ箇条書き構成の実物 PLAN（パース対象の代表例）             |
| `dashboard/components/ui/collapsible.tsx`         | shadcn Collapsible の API（defaultOpen, open, onOpenChange）                 |

## タスクリスト

### 依存関係図

```
Gate A: パーサー純粋関数（TDD 可能な抽出ロジック）
├── Todo 1: Step 説明抽出関数 + フォールバックチェーン [TDD]
└── Todo 2: Review blockquote パース関数 [TDD]

Gate B: 統合（型 + パーサー本体 + UI + 既存テスト更新）（Gate A 完了後）
├── Todo 3: 型刷新 + h4 Todo パース + parsePlanFile 統合 + 既存テスト更新
└── Todo 4: PlanDetail 3階層アコーディオン再構築
```

### Gate A: パーサー純粋関数（TDD 可能な抽出ロジック）

#### Todo 1: Step 説明抽出関数 + フォールバックチェーン

- [x] **Step 1 — IMPL**
  - **対象**: `dashboard/lib/plan-parser.ts`, `dashboard/__tests__/plan-parser-hierarchy.test.ts`（新規）
  - **内容**: `extractStepDescription(stepBlock: string): string` 関数を `plan-parser.ts` にエクスポート可能な純粋関数として追加し、単体テストを新規ファイルに書く
  - **実装詳細**:
    - 「アーキテクチャ詳細 > Step 説明の抽出」のコード例をそのまま実装
    - `export function extractStepDescription(...)` として外部から import 可能にする（テスト用）
    - `stripMarkdown` は既存関数を流用
    - `firstSentence(text)`: `text.split(/[。.!?！？]/)[0] + (マッチした区切り)` の簡易実装（ヘルパとして `plan-parser.ts` 内に private 関数で追加）
    - テストケース:
      - `内容` bullet あり → `内容` の値を返す
      - `内容` なし・`実装詳細` あり → `実装詳細` の第一文を返す
      - `内容` `実装詳細` なし・`対象` あり → `対象` の値を返す
      - すべてなし・最初の bullet が `- 任意テキスト` → その bullet テキストを返す
      - `依存` bullet しかない → 空文字を返す（依存は除外）
      - `[TDD]` bullet しかない → 空文字を返す（TDDマーカーは除外）
      - マークダウン記法（`**太字**`, `` `コード` ``, `[リンク](url)`) が除去される
  - **[TDD]**: 入出力が明確な純粋関数（マークダウン文字列 → プレーンテキスト文字列）
  - **依存**: なし

- [x] **Step 2 — Review A1**

  > **Review A1**: ✅ PASSED — 7テストケース全 PASS。仕様書通りのフォールバックチェーン + `\[[ xX]\]` 行除外の防御追加で Step ラベル誤マッチも回避

#### Todo 2: Review blockquote パース関数

- [x] **Step 1 — IMPL**
  - **対象**: `dashboard/lib/plan-parser.ts`, `dashboard/__tests__/plan-parser-hierarchy.test.ts`
  - **内容**: `parseReviewBlockquote(stepBlock: string)` を `plan-parser.ts` にエクスポート可能な純粋関数として追加し、書式ブレ3パターン以上をカバーする単体テストを追加
  - **実装詳細**:
    - 「アーキテクチャ詳細 > Review blockquote のパース」のコード例をそのまま実装
    - 戻り値の型: `{ hasReview, reviewFilled, reviewResult, reviewFixCount, summary }`
    - テストケース（必須）:
      1. `> **Review A2**: ✅ PASSED (FIX 1回) — commits a05e43f, d57675a\n> - 初回レビューで [P2] ...` → `reviewResult: 'PASSED'`, `reviewFixCount: 1`, `summary: 'コードブロック内 ## 誤検出...'`（2行目の bullet を採用する代わりに `—` 以降がある場合は1行目を優先）
      2. `> **Review A1**: ⏭️ SKIPPED (型定義のみ、ロジック変更なし) — commit a05e43f` → `reviewResult: 'SKIPPED'`, `reviewFixCount: null`, `summary: '(型定義のみ、ロジック変更なし)'`（括弧は残すかは実装判断、テストは `toContain` で緩く）
      3. `> **Review B1**: ✅ PASSED — react-markdown ^10.1.0 を追加` → `reviewResult: 'PASSED'`, `summary: 'react-markdown ^10.1.0 を追加'`
      4. `> **Review A1**:`（空） → `hasReview: true, reviewFilled: false, reviewResult: null, summary: ''`
      5. blockquote が存在しない Step → `hasReview: false`
      6. `> **Review C1**: FAILED — テスト実行エラー` → `reviewResult: 'FAILED'`
      7. commit hash 除去: `— commits abc123, def456 を参照` → `summary` に `commits abc123, def456` が含まれない
  - **[TDD]**: 入出力が明確な純粋関数
  - **依存**: なし

- [x] **Step 2 — Review A2**

  > **Review A2**: ✅ PASSED — reviewer-correctness 4観点すべて PASS / N/A。ストーリー適合・API/SDK 準拠・リスク前提・セキュリティすべて問題なし。信頼度80以上の指摘ゼロ。14/14 テスト PASS。

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること。`extractStepDescription` と `parseReviewBlockquote` が独立してテスト可能で、書式ブレ3パターン以上をカバーするテストがすべて PASS すること。

### Gate B: 統合（型 + パーサー本体 + UI + 既存テスト更新）

#### Todo 3: 型刷新 + h4 Todo パース + parsePlanFile 統合 + 既存テスト更新

- [x] **Step 1 — IMPL**
  - **対象**: `dashboard/lib/types.ts`, `dashboard/lib/plan-parser.ts`, `dashboard/__tests__/plan-parser.test.ts`, `dashboard/__tests__/plan-parser-summary.test.ts`
  - **内容**: 型を破壊的に刷新し、`parsePlanFile` が Gate → Todo → Step の3階層を返すように統合する。既存テストを新データ構造に書き直す
  - **実装詳細**:
    - **types.ts**:
      - `TodoItem` を削除、`Step`, `Todo`, `StepKind`, `ReviewResult` を「アーキテクチャ詳細 > データモデル」の通り追加
      - `Gate.todos: Todo[]`、`PlanFile.todos: Todo[]` に変更
    - **plan-parser.ts**:
      - `H4_TODO_PATTERN`, `STEP_IMPL_PATTERN`, `STEP_REVIEW_PATTERN` の3パターンを上部に追加
      - 既存 `parseTodos(content)` を `parseSteps(content)` にリネームし、戻り値を `Step[]` に（`extractStepDescription` / `parseReviewBlockquote` を呼び出して description/reviewResult/reviewFixCount などを埋める。`kind` は `STEP_IMPL_PATTERN` / `STEP_REVIEW_PATTERN` で判定）
      - 新規 `parseGateTodos(gateContent: string): Todo[]` を追加。ロジック:
        1. `maskCodeFences(gateContent)` で h4 を探す
        2. h4 が1つ以上あれば、各 h4 セクションを `Todo` として構築し、セクション内で `parseSteps` を呼ぶ
        3. h4 が0個なら、`parseSteps(gateContent)` を呼び、各 Step を 1 Todo に wrap する（title は Step title と同じ、`steps: [step]`）← 非テンプレ PLAN フォールバック
      - `parseGates` を更新: `todos: parseGateTodos(section)` に変更
      - `calculateProgress(todos: Todo[])`: `todos.flatMap((t) => t.steps)` でフラット化してカウント
      - `determineStatus(todos: Todo[], ...)`: 同様にフラット化した Step 列でステータス判定
      - `parsePlanFile` の `const todos = gates.length > 0 ? gates.flatMap((gate) => gate.todos) : parseGateTodos(content)` に変更
    - **plan-parser.test.ts**: 既存7ケースを新データ構造に書き直す
      - 例: 現状 `result.todos: [{title: 'Todo A1', checked: true, hasReview: true, reviewFilled: true}]` → 新 `result.todos: [{title: 'Todo A1', steps: [{title: 'Todo A1', checked: true, kind: 'impl', description: '', hasReview: true, reviewFilled: true, reviewResult: 'PASS' もしくは null, reviewFixCount: null}]}]`
      - フラット bullet PLAN（`- [x] **Todo A1**: 環境構築`）は「各 bullet が 1 Todo = 1 Step」のフォールバックで動作することを検証
      - `progress` テストは Step 単位カウントで期待値を更新
      - `gates[].todos` の検証も新構造に合わせる
    - **plan-parser-summary.test.ts**: `result.summary` / `result.rawMarkdown` のテストは基本通る想定だが、`result.todos` に触れる箇所があれば修正（現状は触れていない）
  - **依存**: Todo 1（`extractStepDescription`）, Todo 2（`parseReviewBlockquote`）

- [x] **Step 2 — Review B1**

  > **Review B1**: ✅ PASSED — 複雑モード3観点並列レビュー (quality / correctness / conventions) すべて PASS。信頼度 80 以上の指摘ゼロ。36/36 テスト PASS、`npm run build` 成功。`plan-detail.tsx` は Todo 4 までの暫定コンパイルシムとして allSteps.flatMap で対応。

#### Todo 4: PlanDetail 3階層アコーディオン再構築

- [ ] **Step 1 — IMPL**
  - **対象**: `dashboard/components/plan-detail.tsx`
  - **内容**: Gate → Todo → Step の3階層アコーディオンに再構築。Gate 排他制御を廃止、デフォルト全 open、Todo ヘッダに進捗、Step に description と Review ラベルを表示
  - **実装詳細**:
    - 既存の `useState<string | null>(defaultGateId)` による Gate 排他制御を**削除**
    - 各 `Collapsible` に `defaultOpen` を付与（`open` / `onOpenChange` は Collapsible 内部の state に委ねる）
    - 外側ループ: `gates.map` → 各 Gate を `<Collapsible defaultOpen>` でラップ。Gate ヘッダは `{gate.id}: {gate.title}` のみ（進捗は出さない）、右端に `<ChevronDown>`
    - 内側ループ: `gate.todos.map` → 各 Todo を `<Collapsible defaultOpen>` でラップ。Todo ヘッダは `{todo.title}` + `{completedSteps}/{todo.steps.length} 完了` + `<ChevronDown>`
    - Step リスト: `todo.steps.map` → 「アーキテクチャ詳細 > UI 構造」の `StepRow` 相当をインラインで実装
      - `step.checked` で `<Check>` / `<Circle>`
      - Step タイトル + 2行目に `description`（`text-muted-foreground text-xs pl-6 line-clamp-2`）
      - `step.kind === 'review' && step.hasReview && step.reviewFilled` のとき結果バッジ表示（`step.reviewResult ?? 'Review済'` + `FIX N回` があれば併記）
    - 概要ブロック（`plan.summary` + `<Separator />`）は現行のまま維持
    - 既存の `gate.todos.length === 0` の空状態表示は、`gate.todos.flatMap((t) => t.steps).length === 0` で判定するように更新
    - key 生成: `${plan.projectName}/${plan.filePath}-gate-${gateIndex}`, `-todo-${todoIndex}`, `-step-${stepIndex}` で衝突回避
    - アクセシビリティ: `CollapsibleTrigger` に `aria-label={`${gate.title} の Todo を開閉`}` 等を付与
  - **依存**: Todo 3（新型定義・新 parsePlanFile）

- [ ] **Step 2 — Review B2**

  > **Review B2**: [記入欄]

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること。ビルド（`npm run build` または `next build`）と全テスト（`npm test`）が成功すること。ブラウザで既存 PLAN (`docs/PLAN/260410_kanban-card-detail.md` 相当のデータ) を表示して Gate → Todo → Step の3階層が正しく表示され、Step に1行説明が出ていること。

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク                                                       | 影響                                                                                       | 緩和策                                                                                                               |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| 既存テストの広範な書き換え                                   | `plan-parser.test.ts` の全ケースで `expected` が変わる。マイグレ誤りで回帰の恐れ           | Todo 3 の Step 1 で1ケースずつ丁寧に更新。Gate B 通過条件にテスト全 PASS を含める                                    |
| Review blockquote の書式ブレ                                 | `parseReviewBlockquote` が新しいブレに遭遇すると `reviewResult: null` でフォールバック     | 7パターンの単体テストで主要ブレをカバー。`null` 時は `'Review済'` で UI は破綻しない                                |
| 非テンプレ PLAN のフォールバックで Todo タイトルが Step タイトルと重複する | 見た目として冗長（Todo タイトル = `- [x] **Todo A1**` の Step タイトルと同じ）           | 実装上は許容。フォールバック挙動が予測可能になる方が優先度高い。将来的に Todo タイトルのみ表示する条件分岐で対応可能 |
| デフォルト全 open による縦スクロール増加                     | Gate/Todo が多い PLAN でカードが非常に長くなる                                             | ユーザーが手動で畳めるのでアコーディオン自体は残す。Step 数が極端に多い場合は PLAN 側の分割を推奨                    |
| 進捗計算が Step 単位になることで数値が現状より増える         | 例: 現状「13/15 完了」が「26/30 完了」等に変わる（Step 1 IMPL + Step 2 Review で2倍）      | 既存カード全体進捗バーの意味は温存（Step 単位なのでむしろ粒度が揃う）。ユーザー説明不要と判断                         |
| `[TDD]` bullet 等の特殊 bullet がフォールバックチェーンに引っかかる | 非テンプレ PLAN で TDD bullet しかない Step で description が空になる可能性               | `extractStepDescription` の最後のフォールバックで `依存` / `[TDD]` bullet を明示的にスキップする除外ロジックを実装   |
