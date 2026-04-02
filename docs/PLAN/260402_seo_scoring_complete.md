# SEO診断スキル 完全チェックリスト & 実装設計

> **目的**: ローカル動作のSEO診断スキルで使用する全チェック項目と実装方式の定義
> **作成日**: 2026-04-02
> **前提**: ローカル実行。汎用スキルが全体をオーケストレーションし、プロジェクト差分は各リポジトリの `<target-project>/scripts/seo/` アダプタで吸収する。
> **参照ツール**: Semrush(140+), Ahrefs(170+), Lighthouse(8), SEO Site Checkup(70+), Seobility(200+)

---

## パス表記ルール

この資料では、パスの基準位置を明示的に次の2つに分ける。

| 表記 | 意味 |
|------|------|
| `<skill-root>/...` | SEO監査スキル自身のディレクトリ配下 |
| `<target-project>/...` | 監査対象のアプリケーション/サイトのリポジトリ配下 |

例:
- `<skill-root>/scripts/score.sh` はスキル側の共通スクリプト
- `<target-project>/scripts/seo/collect.sh` は対象プロジェクト側のSEOアダプタ
- `<target-project>/docs/seo/pages/<page-id>.json` は対象プロジェクト側に生成される監査成果物

以下、単に `scripts/` や `docs/seo/` と書くと曖昧になるため、原則としてこのプレフィックス付きで記述する。

---

## 実行モード

スキル起動時に AskUserQuestion で本番URLの有無を確認し、実行モードを決定する。

```
スキル起動
  └─ AskUserQuestion: 「本番URLはありますか？（例: https://example.com）」
       ├─ URL入力あり → Full モード（コード解析 + ライブチェック）
       └─ なし/スキップ → Code-only モード（コード解析のみ）
```

### チェック項目の3層分類

| 層 | ラベル | データソース | 実行条件 |
|----|--------|-------------|----------|
| **Layer 1: code** | コード解析 | `<target-project>/scripts/seo/` が生成した監査アーティファクト、または静的ファイルを `Read`, `Glob`, `Grep` で解析 | 常に実行 |
| **Layer 2: live** | ライブチェック | `curl` でHTTPヘッダー・SSL・リダイレクト等を取得 | 本番URL提供時のみ |
| **Layer 3: api** | 外部API | PageSpeed Insights API でCWV等を取得 | 本番URL提供時のみ |

**Code-only モード時**: Layer 2/3 の項目はスキップし、Layer 1 の結果のみでスコア算出。スキップ項目は「未検査」と表示し、該当カテゴリの重みを Layer 1 項目で按分。

## 実装方式の定義

| 方式 | 配置 | 用途 | 例 |
|------|------|------|-----|
| **adapter** | `<target-project>/scripts/seo/` | プロジェクト固有の構成差分を吸収 | ルート検出、ルート一覧、head抽出、ビルド/起動方法 |
| **code** | Read/Grep/Glob | 正規化済みアーティファクトまたは単純な静的ファイルを判定 | HTMLタグ有無、構造化データ、リンク構成 |
| **script** | `<skill-root>/scripts/` または `<target-project>/scripts/seo/` | bash/jq/grep で確定的ルール判定 | robots.txt解析、文字数カウント、パターンマッチ |
| **agent** | `<skill-root>/agents/` | LLMの判断が必要 | コンテンツ品質、可読性、E-E-A-T評価 |
| **hybrid** | adapter/code/script + agent | 抽出→判定 | アンカーテキスト品質、アンサーファースト |
| **live** | `curl` | HTTPレスポンスが必要 | ヘッダー、SSL、リダイレクト、TTFB |
| **api** | PSI API | 外部API呼び出し | CWV（LCP, INP, CLS, FCP） |

### データ取得フロー

```
■ 常に実行（Layer 1: code）
  まず <target-project>/scripts/seo/ のアダプタで監査対象を正規化
  ├─ discover      → 監査対象ページ/ルート/設定ファイル候補の列挙
  ├─ collect       → head/body/JSON-LD/リンク一覧などの監査アーティファクト生成
  ├─ files         → robots.txt, sitemap.xml, llms.txt, favicon などの実体パス解決
  └─ checks        → 汎用ルールがアーティファクトに対して判定

■ 本番URL提供時のみ（Layer 2: live）
  <skill-root>/scripts/fetch-live.sh <URL>
  ├─ curl -sIL → headers.txt（レスポンスヘッダー + リダイレクトチェーン）
  ├─ curl -vI 2>&1 → ssl-info.txt（SSL証明書情報）
  ├─ curl -w "%{time_starttransfer}" → ttfb.txt
  ├─ curl --http2 -sI → http2-check.txt
  └─ curl -s http://<domain> -o /dev/null -w "%{redirect_url}" → redirect-check.txt
  （並列実行、5秒タイムアウト）

■ 本番URL提供時のみ（Layer 3: api）
  <skill-root>/scripts/call-psi-api.sh <URL>
  └─ PageSpeed Insights API → CWV, Lighthouseスコア
```

### 汎用スキルとしての責務分離

フレームワーク差分とディレクトリ差分が大きいため、汎用スキルは「直接すべてを読む」のではなく、以下の二層に分ける。

| 層 | 責務 | 置き場所 |
|----|------|---------|
| **汎用スキル本体** | チェックリスト、スコアリング、レポート、アダプタ生成/更新判断 | `<skill-root>/` |
| **プロジェクトSEOアダプタ** | ページ発見、ルート解決、head/body抽出、ビルド/起動方法の吸収 | `<target-project>/scripts/seo/` |

この設計では `C01 title タグ存在` のような項目も、ソースコード中の `<title>` を直接 `Grep` するのではなく、アダプタが収集した「監査対象ページの正規化済み head 情報」に対して判定する。これにより Next.js/Nuxt/Astro/Vite/静的HTML の差異を吸収できる。

### プロジェクトSEOアダプタの基本方針

