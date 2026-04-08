# PLAN Dashboard デザインリニューアル

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

---

## 概要

PLAN Dashboard の UI を `dashboard/DESIGN.md`（STUDIO デザインシステム）に完全準拠させるビジュアルリニューアル。フォント・カラー・タイポグラフィの基盤刷新、レスポンシブ対応、Critical/Medium QA 指摘（D1〜D21）の修正を行う。データ層・API・ビジネスロジックは変更しない。

## 背景

初回実装（260408_plan-dashboard）は機能要件（8プロジェクト112 PLAN、4ステータスカンバン）をすべて満たしたが、デザイン面で深刻な問題がある：

1. **DESIGN.md との乖離**: Inter フォント未導入、mauve（紫系）カラーテーマ、Arial 上書き等
2. **レスポンシブ未対応**: ブレークポイント皆無、モバイルで使用不可
3. **KanbanBoard 未接続**: コンポーネントは実装済みだが page.tsx がプレースホルダーを表示
4. **QA 指摘 39 件**: Critical 3 / Medium 21 を今回のスコープで修正

## 設計決定事項

| #   | トピック | 決定 | 根拠 |
| --- | -------- | ---- | ---- |
| 1   | カラーテーマ | 現在の mauve（紫系）OKLCH パレットをそのまま維持 | ユーザー判断。紫系のブランドカラーを採用 |
| 2   | フォント | `Inter` + `Noto Sans JP` + `IBM Plex Mono` の 3 フォント体制 | DESIGN.md 仕様。Inter は欧文優先、Noto Sans JP は和文フォールバック、IBM Plex Mono はラベル用 |
| 3   | カラー形式 | OKLCH をそのまま維持 | shadcn/ui base-nova プリセットとの互換性を保つ |
| 4   | レスポンシブ戦略 | モバイル: ハンバーガー + ドロワーサイドバー / タブレット: 折りたたみサイドバー / デスクトップ: 固定サイドバー | DESIGN.md のブレークポイント定義（≤768px / ≤1024px / >1024px）に準拠 |
| 5   | カンバン列レスポンシブ | モバイル: snap-scroll 横スワイプ / タブレット: 2列 grid / デスクトップ: 4列 grid | モバイルでもカンバンの視覚メタファーを維持。タブレット以上は grid で表示 |
| 6   | ローディング状態 | テキストのみ → スケルトン UI | CLS 軽減（QA D20）、プロフェッショナルな印象 |
| 7   | サイドバー実装 | shadcn/ui の Sidebar コンポーネント（SidebarProvider + collapsible）を採用 | shadcn Sidebar は自動モバイル Sheet 変換を内蔵。`collapsible="icon"` でタブレット時にアイコンレールに縮小 |
| 8   | カンバン モバイル | snap-scroll パターン（横スワイプ）をモバイルで採用 | 1列スタックよりカンバンの視覚メタファーを維持できる。`snap-x snap-mandatory` + `w-[85vw]` |
| 9   | ダークモード | 完全廃止。`.dark` クラスの CSS 変数とダークモード関連コードをすべて削除 | ライトモード専用。不要なコードを除去 |

## アーキテクチャ詳細

### カラーシステム（現行 mauve OKLCH を維持）

現在の `:root` OKLCH パレットをそのまま維持する。変更点は以下のみ：

1. `.dark` クラスのブロックを完全削除
2. `globals.css` の `@custom-variant dark` 行を削除
3. Kanban ステータスカラー変数を `:root` に追加

```css
:root {
  /* 既存の OKLCH 変数はすべて維持 */

  /* 追加: Kanban ステータスカラー */
  --status-not-started: oklch(0.95 0.005 325);
  --status-in-progress: oklch(0.93 0.04 270);
  --status-in-review: oklch(0.94 0.06 85);
  --status-completed: oklch(0.93 0.05 155);
}

/* .dark ブロックは完全削除 */
```

### フォント設定

