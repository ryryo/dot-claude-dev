---
name: design-e2e-qa
description: |
  実装済みサイトのデザイン品質を体系的にチェックする。配置・余白・比率・レスポンシブなどデザイン的な問題を検出し、修正は行わず問題のリストアップに集中する。
  Trigger: デザインQA, デザインチェック, レイアウト確認, デザイン検証, 表示崩れ確認, /design-e2e-qa
---

# Design QA — デザイン品質チェック

## 基本原則

### 1. 修正せず、記録する

このスキルの目的は問題の発見と一覧化。修正コードは一切書かない。ユーザーが修正フェーズに移行する判断材料を提供する。

### 2. 網羅性 > 速度

速く終わらせるより、見落としゼロを目指す。全ページ・全ビューポート・全インタラクション状態を検査する。「たぶん大丈夫」は検査していないのと同じ。

### 3. ソースコードが第一の情報源

**スクリーンショットより先にソースコードを読む。** JPEG圧縮で色が変わる・ピクセル差は測れない・ホバー状態は静止SSに写らない。問題の発見と根本原因の特定は `Read`/`Grep`/`Glob` で行い、SSは「実際に崩れているか」の目視確認に限定する。

### 4. 見た目と振る舞いの両方を検査する

静的な見た目だけでなく、ホバー・クリック・フォーカス・画面サイズ変更時の振る舞いも検査対象とする。ただし振る舞いの問題はソースの `:hover`/`transition`/`cursor` クラスから先に検出し、SSはその裏付けに使う。

### 5. ソースコードで必ず裏を取る

問題を発見したら該当コンポーネントのソースを `Read` / `Grep` で読み、原因箇所（ファイル名・行番号・該当コード）を特定する。原因コードの特定なしに問題を報告しない。

### 6. 仕様書を基準にする

プロジェクトにデザイン仕様書（DESIGN.md 等）がある場合、仕様との乖離を基準に判断する。仕様書がない場合はデザインの一般原則とサイト内の一貫性を基準にする。

### 7. Phase 2-3 でページ単位に完結させる

Phase 2（SS撮影）と Phase 3（インタラクション検証）では1つのページの全ビューポート・全インタラクションの収集を終えてから次のページに進む。複数ページを並行で収集すると抜け漏れが増える。

---

## .tmp/ ディレクトリ構造

Phase 1〜3 で収集した素材と Phase 4 の出力を格納する:

```
.tmp/design-e2e-qa/
├── screenshots/
│   ├── {page}-{viewport}-full.jpg        # フルページキャプチャ
│   └── {page}-{viewport}-{section}.jpg   # セクション単位キャプチャ
├── source-info/
│   ├── routes.txt        # ルート一覧（src/pages/ の Glob 結果）
│   ├── css-tokens.txt    # CSS変数一覧（global.css から抽出）
│   ├── font-config.txt   # フォント設定（@font-face 定義）
│   ├── preflight.txt     # ダークモード/OGP 該当判定結果
│   └── interaction-observations.txt  # インタラクション操作の観察記録
└── results/
    ├── visual-layout.json    # エージェント出力
    ├── content-media.json
    ├── interaction-nav.json
    ├── seo.json
    ├── accessibility.json
    ├── performance.json
    ├── meta-theme.json       # 条件付き
    └── final-report.md       # 統合レポート
```

プロジェクト側（ステートフル UI 向け）:

```
{project}/
└── .claude/e2e/
    └── {scenario}.mjs   # before-script（export default async (page) => {}）
```

### SS 命名規則

- **page**: ページ識別子（例: `top`, `article-detail`, `archive`, `about`, `404`）
- **viewport**: `desktop`, `tablet`, `mobile`
- **section**: ページ内のセクション名（`hero`, `posts`, `sidebar` 等）

例: `top-desktop-full.jpg`, `top-desktop-hero.jpg`, `top-mobile-full.jpg`

---

## Pre-Flight

Phase 1 に入る前に完了させる（preview ツール不要）:

- [ ] 開発サーバー起動（`preview_start`）— 起動成功を確認
- [ ] 仕様書の探索 — `DESIGN.md` 等のデザイン仕様書を `Glob` / `Grep` で探す。見つかればパスを記録し `Read`、なければ「仕様書なし — サイト内一貫性と一般原則で判断」と記録
- [ ] ダークモード判定 — `dark:`, `prefers-color-scheme` を `Grep` → `preflight.txt` に記録
- [ ] OGP判定 — `og:image`, `og:title` を `Grep` → `preflight.txt` に記録

---

## 実行手順

### フェーズ依存関係図

```
Pre-Flight
    ↓
Phase 1: ソース収集（Read/Grep/Glob のみ）
    ↓
Phase 2: SS撮影（Haiku エージェント — take-screenshots.sh 実行）
    ↓
Phase 3: インタラクション検証（メイン — preview_click + observations.txt 記録）
    ↓（Phase 1〜3 すべて完了してから）
Phase 4: 並列レビュー（Sonnet × 3-4）
├── visual-layout (A/B/E)
├── content-media (C/D/F)
├── interaction-nav (G/H)
└── [条件] meta-theme (I/J)
    ↓
Phase 5: 統合（メイン）
```