各プロジェクトに `<target-project>/scripts/seo/` を持たせ、初回実行時に未作成ならスキルが生成する。既存アダプタがあっても、プロジェクト構成の変化で古くなっている場合はスキルが更新提案または更新実施を行う。

最低限必要な責務は以下。

| ファイル | 役割 | 出力 |
|---------|------|------|
| `<target-project>/scripts/seo/discover.*` | 監査対象のページ・ルート・設定ファイル候補を検出 | `<target-project>/docs/seo/pages.json` |
| `<target-project>/scripts/seo/collect.*` | 各ページの head/body/JSON-LD/リンク一覧を正規化して収集 | `<target-project>/docs/seo/pages/<page-id>.json` |
| `<target-project>/scripts/seo/files.*` | robots.txt, sitemap.xml, llms.txt, favicon などの実パスを解決 | `<target-project>/docs/seo/files.json` |
| `<target-project>/scripts/seo/manifest.json` | フレームワーク、主要ディレクトリ、実行方法、除外対象を宣言 | アダプタ設定 |

`discover` はフレームワーク別のルート規約を解決する。例:
- Next.js App Router: `app/**/page.*`, `generateMetadata`, `layout.*`
- Next.js Pages Router: `pages/**/*.tsx`, `_app.*`, `_document.*`
- Astro: `src/pages/**/*.astro`
- Nuxt: `pages/**/*.vue`, `app.vue`, `nuxt.config.*`
- 静的HTML: `public/**/*.html`, `dist/**/*.html`, ルート直下HTML

`collect` は初版では静的解析を優先し、`title`, `canonical`, `robots`, `hreflang` など静的解析だけで確定しないページだけレンダリング補完を行う。これにより導入容易性を保ちつつ、動的メタデータも扱いやすくする。

manifest が無い場合は、アダプタが `package.json`, framework config, ディレクトリ構成, route 規約から `framework`, `roots`, `commands`, `output` を自動推定する。manifest がある場合は、指定されたフィールドだけを override として扱い、未指定フィールドは引き続き自動推定結果を使う。

### アダプタのライフサイクル

```
1. 初回実行
   - `<target-project>/scripts/seo/` の有無確認
   - 無ければプロジェクト構成を見て雛形を生成

2. 実行前点検
   - manifest と現在の構成差分を確認
   - 主要ディレクトリやフレームワークが変わっていたら refresh を実行

3. 監査実行
   - adapter で監査アーティファクト生成
   - 汎用ルールがそのアーティファクトを評価

4. 保守
   - チェック失敗の原因が「構成変化」なら、ルール修正より先に adapter 更新を優先
```

### 判定対象を「ソースコード」から「監査アーティファクト」へ寄せる

汎用スキル側の各チェックは、可能な限り次の入力に対して判定する。

| 判定対象 | 例 | 備考 |
|---------|----|------|
| `page.head` | title, meta description, canonical, OG, Twitter Card | `<target-project>/docs/seo/pages/<page-id>.json` 内。C01-C04, C16-C19 を安定化 |
| `page.body` | H1, 見出し階層, FAQ, 本文量 | `<target-project>/docs/seo/pages/<page-id>.json` 内。C05-C08, C24-C30 |
| `page.links` | 内部リンク数、空アンカー、unsafe target | `<target-project>/docs/seo/pages/<page-id>.json` 内。L01-L08 |
| `page.structuredData` | JSON-LD構文、@type、必須プロパティ | `<target-project>/docs/seo/pages/<page-id>.json` 内。S01-S08 |
| `project.files` | robots.txt, sitemap.xml, llms.txt, favicon | `<target-project>/docs/seo/files.json` 内。T01-T07, G01-G03 |

この整理を入れておくと、「どのチェックが raw Grep で済み、どのチェックは adapter 前提か」が明確になる。

### 監査成果物の標準配置

監査成果物の標準配置は `<target-project>/docs/seo/` とし、JSON と人間向け要約の両方を Git 管理する。

| パス | 役割 | 備考 |
|------|------|------|
| `<target-project>/docs/seo/pages.json` | 監査対象ページの一覧 | route ベースの安定IDを持つ |
| `<target-project>/docs/seo/files.json` | ページ単位ではない静的資産の監査情報 | robots, sitemap, llms, favicon の窓口 |
| `<target-project>/docs/seo/pages/<page-id>.json` | ページ単位の正規化済み監査成果物 | `head`, `body`, `links`, `structuredData` を含む |
| `<target-project>/docs/seo/summary.md` | 人間向けの監査要約 | 総合スコア、カテゴリ別スコア、重大指摘、次アクション |

`<page-id>` は URL path または route path から決定する安定IDとし、毎回同じページが同じファイル名になることを優先する。

### `summary.md` の役割

`<target-project>/docs/seo/summary.md` は人間向けの監査結果の入口とし、少なくとも以下を含む前提とする。

- 総合スコアとランク
- カテゴリ別スコア
- critical / error の重大指摘
- 直近で着手すべき次アクション
- `pages.json`, `files.json`, `pages/<page-id>.json` を一次情報源とした旨

### `pages/<page-id>.json` 初版スキーマ

初版のページ成果物は「中程度の詳細」とし、SEO判定だけでなく保守時の由来追跡にも使える粒度にする。

