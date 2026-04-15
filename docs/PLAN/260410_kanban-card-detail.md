# 看板カード詳細表示の改善（概要表示 + 全文モーダル）

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

---

## 概要

看板ボードのPLANカード展開時に「概要」テキストを表示し、カードヘッダーから「全体を読む」モーダルでマークダウン全文を閲覧できるようにする。現状はGate/Todoステップ一覧のみの表示を、概要 → ステップ一覧の縦並びレイアウトに拡張し、全文閲覧はモーダルで提供する。

## 背景

現在のカード展開時はGate内のTodoステップ一覧しか表示されず、PLANの目的や背景を把握するには元のマークダウンファイルを直接開く必要がある。概要を展開カード内に表示し、全文閲覧モーダルを追加することで、ダッシュボード上だけでPLANの全体像を把握できるようにする。

## 設計決定事項

| # | トピック | 決定 | 根拠 |
|---|----------|------|------|
| 1 | 概要ソース | `## 概要` セクションをパース。なければ `# タイトル` 直後〜最初の `##` までをフォールバック | テンプレートで `## 概要` は必須。AIが崩す場合のフォールバックも確保 |
| 2 | 概要の表示形式 | プレーンテキスト化（md記法除去） | カード内の一覧性を維持。軽量 |
| 3 | 全文表示UI | モーダル/ダイアログ | 看板レイアウトを崩さない |
| 4 | レンダリング方式 | APIレスポンスに rawMarkdown を追加 + フロントで react-markdown | 追加GitHub API呼び出しゼロ（パース時に既に取得済み） |
| 5 | 「全体を読む」ボタン配置 | カードヘッダーにアクションアイコン | 展開しなくても全文アクセス可能 |
| 6 | モーダルスタイリング | Tailwind Typography（prose クラス） | 導入簡単・保守軽量 |
| 7 | カードレイアウト | 概要 → ステップ一覧（縦並び） | 自然な読み順 |

## アーキテクチャ詳細

### データフロー

```
GitHub API → fetchFileContent() → content(生md)
  → parsePlanFile(content, ...)
    → parseSummary(content) → summary (プレーンテキスト)
    → rawMarkdown = content (そのまま)
  → API Response: { ...既存フィールド, summary, rawMarkdown }
  → フロント:
    → PlanDetail: summary をプレーンテキスト表示
    → PlanCard: FileText アイコン → PlanMarkdownModal(rawMarkdown)
```

### 型定義の変更

```typescript
// dashboard/lib/types.ts - PlanFile に追加
export interface PlanFile {
  // ...既存フィールド
  summary: string;       // ## 概要 のプレーンテキスト（md記法除去済み）
  rawMarkdown: string;   // 生マークダウン全文
}
```

### 概要パースロジック

```typescript
// dashboard/lib/plan-parser.ts
const SUMMARY_SECTION_PATTERN = /^## 概要\s*\n([\s\S]*?)(?=\n## |\n---\s*$|$)/m;
const INTRO_TEXT_PATTERN = /^# .+\n+([\s\S]*?)(?=\n## )/m;

function parseSummary(content: string): string {
  // 1. ## 概要 セクションを探す
  const summaryMatch = content.match(SUMMARY_SECTION_PATTERN);
  if (summaryMatch) {
    return stripMarkdown(summaryMatch[1].trim());
  }
  // 2. フォールバック: タイトル直後〜最初の ## まで
  const introMatch = content.match(INTRO_TEXT_PATTERN);
  if (introMatch) {
    return stripMarkdown(introMatch[1].trim());
  }
  return '';
}

function stripMarkdown(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1')     // 太字
    .replace(/\*(.+?)\*/g, '$1')          // 斜体
    .replace(/`(.+?)`/g, '$1')            // インラインコード
    .replace(/\[(.+?)\]\(.+?\)/g, '$1')   // リンク
    .replace(/^[-*+]\s+/gm, '')           // リスト記号
    .replace(/^\d+\.\s+/gm, '')           // 番号付きリスト
    .replace(/^>\s+/gm, '')               // 引用
    .replace(/^#{1,6}\s+/gm, '')          // 見出し
    .replace(/\n{3,}/g, '\n\n')           // 連続改行を圧縮
    .trim();
}
```

### PlanMarkdownModal コンポーネント

```typescript
// dashboard/components/plan-markdown-modal.tsx
interface PlanMarkdownModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  markdown: string;
}
```