```tsx
// layout.tsx
import { Inter, Noto_Sans_JP, IBM_Plex_Mono } from "next/font/google"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
})

const notoSansJP = Noto_Sans_JP({
  subsets: ["latin"],
  variable: "--font-jp",
  display: "swap",
})

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
})

// globals.css body
// font-family: var(--font-sans), var(--font-jp), sans-serif;
// ※ Arial 上書きは削除
```

### タイポグラフィスケール

```css
/* Tailwind カスタムユーティリティ（globals.css に追加） */
/* ダッシュボード向けに DESIGN.md の LP 用サイズをスケールダウン */
/* Heading 1: 35px / 600 / 1.2 — ヒーローコピー（ダッシュボードでは未使用） */
/* Heading 2: 24px / 600 / 1.5 — メインタイトル（PLAN Board 等） */
/* Heading 3: 18px / 600 / 1.4 — セクション見出し（カード・サイドバー） */
/* Body: 15px / 400 / 1.7 */
/* Nav: 14px / 500 / -0.28px */
/* Label: 13px / 500 / -0.26px */
/* Mono Label: 11px / 500 / -0.44px (IBM Plex Mono) */
```

### レスポンシブレイアウト構造

```
Desktop (>1024px):  SidebarProvider + Sidebar(collapsible="icon")
┌──────────────┬────────────────────────────────┐
│   Sidebar    │  SidebarInset / Main Content    │
│   (280px)    │   ┌──────┬──────┬──────┬─────┐ │
│   展開表示    │   │未実装│実装中│Review│完了  │ │
│              │   │      │      │      │      │ │
└──────────────┴───┴──────┴──────┴──────┴─────┘

Tablet (769px〜1024px):  Sidebar → アイコンレール(collapsed)
┌───┬───────────────────────────────────────────┐
│ ⊞ │  SidebarInset / Main Content              │
│ ☰ │   ┌──────────────┬──────────────┐         │
│ 📊│   │ 未実装        │ 実装中        │         │
│   │   ├──────────────┼──────────────┤         │
│   │   │ Review       │ 完了          │         │
│   │   └──────────────┴──────────────┘         │
└───┴───────────────────────────────────────────┘
(アイコンレールクリックで展開)

Mobile (≤768px):  Sidebar → Sheet(自動変換)
┌────────────────────┐
│ [☰] PLAN Dashboard │
├────────────────────┤
│  ← snap-scroll →   │
│ ┌────────────────┐ │
│ │ 未実装 (85vw)   │ │
│ └────────────────┘ │
└────────────────────┘
(ハンバーガーで Sheet ドロワー表示)
```

### シャドウ定義

```css
/* Level 0: none（フラット、ボタン） */
/* Level 1: 0 2px 8px rgba(0,0,0,0.08) — カード */
/* Level 2: 0 4px 16px rgba(0,0,0,0.12) — ホバー時 */
```

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
| -------- | -------- | ---- |
| `dashboard/DESIGN.md` | カラーパレットを現行紫系に更新、ダークモード記述削除 | デザイン仕様の原典が実装と整合する |
| `dashboard/app/globals.css` | ダークモード削除、Arial 上書き削除、タイポグラフィユーティリティ追加、ステータスカラー追加 | 全コンポーネントの見た目が変わる |
| `dashboard/app/layout.tsx` | Inter + Noto Sans JP + IBM Plex Mono の 3 フォント読み込み | フォント描画が変わる |
| `dashboard/app/page.tsx` | KanbanBoard 接続、プレースホルダー削除、ローディングスケルトン追加、レスポンシブヘッダー | メイン画面の構成が変わる |
| `dashboard/components/dashboard-layout.tsx` | レスポンシブレイアウト（Sheet サイドバー、ハンバーガーメニュー）、セマンティック HTML | レイアウト構造が変わる |
| `dashboard/components/kanban-board.tsx` | レスポンシブ列数、DESIGN.md カラー、cursor-pointer | カンバンボードの見た目・操作性 |
| `dashboard/components/plan-card.tsx` | タイポグラフィ修正、cursor-pointer(D10)、コントラスト修正(D5/D6)、タッチターゲット | カード表示の品質 |
| `dashboard/components/plan-detail.tsx` | cursor-pointer(D11)、タイポグラフィ修正 | 詳細展開の品質 |
| `dashboard/components/project-filter.tsx` | タッチターゲット拡大(D12)、DESIGN.md スタイル適用 | フィルターの操作性 |

