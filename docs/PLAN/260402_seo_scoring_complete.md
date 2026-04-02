# SEO診断スキル 完全チェックリスト & 実装設計

> **目的**: ローカル動作のSEO診断スキルで使用する全チェック項目と実装方式の定義
> **作成日**: 2026-04-02
> **前提**: ローカル実行。コードベースを直接Read/Grep/Globで解析するのが基本。
> **参照ツール**: Semrush(140+), Ahrefs(170+), Lighthouse(8), SEO Site Checkup(70+), Seobility(200+)

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
| **Layer 1: code** | コード解析 | `Read`, `Glob`, `Grep` でソースコードを直読み | 常に実行 |
| **Layer 2: live** | ライブチェック | `curl` でHTTPヘッダー・SSL・リダイレクト等を取得 | 本番URL提供時のみ |
| **Layer 3: api** | 外部API | PageSpeed Insights API でCWV等を取得 | 本番URL提供時のみ |

**Code-only モード時**: Layer 2/3 の項目はスキップし、Layer 1 の結果のみでスコア算出。スキップ項目は「未検査」と表示し、該当カテゴリの重みを Layer 1 項目で按分。

## 実装方式の定義

| 方式 | 配置 | 用途 | 例 |
|------|------|------|-----|
| **code** | Read/Grep/Glob | ソースコード直読みで判定 | HTMLタグ有無、構造化データ、リンク構成 |
| **script** | `scripts/` | bash/jq/grep で確定的ルール判定 | robots.txt解析、文字数カウント、パターンマッチ |
| **agent** | `agents/` | LLMの判断が必要 | コンテンツ品質、可読性、E-E-A-T評価 |
| **hybrid** | code/script + agent | 抽出→判定 | アンカーテキスト品質、アンサーファースト |
| **live** | `curl` | HTTPレスポンスが必要 | ヘッダー、SSL、リダイレクト、TTFB |
| **api** | PSI API | 外部API呼び出し | CWV（LCP, INP, CLS, FCP） |

### データ取得フロー

```
■ 常に実行（Layer 1: code）
  Read/Glob/Grep でプロジェクト内のHTML/設定ファイルを直読み
  ├─ HTMLファイル群 → メタタグ、構造化データ、リンク、画像等
  ├─ robots.txt    → クローラビリティチェック
  ├─ sitemap.xml   → サイトマップ検証
  └─ llms.txt      → AI検索対応

■ 本番URL提供時のみ（Layer 2: live）
  scripts/fetch-live.sh <URL>
  ├─ curl -sIL → headers.txt（レスポンスヘッダー + リダイレクトチェーン）
  ├─ curl -vI 2>&1 → ssl-info.txt（SSL証明書情報）
  ├─ curl -w "%{time_starttransfer}" → ttfb.txt
  ├─ curl --http2 -sI → http2-check.txt
  └─ curl -s http://<domain> -o /dev/null -w "%{redirect_url}" → redirect-check.txt
  （並列実行、5秒タイムアウト）

■ 本番URL提供時のみ（Layer 3: api）
  scripts/call-psi-api.sh <URL>
  └─ PageSpeed Insights API → CWV, Lighthouseスコア
```

---

## カテゴリ1: テクニカルSEO（重み: 30%）

### 1A. クローラビリティ & インデクサビリティ

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| T01 | **robots.txt 存在** | warning | code | Glob | プロジェクトルートに `robots.txt` が存在するか |
| T02 | **robots.txt 構文エラー** | error | code | script | `Read` で読み込み → `User-agent`, `Disallow`, `Allow` の構文パース |
| T03 | **robots.txt で重要ページ遮断** | critical | code | script | `Disallow: /` の有無。主要パスがDisallowに該当するか判定 |
| T04 | **robots.txt にSitemap指定** | warning | code | Grep | `Sitemap:` ディレクティブの有無 |
| T05 | **AIクローラーのブロック** | warning | code | Grep | `GPTBot`, `ClaudeBot`, `PerplexityBot` が Disallow されているか |
| T06 | **sitemap.xml 存在** | warning | code | Glob | プロジェクトルートに `sitemap.xml` が存在するか |
| T07 | **sitemap.xml 構文** | error | code | script | `Read` → XMLとして整形式か検証 |
| T08 | **meta robots** | error | code | Grep | HTML内の `<meta name="robots" content="noindex">` を検出 |
| T09 | **X-Robots-Tag** | error | live | curl | `headers.txt` から `X-Robots-Tag: noindex` を検出 |
| T10 | **canonical タグ存在** | warning | code | Grep | `<link rel="canonical" href="...">` の有無 |
| T11 | **canonical URL妥当性** | error | code | script | canonical href が相対パス・空でないか、URL形式が正しいか |
| T12 | **hreflang 存在** | notice | code | Grep | `<link rel="alternate" hreflang="...">` の検出 |
| T13 | **hreflang 言語コード妥当性** | error | code | script | ISO 639-1 コードとの照合 |
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
| C01 | **title タグ存在** | error | code | Grep | `<title>` タグの有無。空の場合も error |
| C02 | **title 長さ** | warning | code | script | テキスト抽出→文字数カウント。30未満 or 60超 = warning |
| C03 | **meta description 存在** | warning | code | Grep | `<meta name="description">` の有無 |
| C04 | **meta description 長さ** | warning | code | script | content属性の文字数。70未満 or 160超 = warning |
| C05 | **H1 タグ存在** | error | code | Grep | `<h1>` の有無 |
| C06 | **H1 が1つだけか** | notice | code | Grep | `<h1>` の出現回数カウント。2以上=notice |
| C07 | **H1 と title の重複** | warning | code | script | H1テキストとtitleテキストの完全一致チェック |
| C08 | **見出し階層の論理性** | warning | code | script | H1→H2→H3 の順序チェック。スキップ（H1→H3等）を検出 |
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
| L01 | **内部リンク数** | notice | code | Grep | `<a href>` のうち同一ドメイン/相対パスのリンク数カウント |
| L02 | **外部リンク数** | notice | code | Grep | `<a href>` のうち外部ドメインのリンク数カウント |
| L03 | **リンク過多** | warning | code | script | ページ内リンク総数。100超=notice、300超=warning |
| L04 | **アンカーテキスト品質** | warning | code | hybrid | Grep: 全`<a>`のテキスト抽出 → agent: 「こちら」「click here」等を判定 |
| L05 | **空アンカーテキスト** | warning | code | Grep | `<a>` のテキスト+alt(画像リンク)が空のものを検出 |
| L06 | **nofollow 内部リンク** | warning | code | Grep | 内部リンクに `rel="nofollow"` が付いているものを検出 |
| L07 | **壊れた内部リンク候補** | notice | code | Grep | 空href, `javascript:void(0)`, `#` のみのリンクを検出 |
| L08 | **unsafe cross-origin links** | notice | code | Grep | `target="_blank"` に `rel="noopener noreferrer"` がないリンク |
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
| S01 | **JSON-LD 存在** | warning | code | Grep | `<script type="application/ld+json">` の有無 |
| S02 | **JSON-LD 構文妥当性** | error | code | script | JSON-LDブロックを抽出 → `jq` でパース。構文エラー検出 |
| S03 | **@type 検出** | notice | code | script | JSON-LD 内の `@type` 値一覧抽出 |
| S04 | **必須プロパティ充足** | warning | code | hybrid | Grep: JSON-LD抽出 → agent: Schema.org必須/推奨プロパティとの照合 |
| S05 | **Organization schema** | notice | code | Grep | `@type.*Organization` の有無。name, url, logo の存在 |
| S06 | **BreadcrumbList schema** | notice | code | Grep | `@type.*BreadcrumbList` の有無 |
| S07 | **FAQPage schema** | notice | code | Grep | `@type.*FAQPage` の有無 |
| S08 | **Article schema** | notice | code | Grep | `@type.*Article` の有無。author, datePublished の存在 |