| フィールド | 必須 | 内容 |
|-----------|------|------|
| `pageId` | 必須 | route ベースの安定ID |
| `route` | 必須 | 公開URLまたは route path |
| `source.framework` | 必須 | `next-app`, `next-pages`, `astro`, `nuxt`, `static` など |
| `source.sourceFiles` | 必須 | 元になったファイル群 |
| `source.template` | 任意 | layout, page, template などの由来 |
| `source.renderMode` | 必須 | `static`, `ssg`, `ssr`, `csr`, `unknown` のいずれか |
| `source.locale` | 任意 | 言語・地域情報 |
| `head.title` | 任意 | 正規化済み title |
| `head.metaDescription` | 任意 | 正規化済み description |
| `head.canonical` | 任意 | canonical URL |
| `head.robots` | 任意 | robots directives |
| `head.hreflangs` | 任意 | hreflang 配列 |
| `head.openGraph` | 任意 | OGメタ情報 |
| `head.twitterCard` | 任意 | Twitter Card メタ情報 |
| `body.h1` | 任意 | 主見出し |
| `body.headings` | 任意 | 見出し階層の配列 |
| `body.textSummary` | 任意 | 本文要約または冒頭抜粋 |
| `body.textLength` | 任意 | 本文文字数 |
| `body.faqSignals` | 任意 | FAQの有無や件数 |
| `links.internal` | 任意 | 内部リンク一覧と件数 |
| `links.external` | 任意 | 外部リンク一覧と件数 |
| `links.emptyAnchors` | 任意 | 空アンカーの一覧 |
| `links.unsafeTargets` | 任意 | `target=\"_blank\"` で `rel` 不備の一覧 |
| `structuredData.rawBlocks` | 任意 | JSON-LD raw block 一覧 |
| `structuredData.types` | 任意 | 抽出された `@type` 一覧 |
| `structuredData.parseErrors` | 任意 | JSON-LD パースエラー |
| `collectionMeta.collectedBy` | 必須 | `static-analysis`, `build-html`, `preview`, `dev-server` など |
| `collectionMeta.usedRendering` | 必須 | レンダリング補完の有無 |
| `collectionMeta.warnings` | 任意 | 収集失敗や不確定情報の記録 |

### `files.json` 初版スキーマ

`<target-project>/docs/seo/files.json` はページ単位ではない資産の一次情報源とする。

| フィールド | 必須 | 内容 |
|-----------|------|------|
| `robotsTxt` | 任意 | 実パス、存在有無、本文、パース結果 |
| `sitemapXml` | 任意 | 実パス、存在有無、本文、パース結果 |
| `llmsTxt` | 任意 | 実パス、存在有無、本文、パース結果 |
| `favicon` | 任意 | 実パス、存在有無、検出元 |
| `discoveredPaths` | 必須 | 探索した候補パス一覧 |
| `missing` | 必須 | 見つからなかった必須/推奨ファイル一覧 |
| `parseWarnings` | 任意 | パース警告やフォーマット逸脱 |

T01-T07 と G01-G03 は原則 `files.json` を一次情報源として判定する。

### `manifest.json` 初版設計

`<target-project>/scripts/seo/manifest.json` は自動検出優先で、例外だけを上書きする設定ファイルとする。未指定項目はアダプタが推定し、指定された項目だけを override として扱う。

| フィールド | 必須 | 役割 | override ルール |
|-----------|------|------|-----------------|
| `framework` | 任意 | フレームワーク種別の明示 | 指定時は自動推定より優先 |
| `roots.appRoots` | 任意 | app router 系の探索起点 | 指定時は候補追加ではなく優先リスト化 |
| `roots.pageRoots` | 任意 | page ファイル探索起点 | 指定時は候補追加ではなく優先リスト化 |
| `roots.publicRoots` | 任意 | 静的資産探索起点 | 指定時は優先 |
| `roots.configFiles` | 任意 | 設定ファイル候補 | 指定時は優先 |
| `include` | 任意 | 監査に含める route/file pattern | 自動検出後に絞り込み適用 |
| `exclude` | 任意 | 監査から除外する route/file pattern | 自動検出後に除外適用 |
| `collect.preferStaticAnalysis` | 任意 | 静的解析を標準にするか | 未指定時は `true` |
| `collect.allowRenderingFallback` | 任意 | レンダリング補完を許可するか | 未指定時は `true` |
| `commands.build` | 任意 | build 実行コマンド | レンダリング補完時の候補 |
| `commands.dev` | 任意 | dev server 実行コマンド | 最終フォールバック候補 |
| `commands.preview` | 任意 | preview 実行コマンド | build 済み成果物の次候補 |
| `output.docsDir` | 任意 | 監査成果物出力先 | 未指定時は `<target-project>/docs/seo/` |
| `output.pagesDir` | 任意 | ページ成果物出力先 | 未指定時は `<target-project>/docs/seo/pages/` |
| `notes` | 任意 | 人間向けメモ | 判定には使わない |

### `collect` の標準戦略

`<target-project>/scripts/seo/collect.*` は以下の順で動く前提とする。

1. 静的解析で `head`, `body`, `links`, `structuredData` を回収する。
2. `title`, `canonical`, `robots`, `hreflang` など静的解析だけで確定しないページだけレンダリング対象にする。
3. レンダリング補完は `build` 済みHTML、`preview`、`dev server` の順で利用可能なものを選ぶ。
4. レンダリング不能でも監査は継続し、その理由を `collectionMeta.warnings` に記録する。

レンダリングは必須ではなく、不足分だけ補完する方針とする。初版では完全再現より導入容易性を優先する。

`include` / `exclude` は自動検出後のフィルタとして適用し、`commands.*` と `output.*` は manifest に指定があればその値を優先する。

### 成果物を一次情報源とするチェック再定義

少なくとも以下の項目は、元ソースの direct grep ではなく成果物のどのフィールドを見るかを企画書に明記する。

| チェック | 一次情報源 | 判定方法 |
|---------|------------|----------|
| `C01 title タグ存在` | `<target-project>/docs/seo/pages/<page-id>.json` の `head.title` | 空文字または欠損なら error |
| `T01 robots.txt 存在` | `<target-project>/docs/seo/files.json` の `robotsTxt` | `resolvedPath` 不在または `exists=false` なら warning |
| `T10 canonical タグ存在` | `<target-project>/docs/seo/pages/<page-id>.json` の `head.canonical` | 欠損なら warning |
| `S01 JSON-LD 存在` | `<target-project>/docs/seo/pages/<page-id>.json` の `structuredData.rawBlocks` | 空配列なら warning |
| `L01 内部リンク数` | `<target-project>/docs/seo/pages/<page-id>.json` の `links.internal` | 件数をカウントして集計 |

