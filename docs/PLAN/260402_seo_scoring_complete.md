# SEO診断スキル 完全チェックリスト & 実装設計

> **目的**: ローカル動作のSEO診断スキルで使用する全チェック項目と実装方式の定義
> **作成日**: 2026-04-02
> **前提**: ローカル実行（curl でHTML/ヘッダー取得済み → 解析）。サイト全体クロールは不要。
> **参照ツール**: Semrush(140+), Ahrefs(170+), Lighthouse(8), SEO Site Checkup(70+), Seobility(200+)

---

## 実装方式の定義

| 方式 | 配置 | 用途 | 例 |
|------|------|------|-----|
| **script** | `scripts/` | 確定的ルールで判定可能。bash/jq/grep等で実装 | HTMLタグ有無、ヘッダー値、文字数カウント |
| **agent** | `agents/` | LLMの判断が必要。プロンプトで実装 | コンテンツ品質、可読性、E-E-A-T評価 |
| **api** | `scripts/` | 外部API呼び出し。bash+curl で実装 | PageSpeed Insights、CrUX |
| **hybrid** | 両方 | scriptで抽出 → agentで判定 | アンカーテキスト品質、アンサーファースト |

### データ取得フロー（前処理）

```
scripts/fetch.sh <URL>
  ├─ curl -sIL → headers.txt（レスポンスヘッダー + リダイレクトチェーン）
  ├─ curl -sL  → page.html（最終HTML）
  ├─ curl -s <origin>/robots.txt → robots.txt
  ├─ curl -s <origin>/sitemap.xml → sitemap.xml
  ├─ curl -s <origin>/llms.txt → llms.txt
  ├─ curl -s <origin>/favicon.ico -o /dev/null -w "%{http_code}" → favicon_status
  └─ dig +short <domain> → dns.txt
  （全て並列実行、5秒タイムアウト）
```

---

## カテゴリ1: テクニカルSEO（重み: 30%）

### 1A. クローラビリティ & インデクサビリティ

| # | チェック項目 | 深刻度 | 方式 | 実装方法 |
|---|------------|--------|------|----------|
| T01 | **robots.txt 存在** | warning | script | `robots.txt` のHTTPステータスが200か確認 |
| T02 | **robots.txt 構文エラー** | error | script | `User-agent`, `Disallow`, `Allow` の構文パース。不正行を検出 |
| T03 | **robots.txt で重要ページ遮断** | critical | script | `Disallow: /` の有無。対象URLパスがDisallowに該当するか判定 |
| T04 | **robots.txt にSitemap指定** | warning | script | `Sitemap:` ディレクティブの有無を grep |
| T05 | **AIクローラーのブロック** | warning | script | `GPTBot`, `ClaudeBot`, `PerplexityBot` が Disallow されているか確認 |
| T06 | **sitemap.xml 存在** | warning | script | `sitemap.xml` のHTTPステータスが200か確認 |
| T07 | **sitemap.xml 構文** | error | script | XMLとして整形式（well-formed）か検証。`xmllint` 等 |
| T08 | **meta robots** | error | script | `<meta name="robots" content="noindex">` の検出。`page.html` を grep |
| T09 | **X-Robots-Tag** | error | script | `headers.txt` から `X-Robots-Tag: noindex` を検出 |
| T10 | **canonical タグ存在** | warning | script | `<link rel="canonical" href="...">` の有無を grep |
| T11 | **canonical 自己参照** | notice | script | canonical href が現在のURLと一致するか比較 |
| T12 | **canonical 矛盾** | error | script | canonical が存在するが不正URL（相対パス、空）の検出 |
| T13 | **hreflang 存在** | notice | script | `<link rel="alternate" hreflang="...">` の検出 |
| T14 | **hreflang 言語コード妥当性** | error | script | ISO 639-1 コードとの照合 |
| T15 | **HTTPステータスコード** | error | script | `headers.txt` から最終ステータスコード取得。4xx/5xx = error |
| T16 | **リダイレクトチェーン** | warning | script | `headers.txt` のリダイレクト回数カウント。3段以上 = warning |
| T17 | **WWW解決** | warning | script | www あり/なしの両方にcurl して同一ページに解決されるか |
| T18 | **HTTP→HTTPSリダイレクト** | error | script | `http://` でアクセスして `https://` にリダイレクトされるか |

