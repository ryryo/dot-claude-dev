# Dashboard 計画書パスコピー機能

## Gate 0: 準備 **必須工程(スキップ不可)**

この仕様書の実行には `/dev:spec-run` スキルを使用すること。

**Gate 0 通過条件**: `/dev:spec-run` の実行プロトコルに従い、実行モード（従来 / Codex）を選択済みであること。

---

## 概要

dashboard に計画書のディレクトリパスをクリップボードへコピーする機能を 2 種類追加する。個別カードの Copy アイコン（単一パス）と、カンバン「レビュー待ち」カラムヘッダーのまとめコピー（表示中全件のパスを改行区切り）の 2 系統。

## 背景

日常的な運用で計画書を `/dev:spec-run` や会話で参照する際に、該当の `docs/PLAN/{YYMMDD}_{slug}` パスを手入力する手間が発生している。特に複数のレビュー待ち計画をまとめて実装セッションに渡す用途では、手動でパスを一覧化する作業が煩わしい。dashboard 上でワンクリック取得できれば、人間オペレーターが計画書選択から次アクション起動までを素早く繋げられる。

## 設計決定事項

| #   | トピック | 決定 | 根拠 |
| --- | -------- | ---- | ---- |
| 1   | コピー対象の形式 | ディレクトリパスに統一（例: `docs/PLAN/260412_foo`）。v2 (`/spec.md` 付き) もレガシー単独 `.md` も末尾を除去してディレクトリパスへ正規化 | ユーザー要望で一貫性を優先。`/dev:spec-run` が受け付ける参照形式と一致 |
| 2   | 個別コピーボタンの配置 | `plan-card.tsx` の既存アイコングループ（L42-72）の先頭に `Copy` アイコンとして追加 | 既存 UI パターンに統合。`ListChecks` / `FileText` と同列でワンカラムに集約 |
| 3   | まとめコピーボタンの配置 | `kanban-board.tsx` カラムヘッダー（L217-222）の「レビュー待ち」カラムのみ、Badge の隣に `Copy` アイコンを表示 | ユーザー回答「カラムヘッダー配置・表示中全件」に従う |
| 4   | まとめコピー対象の範囲 | 現在 `KanbanGrid` がレンダリングしている `columnPlans` 配列（フィルタ適用後の in-review 全件）。`groupByProject` モードでも全プロジェクトを横断せず、そのカラム内で描画中のものに限る | `KanbanGrid` はプロジェクトグルーピング時に各プロジェクト単位で呼ばれるため、「表示中全件」の意味がスコープごとに自然に決まる |
| 5   | パス変換ロジックの分離 | `dashboard/lib/plan-path.ts` に `getPlanDirectoryPath(filePath: string): string` を新設し、`plan-card.tsx` / `kanban-board.tsx` から共通利用 | 純粋関数で TDD 可能。UI コンポーネントと切り離すことでテスト容易性を確保 |
| 6   | コピー成功時のフィードバック | アイコンを `Copy` → `Check` に 1.5 秒切り替え。トースト通知は追加しない | 既存 UI に Toast/Sonner 未導入。軽量・即時・依存追加ゼロの選択肢 |
| 7   | エラー時のフィードバック | `navigator.clipboard.writeText` が例外を投げた場合は `console.error` でログのみ。アイコンは切り替えない | HTTPS 非配信・古いブラウザは対象外。dashboard は Vercel (HTTPS) 前提。過剰防御を避ける |
| 8   | イベント伝播 | コピーボタンは `onClick` で `e.stopPropagation()` を呼び、`Collapsible` / カラム全体への伝播を阻止 | 既存の `ListChecks` / `FileText` ボタンと同じパターン |

## アーキテクチャ詳細

### パス変換ロジック

```typescript
// dashboard/lib/plan-path.ts
export function getPlanDirectoryPath(filePath: string): string {
  // 末尾の /spec.md または /tasks.json を除去（v2 ディレクトリ形式）
  // 末尾の .md を除去（レガシー単独 .md 形式）
  // どちらにも該当しなければそのまま返す（想定外入力の safe fallback）
}
```

変換例:

| 入力 | 出力 |
| ---- | ---- |
| `docs/PLAN/260412_spec-dashboard-format-v2/spec.md` | `docs/PLAN/260412_spec-dashboard-format-v2` |
| `docs/PLAN/260412_spec-dashboard-format-v2/tasks.json` | `docs/PLAN/260412_spec-dashboard-format-v2` |
| `docs/PLAN/260411_dashboard-auth-hardening.md` | `docs/PLAN/260411_dashboard-auth-hardening` |
| `docs/PLAN/260410_foo` | `docs/PLAN/260410_foo` |

### データフロー

```
[ユーザー操作]                       [処理]
  │
  ├─ PlanCard の Copy アイコンクリック
  │     → e.stopPropagation()
  │     → navigator.clipboard.writeText(
  │         getPlanDirectoryPath(plan.filePath)
  │       )
  │     → setCopied(true); setTimeout(() => setCopied(false), 1500)
  │     → アイコン Copy → Check → Copy
  │
  └─ Kanban「レビュー待ち」カラムヘッダーの Copy アイコンクリック
        → e.stopPropagation()
        → navigator.clipboard.writeText(
            columnPlans
              .map(p => getPlanDirectoryPath(p.filePath))
              .join('\n')
          )
        → 同じ Copy → Check → Copy アニメーション
        → columnPlans.length === 0 の場合は disabled（ボタン押下不可）
```