---

## カテゴリ1: テクニカルSEO（重み: 30%）

### 1A. クローラビリティ & インデクサビリティ

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| T01 | **robots.txt 存在** | warning | code | code | `<target-project>/docs/seo/files.json` の `robotsTxt.exists` と `robotsTxt.resolvedPath` を判定 |
| T02 | **robots.txt 構文エラー** | error | code | script | `<target-project>/docs/seo/files.json` の `robotsTxt.content` を `User-agent`, `Disallow`, `Allow` としてパース |
| T03 | **robots.txt で重要ページ遮断** | critical | code | script | `<target-project>/docs/seo/files.json` の `robotsTxt.content` と `pages.json` の主要routeを照合 |
| T04 | **robots.txt にSitemap指定** | warning | code | code | `<target-project>/docs/seo/files.json` の `robotsTxt.directives` から `Sitemap` を確認 |
| T05 | **AIクローラーのブロック** | warning | code | code | `<target-project>/docs/seo/files.json` の `robotsTxt.directives` で `GPTBot`, `ClaudeBot`, `PerplexityBot` を確認 |
| T06 | **sitemap.xml 存在** | warning | code | code | `<target-project>/docs/seo/files.json` の `sitemapXml.exists` と `sitemapXml.resolvedPath` を判定 |
| T07 | **sitemap.xml 構文** | error | code | script | `<target-project>/docs/seo/files.json` の `sitemapXml.content` をXMLとして検証 |
| T08 | **meta robots** | error | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `head.robots` に `noindex` があるか判定 |
| T09 | **X-Robots-Tag** | error | live | curl | `headers.txt` から `X-Robots-Tag: noindex` を検出 |
| T10 | **canonical タグ存在** | warning | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `head.canonical` の有無 |
| T11 | **canonical URL妥当性** | error | code | script | `<target-project>/docs/seo/pages/<page-id>.json` の `head.canonical` が空・相対・不正形式でないか検証 |
| T12 | **hreflang 存在** | notice | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `head.hreflangs` 配列の有無 |
| T13 | **hreflang 言語コード妥当性** | error | code | script | `<target-project>/docs/seo/pages/<page-id>.json` の `head.hreflangs` を ISO 639-1 と照合 |
| T14 | **HTTPステータスコード** | error | live | curl | 最終ステータスコード取得。4xx/5xx = error |
| T15 | **リダイレクトチェーン** | warning | live | curl | リダイレクト回数カウント。3段以上 = warning |
| T16 | **WWW解決** | warning | live | curl | www あり/なし両方で同一ページに解決されるか |
| T17 | **HTTP→HTTPSリダイレクト** | error | live | curl | `http://` でアクセスして `https://` にリダイレクトされるか |

### 1B. セキュリティ

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| T18 | **HTTPS対応** | critical | live | curl | URLスキームが `https://` か。非対応ならクリティカル係数0.5 |
| T19 | **SSL証明書有効性** | error | live | curl | `curl -vI 2>&1` で有効期限取得。30日以内=warning、期限切れ=error |
| T20 | **SSL プロトコルバージョン** | error | live | curl | `curl --tlsv1.2` 成功確認。TLS 1.0/1.1のみ=error |
| T21 | **HSTS ヘッダー** | notice | live | curl | `Strict-Transport-Security` を検出。max-age≥31536000 推奨 |
| T22 | **Mixed Content** | error | code | Grep | HTML内の `http://` リソース参照（src, href）を検出 |
| T23 | **HTTP/2 対応** | notice | live | curl | `curl --http2 -sI` で `HTTP/2` 応答を確認 |
| T24 | **セキュリティヘッダー** | notice | live | curl | CSP, X-Content-Type-Options, X-Frame-Options の有無 |
| T25 | **Unsafe Cross-Origin Links** | notice | code | Grep | `target="_blank"` の `<a>` に `rel="noopener"` があるか |

### 1C. URL品質

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| T26 | **URL長** | notice | code | script | HTMLリンクのhref文字数カウント。200文字超=notice |
| T27 | **URL内アンダースコア** | notice | code | Grep | URLパス部分に `_` が含まれるか |
| T28 | **URLパラメータ過多** | warning | code | script | `?` 以降のパラメータ数。3個以上=warning |
| T29 | **URL階層深度** | warning | code | script | パスの `/` 数カウント。5階層超=warning |

---

## カテゴリ2: コンテンツ品質（重み: 25%）