### 1B. セキュリティ

| # | チェック項目 | 深刻度 | 方式 | 実装方法 |
|---|------------|--------|------|----------|
| T19 | **HTTPS対応** | critical | script | URLスキームが `https://` か。非対応ならクリティカル係数0.5 |
| T20 | **SSL証明書有効性** | error | script | `curl -vI 2>&1 \| grep "expire date"` で有効期限取得。30日以内=warning、期限切れ=error |
| T21 | **SSL プロトコルバージョン** | error | script | `curl --tlsv1.2` が成功するか。TLS 1.0/1.1のみ=error |
| T22 | **HSTS ヘッダー** | notice | script | `headers.txt` から `Strict-Transport-Security` を検出。max-age≥31536000 推奨 |
| T23 | **Mixed Content** | error | script | `page.html` 内の `http://` リソース参照（src, href）を grep。HTTPS ページ上なら error |
| T24 | **HTTP/2 対応** | notice | script | `curl --http2 -sI` で `HTTP/2` 応答を確認 |
| T25 | **セキュリティヘッダー** | notice | script | `headers.txt` から CSP, X-Content-Type-Options, X-Frame-Options の有無 |
| T26 | **Unsafe Cross-Origin Links** | notice | script | `target="_blank"` の `<a>` に `rel="noopener"` があるか grep |

### 1C. URL品質

| # | チェック項目 | 深刻度 | 方式 | 実装方法 |
|---|------------|--------|------|----------|
| T27 | **URL長** | notice | script | URLの文字数カウント。200文字超=notice |
| T28 | **URL内アンダースコア** | notice | script | URLパス部分に `_` が含まれるか。ハイフン推奨 |
| T29 | **URLパラメータ過多** | warning | script | `?` 以降のパラメータ数カウント。3個以上=warning |
| T30 | **URL階層深度** | warning | script | パスの `/` 数カウント。5階層超=warning |

---

## カテゴリ2: コンテンツ品質（重み: 25%）

### 2A. メタ情報 & HTML品質

| # | チェック項目 | 深刻度 | 方式 | 実装方法 |
|---|------------|--------|------|----------|
| C01 | **title タグ存在** | error | script | `<title>` タグの有無。空の場合も error |
| C02 | **title 長さ** | warning | script | 文字数カウント。30未満 or 60超 = warning |
| C03 | **meta description 存在** | warning | script | `<meta name="description">` の有無 |
| C04 | **meta description 長さ** | warning | script | 文字数カウント。70未満 or 160超 = warning |
| C05 | **H1 タグ存在** | error | script | `<h1>` の有無 |
| C06 | **H1 が1つだけか** | notice | script | `<h1>` の出現回数カウント。2以上=notice |
| C07 | **H1 と title の重複** | warning | script | H1テキストとtitleテキストの完全一致チェック |
| C08 | **見出し階層の論理性** | warning | script | H1→H2→H3 の順序チェック。スキップ（H1→H3等）を検出 |
| C09 | **画像 alt 属性** | warning | script | `<img>` の総数と `alt` 属性なしの数をカウント。充足率算出 |
| C10 | **レスポンシブ画像（srcset）** | notice | script | `<img>` に `srcset` 属性があるか。主要画像で未使用=notice |
| C11 | **モダン画像フォーマット** | notice | script | `<img src>` の拡張子/Content-Type。WebP/AVIF が使われているか |
| C12 | **画像アスペクト比（CLS防止）** | warning | script | `<img>` に `width`/`height` 属性があるか。未指定=CLS原因 |
| C13 | **lang 属性** | warning | script | `<html lang="...">` の有無と妥当性 |
| C14 | **charset 宣言** | notice | script | `<meta charset="UTF-8">` の有無 |
| C15 | **doctype 宣言** | notice | script | `<!DOCTYPE html>` の有無 |
| C16 | **viewport メタタグ** | error | script | `<meta name="viewport">` の有無と `width=device-width` 含有 |
| C17 | **Open Graph タグ** | notice | script | `og:title`, `og:description`, `og:image` の有無 |
| C18 | **Twitter Card タグ** | notice | script | `twitter:card`, `twitter:title` の有無 |
| C19 | **favicon 存在** | notice | script | `/favicon.ico` のHTTPステータス、または `<link rel="icon">` の有無 |
| C20 | **Deprecated HTML タグ** | notice | script | `<font>`, `<center>`, `<marquee>` 等の検出 |
| C21 | **frames 使用** | warning | script | `<frame>`, `<iframe>`（広告以外の主要コンテンツ用）の検出 |
| C22 | **DOM Size** | warning | script | HTMLタグ総数カウント。1500超=warning（`grep -c '<' page.html` 近似） |
| C23 | **HTML Page Size** | warning | script | `page.html` のファイルサイズ。1MB超=warning |

