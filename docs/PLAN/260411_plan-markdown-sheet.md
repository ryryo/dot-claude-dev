# PlanMarkdownModal を右スライド Sheet に変更

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

---

## 概要

カンバンビューとテーブルビューで共通して使われる `PlanMarkdownModal` を、中央表示の `Dialog` から右スライドの `Sheet` に変更する。`FileText` アイコンをクリックすると右から Markdown 全文パネルがスライドインするようになる。

## 背景

現在の `PlanMarkdownModal` は `Dialog`（中央ポップアップ）で表示しているが、マークダウンの全文閲覧には右スライドの Sheet の方が広い縦スペースを活かせる。既存の `Sheet` コンポーネントがあるためライブラリ追加不要。

## 設計決定事項

| # | トピック | 決定 | 根拠 |
|---|----------|------|------|
| 1 | コンポーネント | `dialog/components/ui/sheet.tsx` をそのまま使用 | 既存実装あり、追加インストール不要 |
| 2 | Sheet 幅 | `style={{ maxWidth: '48rem' }}` | マークダウンの読みやすい幅。SheetContent のデフォルト `sm:max-w-sm` を上書き |
| 3 | スクロール | `ScrollArea` を使用 | Sheet 内コンテンツが長い場合に備える |
| 4 | タイトル表示 | `SheetHeader` + `SheetTitle` に `title` prop を表示 | Dialog では非表示だったが、Sheet では何のドキュメントか識別できた方が良い |
| 5 | コンポーネント名 | `PlanMarkdownModal` のまま維持 | 呼び出し側（plan-card.tsx / plan-table.tsx）の変更を最小化 |

## アーキテクチャ詳細

### 変更前後

```
【変更前】
PlanMarkdownModal
  └── Dialog
        └── DialogContent (max-w-3xl, 中央表示)
              └── div (max-h-[80vh] overflow-y-auto)
                    └── Markdown

【変更後】
PlanMarkdownModal
  └── Sheet
        └── SheetContent (side="right", maxWidth: 48rem, flex-col, p-0)
              ├── SheetHeader (px-6 py-4 border-b shrink-0)
              │     └── SheetTitle
              └── ScrollArea (flex-1 min-h-0)
                    └── div (px-6 py-4 prose prose-sm dark:prose-invert)
                          └── Markdown
```

### Sheet コンポーネント構造

```tsx
<Sheet open={open} onOpenChange={onOpenChange}>
  <SheetContent side="right" className="flex flex-col p-0" style={{ maxWidth: '48rem' }}>
    <SheetHeader className="px-6 py-4 border-b shrink-0">
      <SheetTitle>{title}</SheetTitle>
    </SheetHeader>
    <ScrollArea className="flex-1 min-h-0">
      <div className="prose prose-sm dark:prose-invert max-w-none px-6 py-4">
        <Markdown remarkPlugins={[remarkGfm]}>{markdown}</Markdown>
      </div>
    </ScrollArea>
  </SheetContent>
</Sheet>
```

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
|----------|----------|------|
| `dashboard/components/plan-markdown-modal.tsx` | Dialog → Sheet に置き換え、SheetHeader・ScrollArea を追加 | カンバン・テーブル両ビューに自動反映 |

### 変更しないファイル

| ファイル | 理由 |
|----------|------|
| `dashboard/components/plan-card.tsx` | `PlanMarkdownModal` の呼び出しインターフェース（props）は変わらないため変更不要 |
| `dashboard/components/plan-table.tsx` | 同上 |
| `dashboard/components/ui/sheet.tsx` | 既存コンポーネントをそのまま使用 |
| `dashboard/components/ui/scroll-area.tsx` | 既存コンポーネントをそのまま使用 |

## 参照すべきファイル

### コードベース内

| ファイル | 目的 |
|----------|------|
| `dashboard/components/plan-markdown-modal.tsx` | 変更元。現在の Dialog 構造を確認 |
| `dashboard/components/ui/sheet.tsx` | Sheet/SheetContent/SheetHeader/SheetTitle の API |
| `dashboard/components/ui/scroll-area.tsx` | ScrollArea の API |

## タスクリスト

### 依存関係図

```
Gate A: PlanMarkdownModal Sheet 化
└── Todo A1: Dialog → Sheet に置き換え
```

---

### Gate A: PlanMarkdownModal Sheet 化

#### Todo A1: Dialog → Sheet に置き換え

- [ ] **Step 1 — IMPL**
  - **対象**: `dashboard/components/plan-markdown-modal.tsx`
  - **内容**: `Dialog`/`DialogContent` を `Sheet`/`SheetContent` に置き換え、`SheetHeader` + `ScrollArea` を追加
  - **実装詳細**:
    1. import を更新:
       ```tsx
       // 削除
       import { Dialog, DialogContent } from "@/components/ui/dialog"
       // 追加
       import { ScrollArea } from "@/components/ui/scroll-area"
       import {
         Sheet,
         SheetContent,
         SheetHeader,
         SheetTitle,
       } from "@/components/ui/sheet"
       ```
    2. return 文を書き換え:
       ```tsx
       return (
         <Sheet open={open} onOpenChange={onOpenChange}>
           <SheetContent side="right" className="flex flex-col p-0" style={{ maxWidth: '48rem' }}>
             <SheetHeader className="px-6 py-4 border-b shrink-0">
               <SheetTitle>{title}</SheetTitle>
             </SheetHeader>
             <ScrollArea className="flex-1 min-h-0">
               <div className="prose prose-sm dark:prose-invert max-w-none px-6 py-4">
                 <Markdown remarkPlugins={[remarkGfm]}>{markdown}</Markdown>
               </div>
             </ScrollArea>
           </SheetContent>
         </Sheet>
       )
       ```
  - **依存**: なし

- [ ] **Step 2 — Review A1**

  > | 検証項目 | 結果 | コメント |
  > |---------|------|---------|
  > | FileText アイコンをクリックすると右から Sheet がスライドインする | | |
  > | SheetHeader にプランタイトルが表示される | | |
  > | マークダウン全文がレンダリングされる | | |
  > | コンテンツが長い場合にスクロールできる | | |
  > | × ボタンまたは Sheet 外クリックで閉じられる | | |

**Gate A 通過条件**: `FileText` アイコンをクリックすると右から Sheet がスライドインし、タイトルとマークダウン全文が表示される。スクロール・閉じる動作が正常。全 Review 結果記入欄が埋まり、総合判定が PASS であること

---

## レビューステータス

- [ ] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| `SheetContent` の `data-[side=right]:sm:max-w-sm` クラスと `style.maxWidth` が競合する | Sheet 幅が想定より狭くなる可能性 | `style={{ maxWidth: '48rem' }}` はインラインスタイルで CSS specificity が高いため優先される |