### 2A. メタ情報 & HTML品質

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| C01 | **title タグ存在** | error | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `head.title` が空でないか判定 |
| C02 | **title 長さ** | warning | code | script | `<target-project>/docs/seo/pages/<page-id>.json` の `head.title` 文字数。30未満 or 60超 = warning |
| C03 | **meta description 存在** | warning | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `head.metaDescription` の有無 |
| C04 | **meta description 長さ** | warning | code | script | `<target-project>/docs/seo/pages/<page-id>.json` の `head.metaDescription` 文字数。70未満 or 160超 = warning |
| C05 | **H1 タグ存在** | error | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `body.h1` の有無 |
| C06 | **H1 が1つだけか** | notice | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `body.headings` から H1 件数を集計 |
| C07 | **H1 と title の重複** | warning | code | script | `<target-project>/docs/seo/pages/<page-id>.json` の `body.h1` と `head.title` を比較 |
| C08 | **見出し階層の論理性** | warning | code | script | `<target-project>/docs/seo/pages/<page-id>.json` の `body.headings` を使って H1→H2→H3 の順序を検証 |
| C09 | **画像 alt 属性** | warning | code | Grep | `<img>` の総数と `alt` 属性なしの数をカウント。充足率算出 |
| C10 | **レスポンシブ画像（srcset）** | notice | code | Grep | `<img>` に `srcset` 属性があるか |
| C11 | **モダン画像フォーマット** | notice | code | Grep | `<img src>` / `<source>` の拡張子。WebP/AVIF が使われているか |
| C12 | **画像アスペクト比（CLS防止）** | warning | code | Grep | `<img>` に `width`/`height` 属性があるか。未指定=CLS原因 |
| C13 | **lang 属性** | warning | code | Grep | `<html lang="...">` の有無と妥当性 |
| C14 | **charset 宣言** | notice | code | Grep | `<meta charset="UTF-8">` の有無 |
| C15 | **doctype 宣言** | notice | code | Grep | `<!DOCTYPE html>` の有無 |
| C16 | **viewport メタタグ** | error | code | Grep | `<meta name="viewport">` の有無と `width=device-width` 含有 |
| C17 | **Open Graph タグ** | notice | code | Grep | `og:title`, `og:description`, `og:image` の有無 |
| C18 | **Twitter Card タグ** | notice | code | Grep | `twitter:card`, `twitter:title` の有無 |
| C19 | **favicon 存在** | notice | code | Grep/Glob | `<link rel="icon">` の有無、またはプロジェクトに `favicon.ico` が存在するか |
| C20 | **Deprecated HTML タグ** | notice | code | Grep | `<font>`, `<center>`, `<marquee>` 等の検出 |
| C21 | **frames 使用** | warning | code | Grep | `<frame>`, `<iframe>`（主要コンテンツ用）の検出 |
| C22 | **DOM Size** | warning | code | script | HTMLタグ総数カウント。1500超=warning |
| C23 | **HTML Page Size** | warning | code | script | HTMLファイルサイズ。1MB超=warning |

### 2B. コンテンツ分析

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| C24 | **テキスト量（ワードカウント）** | warning | code | script | HTMLタグ除去後のテキスト文字数。日本語400字未満=warning |
| C25 | **テキスト/HTML比率** | warning | code | script | テキストバイト数 / HTML全体バイト数。10%未満=warning |
| C26 | **可読性スコア（日本語）** | notice | code | agent | Read でテキスト抽出 → プロンプトで文の平均長・漢字率・段落構成を評価 |
| C27 | **アンサーファースト構造** | warning | code | hybrid | Read: H1直後200文字抽出 → agent: 検索意図への直接回答があるか判定 |
| C28 | **コンテンツ鮮度** | warning | code | hybrid | Grep: `dateModified`(JSON-LD), `<time>`タグ抽出 → 現在日との差分計算 |
| C29 | **陳腐化シグナル** | notice | code | agent | Read でテキスト → 古い年号（「2022年最新」等）の検出 |
| C30 | **キーワード最適化** | notice | code | hybrid | Grep: title/H1/本文から頻出語抽出 → agent: KW配置の自然さ評価 |

---

## カテゴリ3: 内部リンク & リンク品質（重み: 15%）

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| L01 | **内部リンク数** | notice | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `links.internal` 件数を集計 |
| L02 | **外部リンク数** | notice | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `links.external` 件数を集計 |
| L03 | **リンク過多** | warning | code | script | `<target-project>/docs/seo/pages/<page-id>.json` の `links.internal` + `links.external` の総数。100超=notice、300超=warning |
| L04 | **アンカーテキスト品質** | warning | code | hybrid | `<target-project>/docs/seo/pages/<page-id>.json` のリンクテキストを抽出 → agent が「こちら」「click here」等を判定 |
| L05 | **空アンカーテキスト** | warning | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `links.emptyAnchors` を検出 |
| L06 | **nofollow 内部リンク** | warning | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `links.internal` で `rel=\"nofollow\"` を検出 |
| L07 | **壊れた内部リンク候補** | notice | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `links.internal` で空href, `javascript:void(0)`, `#` を検出 |
| L08 | **unsafe cross-origin links** | notice | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `links.unsafeTargets` を検出 |
| L09 | **パンくずリスト** | notice | code | Grep | `BreadcrumbList` JSON-LD、または `<nav aria-label="breadcrumb">` |
| L10 | **meta refresh リダイレクト** | error | code | Grep | `<meta http-equiv="refresh">` の検出 |

---

## カテゴリ4: UX / 表示速度（重み: 20%）

### 4A. Core Web Vitals & サーバー応答

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| U01 | **LCP（Largest Contentful Paint）** | error | api | PSI API | ≤2.5s=Good, ≤4.0s=NI, >4.0s=Poor |
| U02 | **INP（Interaction to Next Paint）** | error | api | PSI API | ≤200ms=Good, ≤500ms=NI, >500ms=Poor |
| U03 | **CLS（Cumulative Layout Shift）** | error | api | PSI API | ≤0.1=Good, ≤0.25=NI, >0.25=Poor |
| U04 | **FCP（First Contentful Paint）** | warning | api | PSI API | ≤1.8s=Good, ≤3.0s=NI, >3.0s=Poor |
| U05 | **TTFB（Time To First Byte）** | warning | live | curl | `curl -w "%{time_starttransfer}"` 計測。0.8s超=warning |
| U06 | **Lighthouse Performance スコア** | notice | api | PSI API | 50未満=warning。参考値 |
| U07 | **Lighthouse SEO スコア** | notice | api | PSI API | 参考値として表示 |

### 4B. パフォーマンス最適化

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| U08 | **GZIP/Brotli 圧縮** | warning | live | curl | `Content-Encoding: gzip` or `br` を確認 |
| U09 | **JS ミニファイ** | notice | code | Grep | `<script src>` のURL取得、`.min.js` パターン確認 |
| U10 | **CSS ミニファイ** | notice | code | Grep | `<link rel="stylesheet">` のURL、`.min.css` パターン確認 |
| U11 | **JS/CSS キャッシュヘッダー** | warning | live | curl | 主要JS/CSSの `Cache-Control` 確認 |
| U12 | **JS/CSS ファイル数** | notice | code | Grep | `<script src>` + `<link rel="stylesheet">` の数。20超=notice |
| U13 | **JS/CSS 合計サイズ** | warning | code | script | プロジェクト内のJS/CSSファイルサイズ合計。1MB超=warning |
| U14 | **レンダーブロッキングリソース** | warning | code | Grep | `<head>`内の `<script>` で `defer`/`async` なし、`<link rel="stylesheet">` の数 |
| U15 | **画像 lazy loading** | notice | code | Grep | `<img>` に `loading="lazy"` があるか |