### 2B. コンテンツ分析（LLM必要）

| # | チェック項目 | 深刻度 | 方式 | 実装方法 |
|---|------------|--------|------|----------|
| C24 | **テキスト量（ワードカウント）** | warning | script | HTMLタグ除去後のテキスト文字数。200語(日本語400字)未満=warning |
| C25 | **テキスト/HTML比率** | warning | script | テキストバイト数 / HTML全体バイト数。10%未満=warning |
| C26 | **可読性スコア（日本語）** | notice | agent | HTMLからテキスト抽出 → プロンプトで文の平均長・漢字率・段落構成を評価 |
| C27 | **アンサーファースト構造** | warning | hybrid | script: H1直後200文字を抽出 → agent: 検索意図への直接回答があるか判定 |
| C28 | **コンテンツ鮮度** | warning | hybrid | script: `dateModified`(JSON-LD), `Last-Modified`ヘッダー, `<time>`タグ抽出 → 現在日との差分計算。12ヶ月超=warning |
| C29 | **陳腐化シグナル** | notice | agent | テキスト内の古い年号（「2022年最新」等）、廃止サービスへの言及を検出 |
| C30 | **キーワード最適化** | notice | hybrid | script: title/H1/本文から頻出語抽出 → agent: KW配置の自然さを評価 |

---

## カテゴリ3: 内部リンク & リンク品質（重み: 15%）

| # | チェック項目 | 深刻度 | 方式 | 実装方法 |
|---|------------|--------|------|----------|
| L01 | **内部リンク数** | notice | script | `<a href>` のうち同一ドメインのリンク数カウント |
| L02 | **外部リンク数** | notice | script | `<a href>` のうち異なるドメインのリンク数カウント |
| L03 | **リンク過多** | warning | script | ページ内リンク総数。100超=notice、300超=warning |
| L04 | **アンカーテキスト品質** | warning | hybrid | script: 全`<a>`のテキスト抽出 → agent: 「こちら」「詳細」「click here」等の非記述的テキストを判定 |
| L05 | **空アンカーテキスト** | warning | script | `<a>` のテキスト+alt(画像リンク)が空のものを検出 |
| L06 | **nofollow 内部リンク** | warning | script | 内部リンクに `rel="nofollow"` が付いているものを検出 |
| L07 | **壊れた内部リンク候補** | notice | script | リンク先URLの形式チェック（空href, `javascript:void(0)`, `#` のみ等） |
| L08 | **unsafe cross-origin links** | notice | script | `target="_blank"` に `rel="noopener noreferrer"` がないリンクを検出 |
| L09 | **パンくずリスト** | notice | script | `BreadcrumbList` JSON-LD、または `<nav aria-label="breadcrumb">` の有無 |
| L10 | **meta refresh リダイレクト** | error | script | `<meta http-equiv="refresh">` の検出 |