- shadcn `Dialog` を使用（既存 `dashboard/components/ui/dialog.tsx`）
- `react-markdown` でレンダリング
- `@tailwindcss/typography` の `prose` クラスでスタイリング
- サイズ: `max-w-3xl`, `max-h-[80vh]`, `overflow-y-auto`

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
|----------|----------|------|
| `dashboard/lib/types.ts` | `PlanFile` に `summary`, `rawMarkdown` フィールド追加 | 型を参照する全コンポーネントに影響（既存フィールドは変更なし） |
| `dashboard/lib/plan-parser.ts` | `parseSummary`, `stripMarkdown` 関数追加。`parsePlanFile` の返り値に2フィールド追加 | APIレスポンスのサイズが増加（rawMarkdown分） |
| `dashboard/components/plan-detail.tsx` | Gate一覧の上部に概要テキスト表示を追加 | レイアウト変更（概要 → Gate一覧の縦並び） |
| `dashboard/components/plan-card.tsx` | ヘッダーに FileText アイコンボタン追加、PlanMarkdownModal を組み込み | カードヘッダーのレイアウト変更 |
| `dashboard/package.json` | `react-markdown`, `@tailwindcss/typography` を dependencies に追加 | バンドルサイズ増加 |
| `dashboard/app/globals.css` | `@plugin "@tailwindcss/typography";` を追加 | prose クラスが有効化される |

### 新規作成ファイル

| ファイル | 内容 |
|----------|------|
| `dashboard/components/plan-markdown-modal.tsx` | マークダウン全文表示モーダルコンポーネント |
| `dashboard/__tests__/plan-parser-summary.test.ts` | 概要パースのユニットテスト |

### 変更しないファイル

| ファイル | 理由 |
|----------|------|
| `dashboard/lib/github.ts` | 既にファイル内容を取得済み。変更不要 |
| `dashboard/app/api/plans/route.ts` | `parsePlanFile` の返り値をそのまま返すため変更不要 |
| `dashboard/components/kanban-board.tsx` | PlanCard に渡す props は `PlanFile` のまま。変更不要 |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
|----------|------|
| `dashboard/lib/plan-parser.ts` | 既存パース処理のパターンを理解 |
| `dashboard/lib/types.ts` | PlanFile 型の現在の定義を確認 |
| `dashboard/components/plan-card.tsx` | カードヘッダーの構造を理解 |
| `dashboard/components/plan-detail.tsx` | 展開コンテンツの構造を理解 |
| `dashboard/components/ui/dialog.tsx` | shadcn Dialog の使い方（base-ui/react ベース）を確認 |
| `dashboard/__tests__/plan-parser.test.ts` | 既存テストのパターンを確認 |

## タスクリスト

### 依存関係図

```
Gate A: データ層（型 + パーサー + テスト）
├── Todo 1: PlanFile 型拡張
├── Todo 2: 概要パースロジック追加（Todo 1 完了後）
└── Todo 3: ユニットテスト追加（Todo 2 完了後）

Gate B: UI層（依存パッケージ + コンポーネント）（Gate A 完了後）
├── Todo 4: 依存パッケージインストール
├── Todo 5: マークダウンモーダル作成（Todo 4 完了後）
├── Todo 6: PlanDetail 概要表示追加
└── Todo 7: PlanCard アクションアイコン追加（Todo 5 完了後）
```

### Gate A: データ層（型 + パーサー + テスト）

#### Todo 1: PlanFile 型に summary と rawMarkdown フィールドを追加

- [x] **Step 1 — IMPL**
  - **対象**: `dashboard/lib/types.ts`
  - **内容**: `PlanFile` インターフェースに `summary: string` と `rawMarkdown: string` を追加
  - **実装詳細**: 既存フィールド（`progress` の後）に2行追加。他の型定義は変更しない
  - **依存**: なし

- [x] **Step 2 — Review A1**

  > **Review A1**: ⏭️ SKIPPED (型定義のみ、ロジック変更なし) — commit a05e43f
  > | 項目 | 結果 | 備考 |
  > |------|------|------|
  > | 型定義の正確性 | ✅ | PlanFile に `summary: string` / `rawMarkdown: string` を追加 |
  > | 既存フィールドへの影響なし | ✅ | 既存フィールド順は維持 |
  > | **総合判定** | ✅ PASS | |

#### Todo 2: plan-parser に概要抽出ロジックを追加

- [x] **Step 1 — IMPL**
  - **対象**: `dashboard/lib/plan-parser.ts`
  - **内容**: `parseSummary(content)` と `stripMarkdown(text)` 関数を追加し、`parsePlanFile` の返り値に `summary` と `rawMarkdown` を含める
  - **実装詳細**: 「アーキテクチャ詳細 > 概要パースロジック」のコード例に従う。正規表現パターンは `SUMMARY_SECTION_PATTERN` と `INTRO_TEXT_PATTERN` をファイル上部の既存パターン群の後に定義。`parsePlanFile` の return オブジェクトに `summary: parseSummary(content)` と `rawMarkdown: content` を追加
  - **[TDD]**: 入出力が明確（マークダウン文字列 → プレーンテキスト文字列）
  - **依存**: Todo 1（型定義）