### 新規作成ファイル

| ファイル | 内容 |
| -------- | ---- |
| `dashboard/components/skeleton-dashboard.tsx` | ダッシュボード全体のスケルトン UI コンポーネント |
| `dashboard/components/app-sidebar.tsx` | shadcn/ui Sidebar ラッパー（SidebarHeader, SidebarContent, SidebarFooter） |
| `dashboard/app/error.tsx` | Next.js ErrorBoundary コンポーネント |

### 変更しないファイル

| ファイル | 理由 |
| -------- | ---- |
| `dashboard/lib/plan-parser.ts` | データ層は変更なし |
| `dashboard/lib/project-scanner.ts` | データ層は変更なし |
| `dashboard/lib/types.ts` | 型定義は変更なし |
| `dashboard/lib/config.ts` | 設定読み込みは変更なし |
| `dashboard/app/api/plans/route.ts` | API は変更なし |
| `dashboard/projects.yaml` | プロジェクト設定は変更なし |
| `dashboard/__tests__/*` | データ層テストは変更なし |

## ui-ux-pro-max スキルからの知見

以下は事前に外部スキルから取得済みの知見。参照先ファイルへのアクセスは不要。

### 採用する推奨事項

| カテゴリ | 推奨 | 適用先 |
| -------- | ---- | ------ |
| フォント | Inter/Inter（dashboard, admin panels に最適）| Gate A: A1 |
| ローディング | スケルトン UI 必須（severity: High）、animate-pulse | Gate B: B1 |
| インタラクション | cursor-pointer を全クリッカブル要素に | Gate C: C2, C3 |
| フォント表示 | `font-display: swap` で FOIT 防止 | Gate A: A1 |
| トランジション | 150-300ms のマイクロインタラクション | Gate C 全体 |
| アクセシビリティ | コントラスト 4.5:1 以上、focus states、prefers-reduced-motion | Gate D: D1 |
| レスポンシブ | 375px / 768px / 1024px / 1440px の 4 ブレークポイント検証 | Gate B: B2, Gate C: C1 |
| shadcn ブロック | `npx shadcn@latest add dashboard-01` の構造参照 | Gate B: B2 |

### 採用しない推奨事項

| 推奨 | 不採用理由 |
| ---- | ---------- |
| Exaggerated Minimalism スタイル | ダッシュボードには過激。クリーン・プロフェッショナル路線を採用 |
| Portfolio Grid パターン | ダッシュボードはカンバンボード。プロダクトタイプが異なる |

### Pre-Delivery チェックリスト（全 Gate 完了後に実施）

- [ ] SVG アイコンのみ使用（絵文字なし）
- [ ] 全クリッカブル要素に cursor-pointer
- [ ] ホバーに smooth transition（150-300ms）
- [ ] ライトモード: テキストコントラスト 4.5:1 以上
- [ ] フォーカス状態がキーボードナビで可視
- [ ] prefers-reduced-motion 対応
- [ ] レスポンシブ: 375px, 768px, 1024px, 1440px

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
| -------- | ---- |
| `dashboard/DESIGN.md` | デザイン仕様の原典。カラー・フォント・タイポグラフィ・コンポーネントスタイル・レスポンシブ仕様 |
| `dashboard/components.json` | shadcn/ui 設定（style: base-nova, baseColor: mauve → 変更対象の把握） |
| `dashboard/package.json` | 依存パッケージの確認（shadcn, @base-ui/react, swr, lucide-react） |

## タスクリスト

> **実装詳細は `tasks.json` を参照。** このセクションは進捗管理と Review 記録用。

### 依存関係図