---

## カテゴリ4: UX / 表示速度（重み: 20%）

### 4A. Core Web Vitals（API経由）

| # | チェック項目 | 深刻度 | 方式 | 実装方法 |
|---|------------|--------|------|----------|
| U01 | **LCP（Largest Contentful Paint）** | error | api | PSI API 呼び出し。≤2.5s=Good, ≤4.0s=NI, >4.0s=Poor |
| U02 | **INP（Interaction to Next Paint）** | error | api | PSI API。≤200ms=Good, ≤500ms=NI, >500ms=Poor |
| U03 | **CLS（Cumulative Layout Shift）** | error | api | PSI API。≤0.1=Good, ≤0.25=NI, >0.25=Poor |
| U04 | **FCP（First Contentful Paint）** | warning | api | PSI API。≤1.8s=Good, ≤3.0s=NI, >3.0s=Poor |
| U05 | **TTFB（Time To First Byte）** | warning | script | `curl -w "%{time_starttransfer}"` で計測。0.8s超=warning |
| U06 | **Lighthouse Performance スコア** | notice | api | PSI API から取得。50未満=warning |
| U07 | **Lighthouse SEO スコア** | notice | api | PSI API から取得。参考値として表示 |

### 4B. パフォーマンス最適化

| # | チェック項目 | 深刻度 | 方式 | 実装方法 |
|---|------------|--------|------|----------|
| U08 | **GZIP/Brotli 圧縮** | warning | script | `headers.txt` から `Content-Encoding: gzip` or `br` を確認 |
| U09 | **JS ミニファイ** | notice | script | `<script src>` のURLを取得し、`.min.js` パターン or レスポンスサイズを確認 |
| U10 | **CSS ミニファイ** | notice | script | `<link rel="stylesheet">` のURLで `.min.css` パターン確認 |
| U11 | **JS/CSS キャッシュヘッダー** | warning | script | 主要JS/CSSの `Cache-Control` / `Expires` ヘッダー確認 |
| U12 | **JS/CSS ファイル数** | notice | script | `<script src>` と `<link rel="stylesheet">` の数をカウント。合計20超=notice |
| U13 | **JS/CSS 合計サイズ** | warning | script | 主要ファイルの `Content-Length` 合計。1MB超=warning |
| U14 | **レンダーブロッキングリソース** | warning | script | `<head>` 内の `<script>` に `defer`/`async` がないもの、`<link rel="stylesheet">` の数 |
| U15 | **画像 lazy loading** | notice | script | `<img>` に `loading="lazy"` があるか（ファーストビュー外の画像） |

---

## カテゴリ5: 構造化データ & AI対応（重み: ※後述）

### 5A. 構造化データ

| # | チェック項目 | 深刻度 | 方式 | 実装方法 |
|---|------------|--------|------|----------|
| S01 | **JSON-LD 存在** | warning | script | `<script type="application/ld+json">` の有無 |
| S02 | **JSON-LD 構文妥当性** | error | script | `jq` でパース。構文エラー検出 |
| S03 | **@type 検出** | notice | script | JSON-LD 内の `@type` 値一覧抽出（Article, Organization, BreadcrumbList等） |
| S04 | **必須プロパティ充足** | warning | hybrid | script: JSON-LD抽出 → agent: Schema.orgの必須/推奨プロパティとの照合 |
| S05 | **Organization schema** | notice | script | `@type: Organization` の有無。name, url, logo の存在確認 |
| S06 | **BreadcrumbList schema** | notice | script | `@type: BreadcrumbList` の有無 |
| S07 | **FAQPage schema** | notice | script | `@type: FAQPage` の有無 |
| S08 | **Article schema** | notice | script | `@type: Article` の有無。author, datePublished, dateModified の存在 |

### 5B. AI検索対応（GEO）