- [x] **Step 2 — Review A2**

  > **Review A2**: ✅ PASSED (FIX 1回) — commits a05e43f, d57675a
  > - 初回レビューで [P2] コードブロック内 `##` 誤検出、[P3] 空 `## 概要` フォールバック未実装を指摘 → `maskCodeFences` 追加 + 空時フォールバックで修正
  > - 再レビュー: regression なし
  >
  > | 項目 | 結果 | 備考 |
  > |------|------|------|
  > | parseSummary の正規表現が正しい | ✅ | コードブロックは事前マスクしてから検索 |
  > | フォールバックロジック | ✅ | `## 概要` なし/空の両方でタイトル直後に流れる |
  > | stripMarkdown の変換精度 | ✅ | 太字/斜体/リンク/リスト/引用/見出しを除去 |
  > | parsePlanFile の返り値に含まれる | ✅ | `summary` + `rawMarkdown` 両方 |
  > | **総合判定** | ✅ PASS | |

#### Todo 3: 概要パースのユニットテストを追加

- [x] **Step 1 — IMPL**
  - **対象**: `dashboard/__tests__/plan-parser-summary.test.ts`（新規）
  - **内容**: `parseSummary` のテストケース3パターン + `stripMarkdown` のテストケース + `parsePlanFile` で summary/rawMarkdown が返ることの統合テスト
  - **実装詳細**: 既存の `dashboard/__tests__/` のテストパターンに従い vitest で作成。テストケース: (1) `## 概要` あり → テキスト抽出 (2) `## 概要` なし・冒頭テキストあり → フォールバック (3) 両方なし → 空文字 (4) マークダウン記法の除去（太字、リンク、リスト等）(5) parsePlanFile が summary と rawMarkdown を返すこと
  - **[TDD]**
  - **依存**: Todo 2（パース関数）

- [x] **Step 2 — Review A3**

  > **Review A3**: ⏭️ SKIPPED (test-only file addition) — commit 0178eb0
  > - 新規 7 テスト全 PASS、既存 plan-parser.test.ts 8 テスト影響なし
  >
  > | 項目 | 結果 | 備考 |
  > |------|------|------|
  > | 3パターンのカバレッジ | ✅ | `## 概要`あり / フォールバック / 両方なし |
  > | stripMarkdown テストケース | ✅ | 太字・斜体・リンク・コード・リスト除去を検証 |
  > | 統合テスト（parsePlanFile） | ✅ | summary + rawMarkdown 両方を検証 |
  > | テスト全件 PASS | ✅ | 新規 7/7、既存 8/8 |
  > | **総合判定** | ✅ PASS | |

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: UI層（依存パッケージ + コンポーネント）

#### Todo 4: 依存パッケージをインストール

- [x] **Step 1 — IMPL**
  - **対象**: `dashboard/package.json`
  - **内容**: `react-markdown` と `@tailwindcss/typography` を追加
  - **実装詳細**: `cd dashboard && npm install react-markdown @tailwindcss/typography` を実行。`dashboard/app/globals.css` の先頭 `@import` ブロックの後に `@plugin "@tailwindcss/typography";` を追加（Tailwind CSS 4 でプラグインを有効化する記法）
  - **依存**: なし

- [x] **Step 2 — Review B1**

  > **Review B1**: ✅ PASSED — `@tailwindcss/typography ^0.5.19`, `react-markdown ^10.1.0`, `remark-gfm ^4.0.1` を追加。ネットワーク不通により `~/.npm/_cacache/` のtarball経由でオフラインインストール後、`package.json` を通常の semver 参照に書き戻し。
  > | 項目 | 結果 | 備考 |
  > |------|------|------|
  > | パッケージインストール成功 | ✅ | semver 参照で dependencies に記録済み |
  > | globals.css に @plugin 追加済み | ✅ | `@import` ブロックの直後に追加 |
  > | **総合判定** | ✅ PASS | |

#### Todo 5: マークダウンモーダルコンポーネントを作成

- [x] **Step 1 — IMPL**
  - **対象**: `dashboard/components/plan-markdown-modal.tsx`（新規）
  - **内容**: `PlanMarkdownModal` コンポーネントを作成。Props: `open`, `onOpenChange`, `title`, `markdown`
  - **実装詳細**: 既存の `dashboard/components/ui/dialog.tsx` の Dialog を使用。`react-markdown` の `<Markdown>` コンポーネントで rawMarkdown をレンダリング。`prose` クラス（@tailwindcss/typography）でスタイリング。モーダルサイズは `max-w-3xl`、コンテンツ領域は `max-h-[80vh] overflow-y-auto`。DialogTitle に plan.title を表示
  - **依存**: Todo 4（パッケージ）