### Phase 1: ソース収集（必達 — スキップ不可）

**preview ツール不要。** `Read`/`Grep`/`Glob` のみ。**全チェックボックスが完了するまで Phase 2 に進まない。**

#### 1. プロジェクト構造の把握

- [ ] プロジェクトルートで `Glob` し、フレームワーク（Astro/Next/Nuxt 等）とディレクトリ構成を特定
- [ ] ルーティングファイルを `Glob` で探索 → `.tmp/design-e2e-qa/source-info/routes.txt` に保存
- [ ] グローバル CSS / テーマ定義を `Grep`（`--color`, `--font`, `@theme`, `:root`）→ `css-tokens.txt` に保存
- [ ] フォント定義を `Grep`（`@font-face`, `font-family`, Google Fonts URL）→ `font-config.txt` に保存
- [ ] `preflight.txt` 作成 — 以下を判定して記録:
  ```
  darkmode: true|false
  ogp: true|false
  ```

#### 2. レイアウト・構造系コンポーネント（観点 A/B/E）

- [ ] レイアウトテンプレート（`layout`, `template`, `app` 等を含むファイル）を `Glob` → `Read`
- [ ] 主要ページ（トップ・記事詳細・一覧・About・404 相当）を `Read`
- [ ] ヘッダー・フッター・サイドバー・セクション系コンポーネントを `Glob` → `Read`
- [ ] CSS変数・スペーシングの使用箇所を `Grep`（`--space`, `gap-`, `py-`, `px-` 等）

#### 3. メディア・コンテンツ系コンポーネント（観点 C/D/F）

- [ ] コンテンツスキーマ / 型定義を `Grep`（`content`, `schema`, `collection` 等）→ `Read`
- [ ] 記事カード・記事本文・関連記事系コンポーネントを `Read`
- [ ] OGP画像生成ロジックがあれば `Read`
- [ ] 画像フォールバック処理を `Grep`（`fallback`, `default`, `placeholder` 等）

#### 4. インタラクション・ナビ系（観点 G/H）

- [ ] `hover:`, `focus:`, `transition`, `cursor`, `group-hover:` を `Grep` で全体検索
- [ ] 全コンポーネントの `href` / `to=` / `Link` を `Grep` → routes.txt と突合
- [ ] モーダル・ドロワー・タブ等のインタラクティブコンポーネントを `Read`

### Phase 2: SS撮影（必達）

**Phase 1 が完了してから開始する。**

Phase 1 の routes.txt から代表ページを選定し、`agents/screenshot.md`（Haiku）で SS を撮影する。

**代表ページの選定基準:**

- トップページ（必須）
- 記事・投稿の詳細ページ（代表1件）
- 一覧・カテゴリページ（代表1件）
- 固定ページ（About / Contact 等、存在すれば）
- エラーページ（404 等、存在すれば — デスクトップのみ可）

**ステートフル UI 向けフロー分岐:**

認証が必要なページやインタラクション後の状態を撮影したい場合は `--before-script` を使用する:

- **判定基準**: ログインが必要など、VP に依存しない共通セットアップが URL だけでは再現できない場合に使用。VP ごとに異なる状態（モバイルドロワー展開等）の撮影には使えない（before-script は全 VP 撮影前に1回だけ実行される）
- **before-script の配置場所**: プロジェクト側 `.claude/e2e/` に `.mjs` ファイルとして配置（`export default async (page) => {}`）
- **実行順序の変更**: ステートフル UI の場合は Phase 3（インタラクション設計）→ Phase 2（SS 撮影）の順に変更可（before-script の内容を先に設計する必要があるため）

- [ ] 代表ページ一覧を routes.txt から選定・記録（`page:path` 形式）
- [ ] ステートフル UI の有無を判定し、必要なら before-script を設計
- [ ] `agents/screenshot.md` エージェントを起動し SS 撮影を実行

---

### Phase 3: インタラクション検証（メイン — 必達）

**Phase 1 が完了してから開始する。** Phase 2 と並行して実施可能。preview ツールはこの Phase のみ使用。

Phase 1 の Grep 結果から検出されたインタラクション要素について、`preview_click` で操作し動作を検証する。

**対象の例:** ハンバーガーメニュー開閉、タブ切替、ホバー状態、モーダル開閉、ドロップダウン等

`preview_screenshot` で操作前後の状態を目視確認し、検証結果を `.tmp/design-e2e-qa/source-info/interaction-observations.txt` に `Write` でテキスト記録する。

記録フォーマット例:

```text
## ハンバーガーメニュー開閉
- 操作: モバイルVPでハンバーガーアイコンをクリック
- 結果: メニューが展開された / アニメーションあり / 閉じるボタンあり
- 問題: なし / {問題の記述}
```

- [ ] Phase 1 で検出したインタラクション要素の一覧を記録
- [ ] 各インタラクションを操作し、目視確認 + 観察結果をテキスト記録