| # | チェック項目 | 深刻度 | 方式 | 実装方法 |
|---|------------|--------|------|----------|
| G01 | **llms.txt 存在** | notice | script | `/llms.txt` のHTTPステータスが200か |
| G02 | **llms.txt フォーマット** | notice | script | llms.txt の基本構文チェック（セクション構造の妥当性） |
| G03 | **AIクローラー許可** | warning | script | robots.txt で GPTBot, ClaudeBot, PerplexityBot が Disallow されていないか |
| G04 | **セマンティックHTML使用率** | notice | hybrid | script: `<article>`, `<section>`, `<nav>`, `<aside>`, `<header>`, `<footer>`, `<main>` の使用数カウント → `<div>` 総数との比率 |
| G05 | **Answer-First 構造** | warning | agent | H1直後のテキストブロックを抽出し、直接回答が含まれるか判定 |
| G06 | **Direct Question Headers** | notice | script | H2/H3 を抽出し、疑問文（「?」「〜とは」「How」「What」）のパターンマッチ |
| G07 | **Named Source Attribution** | notice | agent | 本文テキストから「〇〇によると」「〇〇の調査」等の具体的出典パターンを検出 |
| G08 | **FAQ セクション** | notice | hybrid | script: FAQPage schema の有無 + `<h2>`/`<h3>` にFAQパターン → agent: 3問以上あるか |
| G09 | **コンテンツ更新日の明示** | notice | script | `dateModified`(JSON-LD)、`<time datetime>` タグの有無 |
| G10 | **コンテンツ長の適切さ（AI向け）** | notice | hybrid | script: テキスト文字数 → 極端に長い（10000字超）場合にセクション分割されているか確認 |

---

## カテゴリ6: E-E-A-T & 信頼性

| # | チェック項目 | 深刻度 | 方式 | 実装方法 |
|---|------------|--------|------|----------|
| E01 | **会社概要ページへのリンク** | notice | script | ナビゲーション内の `/about`, `/company`, `会社概要` リンクを検出 |
| E02 | **プライバシーポリシーへのリンク** | warning | script | フッター等の `/privacy`, `プライバシーポリシー` リンク検出 |
| E03 | **利用規約へのリンク** | notice | script | `/terms`, `利用規約` リンク検出 |
| E04 | **お問い合わせページへのリンク** | notice | script | `/contact`, `お問い合わせ` リンク検出 |
| E05 | **著者情報（Person schema）** | notice | script | JSON-LD内の `@type: Person` 検出。`name`, `jobTitle` の有無 |
| E06 | **著者バイライン** | notice | hybrid | script: 記事上部の著者名パターン検出 → agent: バイラインとして妥当か判定 |
| E07 | **Organization schema** | notice | script | S05と共有 |
| E08 | **外部リンク（引用・出典）** | notice | script | 外部リンク数カウント。`<cite>` タグ、「出典」「参考」文言の有無 |
| E09 | **Plaintext メールアドレス** | notice | script | HTML内の `mailto:` を含まないメールアドレスパターン検出（スパム対策） |
| E10 | **E-E-A-T総合評価** | — | agent | 上記E01-E09の結果をまとめて、E-E-A-Tの観点から総合評価。改善提案を生成 |

---

## カテゴリ7: ローカルSEO（重み: 10%）

| # | チェック項目 | 深刻度 | 方式 | 実装方法 |
|---|------------|--------|------|----------|
| R01 | **LocalBusiness schema 存在** | notice | script | JSON-LD内の `@type: LocalBusiness`（またはサブタイプ）検出 |
| R02 | **NAP情報の存在** | warning | hybrid | script: 電話番号パターン(`\d{2,4}-\d{2,4}-\d{4}`)、住所パターン検出 → agent: NAP情報として整合しているか |
| R03 | **NAP と構造化データの一致** | warning | hybrid | script: LocalBusiness schema 内の name/address/telephone 抽出 → ページ本文内の表記と照合 |
| R04 | **GeoCoordinates** | notice | script | JSON-LD内の `latitude`, `longitude` の有無 |
| R05 | **営業時間（openingHours）** | notice | script | LocalBusiness schema 内の `openingHoursSpecification` の有無 |
| R06 | **ローカルSEO該当判定** | — | agent | ページ内容からローカルビジネスサイトかどうかを判定。非該当の場合このカテゴリを除外し他カテゴリに重み再配分 |