- [x] **Step 2 — Review B2**

  > **Review B2**: ✅ PASSED (FIX 1回) — 初回 [P2] 指摘: react-markdown 既定では GFM 非対応で PLAN のテーブル/タスクリストが生テキスト表示。`remark-gfm` を追加し `remarkPlugins={[remarkGfm]}` を適用して修正。
  > | 項目 | 結果 | 備考 |
  > |------|------|------|
  > | Dialog の使い方が既存パターンに準拠 | ✅ | shadcn Dialog + DialogHeader/DialogTitle |
  > | react-markdown レンダリング動作 | ✅ | remark-gfm プラグイン有効 |
  > | prose スタイリング適用 | ✅ | `prose prose-sm dark:prose-invert` |
  > | スクロール・サイズ | ✅ | `max-w-3xl max-h-[80vh] overflow-y-auto` |
  > | **総合判定** | ✅ PASS | |

#### Todo 6: PlanDetail に概要テキスト表示を追加

- [x] **Step 1 — IMPL**
  - **対象**: `dashboard/components/plan-detail.tsx`
  - **内容**: Gate 一覧の上部に概要テキストを表示
  - **実装詳細**: return の `<div className="space-y-3">` 内、Gate の map の前に概要セクションを追加。`plan.summary` が空でない場合のみ表示。スタイル: `text-muted-foreground text-sm` のパラグラフ。概要とGate一覧の間に `<Separator />` を挿入
  - **依存**: Todo 1, 2（summary フィールド）

- [x] **Step 2 — Review B3**

  > **Review B3**: ✅ PASSED (FIX 1回) — 初回 [P2] 指摘: gates が空の early return により summary が非表示になる。早期 return を削除し `space-y-3` 内で summary → gates 空時の placeholder の順に表示する構造へ修正。
  > | 項目 | 結果 | 備考 |
  > |------|------|------|
  > | 概要テキスト表示（summary あり） | ✅ | `whitespace-pre-wrap` で改行維持 |
  > | 概要なし時の非表示 | ✅ | `plan.summary ? ... : null` |
  > | レイアウト（概要 → Gate一覧） | ✅ | gates 空の場合でも summary は表示 |
  > | **総合判定** | ✅ PASS | |

#### Todo 7: PlanCard ヘッダーに「全体を読む」アクションアイコンを追加

- [x] **Step 1 — IMPL**
  - **対象**: `dashboard/components/plan-card.tsx`
  - **内容**: ChevronDown の横に FileText アイコンボタンを追加。クリックで PlanMarkdownModal を開く
  - **実装詳細**: `lucide-react` の `FileText` アイコンを import。ChevronDown の左に配置。`useState<boolean>` で modalOpen を管理。`onClick` ハンドラで `e.stopPropagation()` を呼び CollapsibleTrigger のイベントに干渉しない。`<PlanMarkdownModal open={modalOpen} onOpenChange={setModalOpen} title={plan.title} markdown={plan.rawMarkdown} />` を Card 内に配置。アイコンボタンのスタイル: `text-muted-foreground hover:text-foreground transition-colors size-4`
  - **依存**: Todo 5（モーダルコンポーネント）

- [x] **Step 2 — Review B4**

  > **Review B4**: ✅ PASSED (FIX 2回) — (1) 当初 CollapsibleTrigger（`<button>`）内に FileText `<button>` をネストしていたため HTML 非準拠になる問題を Claude の自己レビューで検出 → Card 直下に絶対配置の兄弟要素として再配置。(2) Agent レビューで [P1] 狭幅カラム時に絶対配置ボタンがタイトルに重なる懸念を検出 → タイトル flex 行に `pr-6` と `min-w-0` を付与。
  > | 項目 | 結果 | 備考 |
  > |------|------|------|
  > | アイコンクリックでモーダル表示 | ✅ | `setModalOpen(true)` |
  > | stopPropagation 動作（カード展開に干渉しない） | ✅ | `e.stopPropagation()` |
  > | モーダル閉じた後の状態 | ✅ | Collapsible の外に PlanMarkdownModal を配置 |
  > | HTML 構造（ネストボタン回避） | ✅ | FileText を CollapsibleTrigger 外に配置 |
  > | 狭幅カラムでの重なり回避 | ✅ | `pr-6` + `min-w-0` でスペース確保 |
  > | **総合判定** | ✅ PASS | |

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

## レビューステータス

- [x] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| APIレスポンスサイズ増加（rawMarkdown追加分） | 大量のPLANファイルがある場合にロード時間が増える | 現在のPLANファイル数では問題なし。将来的にはページネーションや遅延ロードで対応可能 |
| react-markdown のバンドルサイズ | フロントエンドの初期ロード時間が増える | dynamic import でモーダル表示時のみロードすることで軽減可能 |
| `## 概要` セクションが空の場合 | 概要欄が表示されない | フォールバック（冒頭テキスト）で対応。両方空なら概要セクション自体を非表示 |