**Phase 2-3 完了条件:** `.tmp/design-e2e-qa/screenshots/` と `.tmp/design-e2e-qa/source-info/` に全素材が揃っており、`.tmp/design-e2e-qa/source-info/interaction-observations.txt` が存在すること。撮影した SS ファイル一覧を `ls` で確認し、代表ページ一覧・インタラクション一覧と照合する。

---

### Phase 4: 並列レビュー

Phase 1〜3 すべて完了後、以下のエージェントを**1つの応答で並列起動**する。

| エージェント                | 担当観点 | 起動条件                                           |
| --------------------------- | -------- | -------------------------------------------------- |
| `agents/visual-layout.md`   | A, B, E  | 常時                                               |
| `agents/content-media.md`   | C, D, F  | 常時                                               |
| `agents/interaction-nav.md` | G, H     | 常時                                               |
| `agents/seo.md`             | K        | 常時                                               |
| `agents/accessibility.md`   | L        | 常時                                               |
| `agents/performance.md`     | M        | 常時                                               |
| `agents/meta-theme.md`      | I, J     | `preflight.txt` で darkmode/ogp が true の場合のみ |

- [ ] 5〜7エージェントを並列起動
- [ ] 全エージェント完了を確認

---

### Phase 5: 統合

全エージェントの完了後、メインエージェント（Opus）が統合を行う。

1. `.tmp/design-e2e-qa/results/` から各 JSON を `Read`
2. 全 issues を1つのリストに統合
3. **重複排除** — 以下のルールで判定:
   - 同じファイル + 同じ行番号 + 同じ aspect → 統合（1件に）
   - 同じファイル + 異なる行番号 → 別問題として残す
   - 異なるファイル → 別問題として残す
   - 同じ aspect で複数エージェントが指摘 → 説明を比較し、実質同一なら統合
4. 深刻度順にソート（critical → medium → minor）
5. 通し番号 D1, D2, ... を付与
6. 最終レポートを作成し `.tmp/design-e2e-qa/results/final-report.md` に保存

- [ ] 全 JSON の読み込み
- [ ] 重複排除・統合
- [ ] 最終レポート作成

---

## 最終出力

全問題を深刻度順に一覧化し、以下の構成で報告する:

```
## デザインQAレポート

### カバレッジサマリー
| 項目 | 状況 |
|------|------|
| 検査ページ数 | {N} / {全ページ数} |
| 検査ビューポート | デスクトップ / タブレット / モバイル |
| 検査観点 | A〜J（{未実施の観点があれば記載}） |
| インタラクション検証 | 実施済み / 未実施 |
| 仕様書参照 | DESIGN.md / なし |
| レビューエージェント | visual-layout, content-media, interaction-nav{, meta-theme} |

### 定量サマリー
| 深刻度 | 件数 |
|--------|------|
| 重大   | {N}  |
| 中程度 | {N}  |
| 軽微   | {N}  |
| **合計** | **{N}** |

### 重大
- D1. ...
- D2. ...

### 中程度
- D3. ...
- D4. ...

### 軽微
- D5. ...

### 推奨修正優先順
1. {重大から順に、修正の推奨順序}
```

### 次のアクション

最終レポートをユーザーに提示した後、**AskUserQuestion ツール**で次のアクションを確認する:

- **`/dev:spec` で修正仕様書を作成** — レポートの問題一覧を元に、修正の実装仕様書を作成する。問題数が多い場合や影響範囲が広い場合に推奨
- **`/dev:decomposition` でタスク分解して修正** — レポートの問題一覧をタスクに分解し、順次修正する。問題が少数で方針が明確な場合に推奨
- **レポートのみで終了** — 修正は別の機会に行う。レポートを `.tmp/design-e2e-qa/results/final-report.md` に保存して完了

---

## プレビューツール使用上の注意

### Phase 3 限定の方針

**preview ツールは Phase 3 のメインエージェントのみが使用する。** Phase 4 の Sonnet エージェントは preview ツールを使わず、Phase 1〜3 で保存済みのスクリーンショットとソース情報を `Read` するだけで完結する。これは preview サーバーがシングルトンリソースであり、複数エージェントの同時アクセスで競合するためである。

### ローカルコード優先の方針

このスキルは自プロジェクトのソースコードがローカルにある前提で動作する。CSS値・デザイントークン・フォント設定・リンク先などは `Read` / `Grep` / `Glob` でソースコードから直接確認する。preview ツールは以下の用途に限定する:

- 実際のレンダリング結果の確認（レイアウト崩れ、クロッピング）
- レスポンシブでの表示確認（`preview_resize` + `preview_screenshot`）
- アニメーション・トランジションの動作確認
- インタラクション操作（`preview_click`）
- スクリーンショットによる最終的な目視確認

### ツール固有の注意点

- `preview_resize` でビューポートを設定しても、JS 上の `window.innerWidth` がネイティブブラウザサイズのままになる場合がある
- スクリーンショットが切れる場合は `preview_resize` の設定を見直す（不必要に大きくしない）
- `preview_screenshot` は JPEG 圧縮されるため、細かい色味の判定にはソースのカラーコードを参照する
- CSS値の正確な検証にはソースコードの `Read` を優先する（`preview_inspect` は補助的に使用）