### UI 仕様

- アイコン: `lucide-react` の `Copy` / `Check`（サイズ `size-4`、`shrink-0`）
- 色: `text-muted-foreground hover:text-foreground`（既存アイコンボタンと同一クラス）
- `aria-label`: 個別は「{title} のパスをコピー」、まとめは「レビュー待ち{N}件のパスをコピー」
- `disabled` 状態: まとめコピーで `columnPlans.length === 0` のとき。`aria-disabled` + `cursor-not-allowed` + 視覚的 opacity

## 変更対象ファイルと影響範囲

### 変更するファイル

| ファイル | 変更内容 | 影響 |
| -------- | -------- | ---- |
| `dashboard/components/plan-card.tsx` | 既存アイコン群に `Copy`/`Check` ボタンを追加 | PlanCard を使う全画面（カンバン / テーブル想定） |
| `dashboard/components/kanban-board.tsx` | 「レビュー待ち」カラムの CardHeader に `Copy`/`Check` ボタンを追加 | KanbanBoard 全体（ダッシュボード main ビュー） |

### 新規作成ファイル

| ファイル | 内容 |
| -------- | ---- |
| `dashboard/lib/plan-path.ts` | `getPlanDirectoryPath(filePath: string): string` を export |
| `dashboard/__tests__/plan-path.test.ts` | `getPlanDirectoryPath` の Vitest ユニットテスト（v2 / レガシー / ディレクトリ既存 / タスクJSON）|

### 変更しないファイル

| ファイル | 理由 |
| -------- | ---- |
| `dashboard/lib/types.ts` | 既存の `PlanFile` 型で十分 |
| `dashboard/lib/plan-parser.ts` | パス正規化は分離ファイルに持たせるため影響なし |
| `dashboard/components/plan-table.tsx` | 今回のスコープ外（必要なら将来同じ関数を適用可能） |

## 参照すべきファイル

実装着手前に必ず読むこと。

### コードベース内

| ファイル | 目的 |
| -------- | ---- |
| `dashboard/components/plan-card.tsx` | 既存アイコンボタンのスタイル・`stopPropagation` パターン |
| `dashboard/components/kanban-board.tsx` | `COLUMNS` 定義、`KanbanGrid` のカラムヘッダー配置、`columnPlans` の算出 |
| `dashboard/lib/types.ts` | `PlanFile.filePath`, `PlanStatus = 'in-review'` の定義 |
| `dashboard/lib/plan-parser.ts` | `path.basename` / `path.dirname` 使用例（ユーティリティ関数のスタイル参考）|
| `dashboard/__tests__/plan-parser.test.ts` | Vitest テストの書式・describe/it 構造の参考 |
| `dashboard/vitest.config.ts` | テスト設定（Node 環境、`__tests__/**/*.test.{ts,tsx}`）|

## タスクリスト

<!-- generated:begin -->
<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->
<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->

### 依存関係図

```
Gate A: コアロジック
Gate B: UI コピー機能（Gate A 完了後）
```

### Gate A: コアロジック

> パス変換の純粋関数を TDD で先に確立する。

- [x] **A1**: [TDD] getPlanDirectoryPath ユーティリティを実装する
  > **Review A1**: ✅ PASSED — 4ケース全PASS。純粋関数として正確に実装。ストーリー・API・リスク・セキュリティ全観点PASS

**Gate A 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

### Gate B: UI コピー機能

> getPlanDirectoryPath を利用して 2 種類のコピーボタンを UI に組み込む。

- [x] **B1**: [SIMPLE] PlanCard に個別コピーボタンを追加する
  > **Review B1**: ✅ PASSED — 全6要件PASS。既存ボタンと同パターン。stopPropagation/aria-label/isNarrow対応すべて正確
- [x] **B2**: KanbanBoard のレビュー待ちカラムにまとめコピーボタンを追加する
  > **Review B2**: ✅ PASSED — 全要件PASS。ReviewColumnCopyButton・disabled状態・in-reviewのみ表示・groupByProject対応すべて正確

**Gate B 通過条件**: 全 Review 結果記入欄が埋まり、総合判定が PASS であること

<!-- generated:end -->

## レビューステータス

- [x] **レビュー完了** — 人間による最終確認

## 残存リスク

| リスク | 影響 | 緩和策 |
| ------ | ---- | ------ |
| `navigator.clipboard` が HTTPS 非配信環境で失敗 | コピー機能が使えない | dashboard は Vercel 配信 (HTTPS) 前提。ローカル開発は `localhost` で許可される。それ以外の環境はサポート対象外と明記 |
| `filePath` フォーマットが想定外（例: リネーム・ディレクトリ構造変更） | パスが正しく変換されない | `getPlanDirectoryPath` は「末尾 `/spec.md`・`/tasks.json`・`.md` を取り除く」だけの safe fallback にとどめる。元のパスが想定外ならそのまま返す |
| まとめコピー時に改行コードが OS 間で揺れる | LF / CRLF のミスマッチ | `'\n'` 固定。クリップボード受け側（エディタ）で自動変換されるため実用上問題なし |