---

## カテゴリ8: その他

| # | チェック項目 | 深刻度 | 方式 | 実装方法 |
|---|------------|--------|------|----------|
| X01 | **Custom 404ページ** | notice | script | 存在しないURLにアクセスしてカスタム404が返るか確認（HTMLにコンテンツがあるか） |
| X02 | **SPF レコード** | notice | script | `dig TXT <domain>` で `v=spf1` の有無 |
| X03 | **Google Analytics / タグマネージャー** | notice | script | `page.html` 内の `gtag`, `GoogleAnalyticsObject`, `gtm.js` パターン検出 |
| X04 | **JS コンソールエラー** | notice | script | `<script>` 内の明らかな構文エラー検出は困難。PSI API のdiagnostics参照 |

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
seo-audit/
├── scripts/
│   ├── fetch.sh              # データ取得（curl並列実行）
│   ├── analyze-technical.sh   # T01-T30: テクニカルSEO解析
│   ├── analyze-content.sh     # C01-C23: メタ情報・HTML品質解析
│   ├── analyze-links.sh       # L01-L10: リンク解析
│   ├── analyze-performance.sh # U05,U08-U15: パフォーマンス解析
│   ├── analyze-structured.sh  # S01-S08: 構造化データ解析
│   ├── analyze-geo.sh         # G01-G04,G06,G09: GEO技術チェック
│   ├── analyze-eeat.sh        # E01-E05,E07-E09: E-E-A-T技術チェック
│   ├── analyze-local.sh       # R01-R05: ローカルSEO解析
│   ├── analyze-misc.sh        # X01-X04: その他
│   ├── call-psi-api.sh        # U01-U04,U06-U07: PSI API呼び出し
│   └── score.sh               # 全結果集約 → スコア算出
├── agents/
│   ├── content-quality.md     # C26,C27,C29,C30: コンテンツ品質評価
│   ├── geo-readiness.md       # G05,G07,G08,G10: AI検索対応評価
│   ├── eeat-assessment.md     # E06,E10: E-E-A-T総合評価
│   ├── local-seo.md           # R02,R03,R06: ローカルSEO判定
│   ├── link-quality.md        # L04: アンカーテキスト品質評価
│   └── report-generator.md    # 最終レポート生成（改善提案付き）
└── data/
    └── (実行時にfetch.shが生成するデータファイル)
```

### 実行フロー

```
Phase 1: データ取得（並列、5秒タイムアウト）
  scripts/fetch.sh <URL>
  scripts/call-psi-api.sh <URL>  ← 最大ボトルネック(10-20秒)

Phase 2: Script解析（並列、Phase 1完了後）
  scripts/analyze-technical.sh
  scripts/analyze-content.sh
  scripts/analyze-links.sh
  scripts/analyze-performance.sh
  scripts/analyze-structured.sh
  scripts/analyze-geo.sh
  scripts/analyze-eeat.sh
  scripts/analyze-local.sh
  scripts/analyze-misc.sh

Phase 3: Agent解析（並列、Phase 2完了後）
  agents/content-quality.md   ← Phase 2の抽出データを入力
  agents/geo-readiness.md
  agents/eeat-assessment.md
  agents/local-seo.md
  agents/link-quality.md

Phase 4: スコア集計 & レポート生成
  scripts/score.sh            ← 全結果をJSON集約
  agents/report-generator.md  ← スコア+詳細→人間向けレポート
```

### 実装方式の内訳

| 方式 | 項目数 | 割合 |
|------|--------|------|
| **script** のみ | 95項目 | 77% |
| **agent** のみ | 8項目 | 7% |
| **hybrid**（script+agent） | 13項目 | 10% |
| **api** | 7項目 | 6% |
| **合計** | **123項目** | 100% |

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