---

## カテゴリ5: 構造化データ & AI対応（重み: ※後述）

### 5A. 構造化データ

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| S01 | **JSON-LD 存在** | warning | code | code | `<target-project>/docs/seo/pages/<page-id>.json` の `structuredData.rawBlocks` の有無 |
| S02 | **JSON-LD 構文妥当性** | error | code | script | `<target-project>/docs/seo/pages/<page-id>.json` の `structuredData.parseErrors` と raw block を検証 |
| S03 | **@type 検出** | notice | code | script | `<target-project>/docs/seo/pages/<page-id>.json` の `structuredData.types` 一覧を抽出 |
| S04 | **必須プロパティ充足** | warning | code | hybrid | `<target-project>/docs/seo/pages/<page-id>.json` の `structuredData.rawBlocks` を agent が Schema.org 必須/推奨プロパティと照合 |
| S05 | **Organization schema** | notice | code | Grep | `@type.*Organization` の有無。name, url, logo の存在 |
| S06 | **BreadcrumbList schema** | notice | code | Grep | `@type.*BreadcrumbList` の有無 |
| S07 | **FAQPage schema** | notice | code | Grep | `@type.*FAQPage` の有無 |
| S08 | **Article schema** | notice | code | Grep | `@type.*Article` の有無。author, datePublished の存在 |

### 5B. AI検索対応（GEO）

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| G01 | **llms.txt 存在** | notice | code | code | `<target-project>/docs/seo/files.json` の `llmsTxt.exists` と `llmsTxt.resolvedPath` を判定 |
| G02 | **llms.txt フォーマット** | notice | code | script | `<target-project>/docs/seo/files.json` の `llmsTxt.content` を読み、セクション構造を検証 |
| G03 | **AIクローラー許可** | warning | code | code | `<target-project>/docs/seo/files.json` の `robotsTxt.directives` を参照して T05 と共通判定 |
| G04 | **セマンティックHTML使用率** | notice | code | Grep | `<article>`, `<section>`, `<nav>`, `<main>` 数 vs `<div>` 総数の比率 |
| G05 | **Answer-First 構造** | warning | code | hybrid | Read: H1直後テキスト抽出 → agent: 直接回答があるか判定 |
| G06 | **Direct Question Headers** | notice | code | Grep | H2/H3に疑問文パターン（「?」「〜とは」「How」「What」） |
| G07 | **Named Source Attribution** | notice | code | agent | Read → 「〇〇によると」「〇〇の調査」等の具体的出典パターン検出 |
| G08 | **FAQ セクション** | notice | code | hybrid | Grep: FAQPage schema + H2/H3のFAQパターン → agent: 3問以上あるか |
| G09 | **コンテンツ更新日の明示** | notice | code | Grep | `dateModified`(JSON-LD)、`<time datetime>` タグの有無 |
| G10 | **コンテンツ長の適切さ（AI向け）** | notice | code | hybrid | script: テキスト文字数 → 10000字超でセクション分割されているか |

---

## カテゴリ6: E-E-A-T & 信頼性

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| E01 | **会社概要ページへのリンク** | notice | code | Grep | `/about`, `/company`, `会社概要` リンク検出 |
| E02 | **プライバシーポリシーへのリンク** | warning | code | Grep | `/privacy`, `プライバシーポリシー` リンク検出 |
| E03 | **利用規約へのリンク** | notice | code | Grep | `/terms`, `利用規約` リンク検出 |
| E04 | **お問い合わせページへのリンク** | notice | code | Grep | `/contact`, `お問い合わせ` リンク検出 |
| E05 | **著者情報（Person schema）** | notice | code | Grep | JSON-LD内の `@type.*Person`。name, jobTitle の有無 |
| E06 | **著者バイライン** | notice | code | hybrid | Grep: 著者名パターン検出 → agent: バイラインとして妥当か |
| E07 | **Organization schema** | notice | code | Grep | S05と共有 |
| E08 | **外部リンク（引用・出典）** | notice | code | Grep | 外部リンク数、`<cite>` タグ、「出典」「参考」文言の有無 |
| E09 | **Plaintext メールアドレス** | notice | code | Grep | `mailto:` を含まないメールアドレスパターン検出 |
| E10 | **E-E-A-T総合評価** | — | code | agent | E01-E09の結果をまとめてE-E-A-T総合評価・改善提案を生成 |

---

## カテゴリ7: ローカルSEO（重み: 10%）

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| R01 | **LocalBusiness schema 存在** | notice | code | Grep | JSON-LD内の `@type.*LocalBusiness` 検出 |
| R02 | **NAP情報の存在** | warning | code | hybrid | Grep: 電話番号パターン・住所パターン検出 → agent: NAP整合性判定 |
| R03 | **NAP と構造化データの一致** | warning | code | hybrid | Grep: schema内のname/address/telephone → 本文との照合 |
| R04 | **GeoCoordinates** | notice | code | Grep | JSON-LD内の `latitude`, `longitude` の有無 |
| R05 | **営業時間（openingHours）** | notice | code | Grep | `openingHoursSpecification` の有無 |
| R06 | **ローカルSEO該当判定** | — | code | agent | ページ内容からローカルビジネスか判定。非該当→カテゴリ除外・重み再配分 |

---