### 5B. AI検索対応（GEO）

| # | チェック項目 | 深刻度 | Layer | 方式 | 実装方法 |
|---|------------|--------|-------|------|----------|
| G01 | **llms.txt 存在** | notice | code | Glob | プロジェクトルートに `llms.txt` が存在するか |
| G02 | **llms.txt フォーマット** | notice | code | script | Read → セクション構造の妥当性チェック |
| G03 | **AIクローラー許可** | warning | code | Grep | robots.txt でGPTBot等がDisallowされていないか（=T05と共有） |
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
seo-audit/
├── scripts/                        # Layer 2/3（live/api）用
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

**Layer 1（code）の解析はスキル本体（SKILL.md）のプロンプト内でRead/Grep/Globを直接実行。**
専用のスクリプトファイルは不要 — Claude Codeのツールで直接処理する。

### 実行フロー

```
Phase 0: モード決定
  AskUserQuestion → 本番URLの有無確認
  ├─ URL入力 → Full モード
  └─ なし    → Code-only モード

Phase 1: コード解析（Layer 1: code）— 常に実行
  Glob: HTMLファイル、robots.txt、sitemap.xml、llms.txt の特定
  Read: 主要ファイルの読み込み
  Grep: ~75項目のパターンマッチ検査
  （Claude Codeの標準ツールで直接実行、並列可能）

Phase 2: ライブチェック（Layer 2: live）— 本番URL時のみ
  scripts/fetch-live.sh <URL>
  ├─ SSL証明書、HTTPヘッダー、リダイレクト、TTFB等
  └─ 並列実行、5秒タイムアウト

Phase 3: API（Layer 3: api）— 本番URL時のみ
  scripts/call-psi-api.sh <URL>
  └─ CWV（LCP, INP, CLS, FCP）+ Lighthouseスコア

Phase 4: Agent解析 — Phase 1(+2)の結果を入力
  agents/content-quality.md
  agents/geo-readiness.md
  agents/eeat-assessment.md
  agents/local-seo.md
  agents/link-quality.md
  agents/structured-data-review.md
  （並列実行可能）

Phase 5: スコア集計 & レポート生成
  scripts/score.sh            ← 全結果をJSON集約
  agents/report-generator.md  ← スコア+詳細→人間向けレポート
```

### Layer別の内訳

| Layer | 項目数 | 割合 | 実行条件 |
|-------|--------|------|----------|
| **code**（コード直読み） | ~100項目 | ~81% | 常に実行 |
| **live**（curl） | ~16項目 | ~13% | 本番URL提供時のみ |
| **api**（PSI API） | ~7項目 | ~6% | 本番URL提供時のみ |

**Code-onlyモードでも全体の81%の項目を検査可能。**

### 実装方式の内訳

| 方式 | 項目数 | 説明 |
|------|--------|------|
| **Read/Grep/Glob** のみ | ~75項目 | ソースコード直読みで完結 |
| **script**（bash/jq等） | ~20項目 | パース・計算が必要 |
| **agent**（LLMプロンプト） | ~8項目 | 意味理解が必要 |
| **hybrid**（code+agent） | ~13項目 | 抽出→判定の2段階 |
| **live**（curl） | ~16項目 | HTTPレスポンス必要 |
| **api**（PSI API） | ~7項目 | 外部API |

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