```
Gate A: Design Foundation
├── Todo A1: フォントシステム刷新
├── Todo A2: カラーシステム刷新
└── Todo A3: タイポグラフィトークン定義

Gate B: Layout & Core Fix（Gate A 完了後）
├── Todo B1: KanbanBoard 接続 + スケルトン UI
└── Todo B2: レスポンシブダッシュボードレイアウト

Gate C: Component Redesign（Gate A, B 完了後）
├── Todo C1: カンバンボード レスポンシブ再設計
├── Todo C2: PlanCard・PlanDetail 再設計
└── Todo C3: ProjectFilter・統計サマリー 再設計

Gate D: Semantic & Polish（Gate C 完了後）
├── Todo D1: セマンティック HTML・アクセシビリティ
└── Todo D2: iOS Safari viewport・ErrorBoundary
```

### Gate A: Design Foundation

- [x] **Todo A1**: フォントシステム刷新（Inter + Noto Sans JP + IBM Plex Mono）
  > **Review A1**: ✅ PASSED

- [x] **Todo A2**: カラーシステム整理（ダークモード廃止 + ステータスカラー追加）
  > **Review A2**: ✅ PASSED

- [x] **Todo A3**: タイポグラフィトークン定義（サイズ・ウェイト・行間・字間）
  > **Review A3**: ✅ PASSED

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: Layout & Core Fix

- [x] **Todo B1**: KanbanBoard 接続修正 + スケルトンローディング UI
  > **Review B1**: PASSED — kanbanComponentName 削除、プレースホルダーを `<KanbanBoard plans={filteredPlans} />` に置換、SkeletonDashboard 新規作成、isLoading をスケルトンに置換。ビルド成功。

- [x] **Todo B2**: shadcn/ui Sidebar によるレスポンシブレイアウト
  > **Review B2**: PASSED — shadcn sidebar + 依存7ファイル追加。app-sidebar.tsx 新規作成（collapsible="icon"）。dashboard-layout.tsx を SidebarProvider ベースに全面書き換え。page.tsx の sidebar prop を filterContent/statsContent に分解。ビルド成功。

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate C: Component Redesign

- [x] **Todo C1**: カンバンボード レスポンシブ再設計
  > **Review C1**: PASSED — `116e8b7`

- [x] **Todo C2**: PlanCard・PlanDetail 再設計
  > **Review C2**: PASSED — `116e8b7`

- [x] **Todo C3**: ProjectFilter・統計サマリー 再設計
  > **Review C3**: PASSED — `116e8b7`

**Gate C 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate D: Semantic & Polish

- [x] **Todo D1**: セマンティック HTML・アクセシビリティ対応
  > **Review D1**: PASSED — スキップリンク追加、nav+ul/li構造化、見出し階層修正、aria-label追加、prefers-reduced-motion対応。`80794b0`

- [x] **Todo D2**: iOS Safari viewport 修正・ErrorBoundary 追加
  > **Review D2**: PASSED — error.tsx新規作成、min-h-screen→min-h-svh置換、suppressHydrationWarning追加。`80794b0`

**Gate D 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

## 残存リスク

| リスク | 影響 | 緩和策 |
| ------ | ---- | ------ |
| shadcn/ui base-nova プリセットとの競合 | カラー変数上書きで一部コンポーネントのスタイルが崩れる可能性 | 各 shadcn/ui コンポーネント（Badge, Card 等）を変更後に目視確認 |
| Inter フォントの日本語フォールバック | Inter に和文グリフがないため、混在テキストで微妙なサイズ差が出る可能性 | Noto Sans JP の weight を Inter に合わせて調整 |
| Sheet コンポーネント未導入 | モバイルドロワーに shadcn/ui Sheet が必要。未インストールの可能性 | Gate B 開始前に `npx shadcn@latest add sheet` で追加 |
| ダークモード削除後の副作用 | `.dark` 関連コードを削除する際に、shadcn/ui コンポーネント内部でダークモード参照がある可能性 | shadcn/ui の ui/ ディレクトリ内の全ファイルを Grep で確認し、dark: prefix が残っていれば削除 |