## カテゴリ8: その他

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| X01 | **Custom 404ページ** | notice | live | curl | 存在しないURLにcurlしてカスタム404が返るか |
| X02 | **SPF レコード** | notice | live | script | `dig TXT <domain>` で `v=spf1` の有無 |
| X03 | **Analytics設置** | notice | code | Grep | `gtag`, `GoogleAnalyticsObject`, `gtm.js` パターン検出 |
| X04 | **JS コンソールエラー** | notice | api | PSI API | diagnostics情報から参照 |

---

## スコアリング設計

### カテゴリ別重み（デフォルト）

| カテゴリ | 重み | チェック項目数 |
|----------|------|-------------|
| テクニカルSEO | 30% | 30項目（T01-T30） |
| コンテンツ品質 | 25% | 30項目（C01-C30） |
| 内部リンク & リンク品質 | 15% | 10項目（L01-L10） |
| UX / 表示速度 | 20% | 15項目（U01-U15） |
| 構造化データ & AI対応 | ※ | 18項目（S01-S08, G01-G10） |
| E-E-A-T | ※ | 10項目（E01-E10） |
| ローカルSEO | ※ | 6項目（R01-R06） |
| その他 | ※ | 4項目（X01-X04） |

※ 構造化データ/AI対応、E-E-A-T、ローカルSEO、その他は上位4カテゴリのサブ項目として組み込む:
- 構造化データ(S01-S08) → テクニカルSEOに統合
- GEO(G01-G10) → コンテンツ品質に統合
- E-E-A-T(E01-E10) → コンテンツ品質に統合
- ローカルSEO(R01-R06) → 独立カテゴリ（該当時のみ）
- その他(X01-X04) → テクニカルSEOに統合

### 最終カテゴリ構成（SEGO準拠 5カテゴリ）

| カテゴリ | 重み | 含む項目 |
|----------|------|---------|
| **テクニカルSEO** | 30% | T01-T30 + S01-S08 + X01-X04 = 42項目 |
| **コンテンツ品質** | 25% | C01-C30 + G01-G10 + E01-E10 = 50項目 |
| **内部リンク** | 15% | L01-L10 = 10項目 |
| **UX / 表示速度** | 20% | U01-U15 = 15項目 |
| **ローカル / サイテーション** | 10% | R01-R06 = 6項目 |

**合計: 123項目**

### 各項目のスコア配点

```
カテゴリスコア = 100 - Σ(該当項目の減点)

減点値:
  critical  → そのカテゴリスコアを上限50に制限
  error     → -8点
  warning   → -3点
  notice    → -1点

下限: 0点
```

### 総合スコア

```
総合スコア = Σ(カテゴリスコア × カテゴリ重み) × クリティカル係数

クリティカル係数:
  致命的問題なし → 1.0
  HTTPS未対応   → 0.5
  全体noindex   → 0.3
```

### ランク

| ランク | スコア | 説明 |
|--------|--------|------|
| A | 90-100 | 優秀 |
| B | 70-89 | 良好 |
| C | 50-69 | 平均的 |
| D | 30-49 | 要改善 |
| F | 0-29 | 致命的 |

### 業種別プロファイル

| 業種 | テクニカル | コンテンツ | リンク | UX | ローカル |
|------|-----------|-----------|--------|-----|---------|
| メディア/ブログ | 25% | 35% | 20% | 15% | 5% |
| EC | 30% | 20% | 15% | 25% | 10% |
| コーポレート | 25% | 20% | 10% | 20% | 25% |
| LP | 20% | 25% | 5% | 30% | 20% |

---

## 実装アーキテクチャ

### ファイル構成

```
<skill-root>/
├── scripts/                        # 汎用スキル側の共通スクリプト
│   ├── fetch-live.sh               # 本番URLからデータ取得（curl並列）
│   ├── call-psi-api.sh             # PSI API呼び出し（CWV, Lighthouse）
│   └── score.sh                    # 全結果集約 → スコア算出
├── agents/                         # LLM判定が必要な項目
│   ├── content-quality.md          # C26,C27,C29,C30: 可読性・アンサーファースト
│   ├── geo-readiness.md            # G05,G07,G08,G10: AI検索対応評価
│   ├── eeat-assessment.md          # E06,E10: E-E-A-T総合評価
│   ├── local-seo.md                # R02,R03,R06: ローカルSEO判定
│   ├── link-quality.md             # L04: アンカーテキスト品質
│   ├── structured-data-review.md   # S04: 構造化データプロパティ照合
│   └── report-generator.md         # 最終レポート生成（改善提案付き）
└── SKILL.md                        # スキル本体（実行フロー定義）
```

監査対象プロジェクト側には、別途以下を生成・保守する想定:

```
<target-project>/
├── scripts/
│   └── seo/
│       ├── manifest.json           # 自動検出の override 設定
│       ├── discover.sh             # 監査対象ページ/設定ファイルの発見
│       ├── collect.sh              # 静的解析優先 + 必要時レンダリング補完
│       └── files.sh                # robots/sitemap/llms/favicon の実パス解決
└── docs/
    └── seo/
        ├── pages.json
        ├── files.json
        ├── summary.md
        └── pages/
            └── <page-id>.json
```

**Layer 1（code）は「直接ソースを舐める」のではなく、原則として `<target-project>/scripts/seo/` が生成した監査アーティファクトを読む。**
単純な静的ファイルだけは汎用スキル側で直接 `Read/Grep/Glob` してよいが、フレームワーク依存の head 生成やページ列挙はアダプタに寄せる。

### 実行フロー

```
Phase 0: プロジェクト検出 & モード決定
  プロジェクト構成を確認
  ├─ framework, app root, pages root, config file を推定
  ├─ <target-project>/scripts/seo/ の有無確認
  └─ AskUserQuestion → 本番URLの有無確認

Phase 0.5: アダプタ生成/更新
  <target-project>/scripts/seo/ が無ければ生成
  <target-project>/scripts/seo/manifest.json と現状構成がズレていれば refresh
  以降のチェックはこの adapter を一次情報源として扱う

Phase 1: アーティファクト収集（Layer 1: code）— 常に実行
  <target-project>/scripts/seo/discover.*
  <target-project>/scripts/seo/collect.*
  <target-project>/scripts/seo/files.*
  ├─ <target-project>/docs/seo/pages.json
  ├─ <target-project>/docs/seo/files.json
  └─ <target-project>/docs/seo/pages/<page-id>.json（head/body/links/structuredData）

Phase 2: 汎用チェック実行（Layer 1: code）— 常に実行
  Read/Grep/jq 等で監査アーティファクトを評価
  単純な静的ファイルは直接読み込み可

Phase 3: ライブチェック（Layer 2: live）— 本番URL時のみ
  <skill-root>/scripts/fetch-live.sh <URL>
  ├─ SSL証明書、HTTPヘッダー、リダイレクト、TTFB等
  └─ 並列実行、5秒タイムアウト

Phase 4: API（Layer 3: api）— 本番URL時のみ
  <skill-root>/scripts/call-psi-api.sh <URL>
  └─ CWV（LCP, INP, CLS, FCP）+ Lighthouseスコア

Phase 5: Agent解析 — Phase 1-4 の結果を入力
  <skill-root>/agents/content-quality.md
  <skill-root>/agents/geo-readiness.md
  <skill-root>/agents/eeat-assessment.md
  <skill-root>/agents/local-seo.md
  <skill-root>/agents/link-quality.md
  <skill-root>/agents/structured-data-review.md
  （並列実行可能）

Phase 6: スコア集計 & レポート生成
  <skill-root>/scripts/score.sh            ← `<target-project>/docs/seo/*.json` を集約
  <skill-root>/agents/report-generator.md  ← `<target-project>/docs/seo/summary.md` を生成
```

### Layer別の内訳

| Layer | 項目数 | 割合 | 実行条件 |
|-------|--------|------|----------|
| **code**（アーティファクト/静的ファイル解析） | ~100項目 | ~81% | 常に実行 |
| **live**（curl） | ~16項目 | ~13% | 本番URL提供時のみ |
| **api**（PSI API） | ~7項目 | ~6% | 本番URL提供時のみ |

**Code-onlyモードでも全体の81%の項目を検査可能。**

### 実装方式の内訳

| 方式 | 項目数 | 説明 |
|------|--------|------|
| **adapter + code** | ~75項目 | アダプタが収集したアーティファクトに対して確定的ルールを適用 |
| **script**（bash/jq等） | ~20項目 | パース・計算が必要 |
| **agent**（LLMプロンプト） | ~8項目 | 意味理解が必要 |
| **hybrid**（adapter/code+agent） | ~13項目 | 抽出→判定の2段階 |
| **live**（curl） | ~16項目 | HTTPレスポンス必要 |
| **api**（PSI API） | ~7項目 | 外部API |

## 受け入れ条件

この企画書の次版は、以下を満たせば完成とする。

- すべてのパスが `<skill-root>` または `<target-project>` 付きで記載されている
- `<target-project>/docs/seo/pages/<page-id>.json` と `<target-project>/docs/seo/files.json` の必須フィールドが表形式で定義されている
- `<target-project>/scripts/seo/manifest.json` の必須/任意項目と override ルールが定義されている
- `collect` の静的解析とレンダリング補完の分岐条件が書かれている
- 少なくとも `C01`, `T01`, `T10`, `S01`, `L01` が「どの成果物のどのフィールドを見るか」で説明されている
- `<target-project>/docs/seo/` 配下に JSON と要約を Git 管理する方針が明記されている

---

## 情報源

### ツール公式ドキュメント（実チェック項目取得）
- [Semrush Site Audit Issues List](https://www.semrush.com/kb/542-site-audit-issues-list) — 全140+項目
- [Lighthouse SEO Audits](https://unlighthouse.dev/learn-lighthouse/seo) — 全8項目
- [Ahrefs Site Audit](https://help.ahrefs.com/en/articles/1420169-how-to-configure-pre-set-issues-within-ahrefs-site-audit) — 170+項目
- [SEO Site Checkup Tools](https://seositecheckup.com/tools) — 全70+項目
- [Seobility SEO Checker](https://www.seobility.net/en/seocheck/) — 200+項目

### スコアリング手法
- [Lighthouse Scoring Docs](https://github.com/GoogleChrome/lighthouse/blob/main/docs/scoring.md)
- [Ahrefs Health Score](https://help.ahrefs.com/en/articles/1424673-what-is-health-score-and-how-is-it-calculated-in-ahrefs-site-audit)
- [Semrush Site Health Score](https://www.semrush.com/kb/114-total-score)
- [SEO Grade Guide 2026](https://seojuice.com/blog/seo-grade-guide/)

### AI検索対応（GEO）
- [GEO Best Practices 2026](https://firstpagesage.com/seo-blog/generative-engine-optimization-best-practices/)
- [GEO Full Guide](https://searchengineland.com/mastering-generative-engine-optimization-in-2026-full-guide-469142)
- [GEO Research Paper](https://arxiv.org/pdf/2311.09735)
- [LLM SEO 4-Point Audit](https://www.dataslayer.ai/blog/llm-seo-audit-chatgpt-gemini-perplexity)
- [Semrush AI Search Health](https://www.semrush.com/kb/1601-ai-search-health-audit)

### E-E-A-T
- [E-E-A-T Audit: 220+ Markers](https://ahrefs.com/blog/eeat-audit/)
- [E-E-A-T Checklist](https://backlinko.com/eeat-checklist)

### ローカルSEO
- [NAP Audits](https://daltonluka.com/blog/nap-audits)
- [BrightLocal Citation Tracker](https://www.brightlocal.com/local-seo-tools/auditing/citation-tracker/)

### OSS参考
- [SEOnaut](https://github.com/StJudeWasHere/seonaut)
- [seo-audits-toolkit](https://github.com/StanGirard/seo-audits-toolkit)
