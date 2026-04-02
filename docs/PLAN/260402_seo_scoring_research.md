# SEO診断ツール スコアリングシステム リサーチレポート

> **目的**: SEGO と同等のSEO診断・スコアリング機能を開発するための調査資料
> **作成日**: 2026-04-02
> **ステータス**: リサーチ完了 → 仕様書作成待ち

---

## 1. テクニカルSEO評価項目

### 1.1 クローラビリティ（重要度: 最高）

| 項目 | 測定方法 | スコア化 |
|------|----------|----------|
| **robots.txt** | ファイル存在、構文検証、重要ページのDisallow有無 | 未設置=警告、重要ページ遮断=致命的 |
| **XML Sitemap** | 存在、robots.txtでの参照、URL数・lastmodの妥当性 | 未設置=中度エラー、記載URLが4xx=高度エラー |
| **canonical** | `<link rel="canonical">` の存在・整合性 | 未設定=中度警告、矛盾=高度エラー |
| **hreflang** | 双方向参照の整合性、x-defaultの設定 | 片方向のみ=エラー |
| **リダイレクト** | 301/302の適切使用、チェーン（3段以上=警告）、ループ | Pass/Warn/Fail |
| **クロール深度** | トップからの最小クリック数（3以内が理想） | 深度別数値スコア |

### 1.2 インデクサビリティ（重要度: 最高）

| 項目 | 測定方法 | スコア化 |
|------|----------|----------|
| **meta robots** | noindex/nofollow 検出、意図的か誤設定かの判定 | 重要ページにnoindex=致命的 |
| **X-Robots-Tag** | HTTPレスポンスヘッダー検査 | meta robotsと同等 |
| **HTTPステータス** | 200/301/302/404/410/500の分布 | 4xx/5xx多い=減点 |
| **重複コンテンツ** | URL正規化、パラメータ違い、コンテンツ類似度 | 重複比率で減点 |
| **薄いコンテンツ** | テキスト量（200語未満=警告）、HTML対テキスト比率 | 該当ページ割合で減点 |

### 1.3 Core Web Vitals（重要度: 最高）

Google公式ランキングシグナル。75パーセンタイル値で判定。

| 指標 | Good | Needs Improvement | Poor |
|------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | ≤2.5s | ≤4.0s | >4.0s |
| **INP** (Interaction to Next Paint) | ≤200ms | ≤500ms | >500ms |
| **CLS** (Cumulative Layout Shift) | ≤0.1 | ≤0.25 | >0.25 |

※ FIDは2024年3月にINPに正式置換

### 1.4 モバイル対応（重要度: 高）

| 項目 | 基準 |
|------|------|
| viewport メタタグ | `width=device-width, initial-scale=1` 必須 |
| レスポンシブ | 水平スクロール発生=高度エラー |
| タップターゲット | 48x48px以上、間隔8px以上 |
| フォントサイズ | 16px未満のテキストが40%超=警告 |
| モバイルファーストインデックス | モバイル版のコンテンツ欠落=高度エラー |

### 1.5 セキュリティ（重要度: 高）

| 項目 | 基準 |
|------|------|
| **HTTPS** | HTTP のみ=致命的エラー（Googleランキングシグナル） |
| **HSTS** | `Strict-Transport-Security` ヘッダー推奨（max-age≥31536000） |
| **Mixed Content** | HTTPS上のHTTPリソース=高度エラー |
| **セキュリティヘッダー** | CSP, X-Content-Type-Options等（SEO直接影響低、信頼性に寄与） |

### 1.6 HTML品質（重要度: 高）

| 項目 | 推奨値 |
|------|--------|
| title タグ | 30〜60文字、KW含有、重複なし |
| meta description | 70〜160文字、重複なし |
| H1 タグ | 1ページ1つ、空でない |
| 見出し階層 | H1→H2→H3の論理的順序 |
| 画像 alt | 全`<img>`に設定 |
| lang 属性 | `<html lang="ja">` 等 |
| Open Graph | og:title, og:description, og:image |

### 1.7 構造化データ（重要度: 中〜高）

| 項目 | 対応Schemaタイプ |
|------|------------------|
| JSON-LDの存在・構文妥当性 | Article, Product, FAQ, BreadcrumbList |
| 必須プロパティ充足率 | Organization, LocalBusiness, WebSite |
| リッチリザルト適格性 | HowTo, Recipe, Event, VideoObject |

---

## 2. コンテンツ品質評価

### 2.1 キーワード最適化

| 要素 | チェック内容 | 推奨 |
|------|-------------|------|
| title | ターゲットKW含有、先頭寄り | 30〜60文字 |
| H1 | KW含有、1ページ1つ | 必須 |
| 本文KW密度 | 過剰でないか | 1〜3%目安（自然さ優先） |
| URL | KW含有 | スラッグにKW |
| 共起語カバレッジ | 競合上位ページとの比較 | TF-IDFベース |

### 2.2 アンサーファースト構造

**定義**: ユーザーの検索意図に対する直接回答をページ冒頭に配置する構造

**評価方法**:
- H1直後200文字以内に明確な回答文が存在するか
- 定義・回答パターンの検出（「〜とは」「〜です」）
- Featured Snippet適格構造（定義型: 40〜60語の`<p>`、リスト型: `<ol>`/`<ul>`、表型: `<table>`）

**Web検索で確認**: 2026年時点でも「最初の200語で直接回答する」ことがAI検索エンジンでの引用率に大きく影響

### 2.3 可読性スコア（日本語対応）

- **文の平均長**: 40〜60文字が読みやすい（80文字超=要改善）
- **漢字含有率**: 20〜30%が適正（40%超=難読傾向）
- **段落あたりの文数**: 3〜5文推奨
- **実装**: 形態素解析（MeCab / kuromoji）で品詞分解して算出

### 2.4 コンテンツ鮮度

- `dateModified`構造化データ、`Last-Modified`ヘッダーから検出
- YMYL領域: 6ヶ月以上未更新=減点
- 一般コンテンツ: 12ヶ月が目安
- 古い年号の言及（「2022年最新」等）を検出

### 2.5 メディア活用

- WebP/AVIF形式、適切なサイズ、alt属性、lazy loading
- 動画: VideoObject構造化データ
- 図表: `<figure>` + `<figcaption>` の使用

---

## 3. AI検索エンジン対応（GEO: Generative Engine Optimization）

### 3.1 GEOの概要

GEOは生成AI検索エンジン（ChatGPT, Google AI Overview, Perplexity, Claude）での可視性を最適化する手法。2024年のGeorgia Techの研究論文が起点。

**従来SEOとの違い**:
- ランキング・クリック → メンション・引用率にフォーカス
- 情報密度がより重要
- 構造化データ（FAQ, HowTo, Speakable）への依存度が高い
- マルチソースのブランド裏付けが必要

### 3.2 GEO最適化の具体的手法

| 手法 | 効果 |
|------|------|
| **引用の追加**: 信頼できる情報源への参照を本文に含める | 引用確率向上 |
| **統計データの追加**: 具体的数値を含める | 約40%の改善効果（研究結果） |
| **専門用語の適切使用**: ドメイン固有用語を自然に使用 | 専門性シグナル |
| **流暢で権威ある文体**: 簡潔かつ断定的 | 引用されやすさ向上 |
| **最初の200語**: 主要クエリに直接完全に回答 | AI検索での採用率に直結 |

### 3.3 GEO対応の技術的チェック項目

- robots.txt で GPTBot, ClaudeBot, PerplexityBot をブロックしていないか
- Schema.org マークアップ（Article, FAQ, HowTo, Speakable）
- 「Last updated」タイムスタンプの明示
- 構造化されたQ&A形式のコンテンツ

### 3.4 GEO測定KPI

- **Mention Rate**: AI回答でブランドが言及される割合
- **Citation Rate**: クリック可能なURLが含まれる割合
- **Position**: 回答内でのブランドの出現位置

---

## 4. ローカルSEO評価

### 4.1 Google Business Profile最適化

| 項目 | チェック内容 |
|------|-------------|
| ビジネス名 | 正式名称と一致、KW詰め込みなし |
| カテゴリ | プライマリ＋セカンダリ設定 |
| 営業時間 | 正確で最新 |
| 写真 | 外観・内観・商品写真 |

### 4.2 NAP一貫性

- **NAP**: Name, Address, Phone の3要素
- サイト内全ページ、GBP、外部ディレクトリ間で完全一致が必要
- 表記揺れ検出（「株式会社」vs「(株)」等）
- `LocalBusiness`構造化データ内のNAP値との一致確認

### 4.3 ローカル構造化データ

必須プロパティ: name, address, telephone, openingHours, geo (GeoCoordinates)

### 4.4 サイテーション

- 業種別ディレクトリでの掲載状況
- 量より質と一貫性
- BrightLocal, Moz Local等が監査ツールとして利用される

---

## 5. E-E-A-T評価

### 5.1 自動チェック可能な項目

| チェック項目 | 検出方法 |
|-------------|----------|
| 会社概要ページ | `/about`, `/company` パス検出 |
| プライバシーポリシー | `/privacy`, `/privacy-policy` パス検出 |
| 利用規約 | `/terms`, `/tos` パス検出 |
| お問い合わせページ | `/contact` パス検出、フォーム存在 |
| HTTPS | SSL証明書有効性 |
| 著者情報 | Person schema、著者バイライン検出 |
| 運営者情報 | Organization schema |
| 引用・出典 | 外部リンク数、`<cite>`タグ |
| 最終更新日 | 公開日・更新日の表示 |

### 5.2 220+マーカーのE-E-A-T監査

Ahrefsの研究によると220以上のマーカーが存在。自動化可能な技術的チェック23項目が特定されている:
- 壊れたリンク/リダイレクト → 信頼性問題
- 欠落/重複のtitle/description → 品質認知の問題
- 薄いコンテンツ → 専門性の問題

### 5.3 スコアリング方法

各シグナルを0〜2（missing/partial/strong）で評価し、重みを乗算。YMYL判定でより厳格な基準を適用。

---

## 6. 既存ツールのスコアリングアルゴリズム

### 6.1 Google Lighthouse SEO

- **方式**: バイナリ（合格/不合格）× 均等重み
- **計算**: 合格数 / 全audit数 × 100
- **特徴**: 各項目weight=1で均等配分、約14項目、1項目不合格≒8点減
- **参考**: `lighthouse-core/audits/seo/` のソースコード

### 6.2 Ahrefs Health Score

- **方式**: エラーなしURL / 総クロールURL × 100
- **3段階**: Error（重大）> Warning（注意）> Notice（参考）
- **特徴**: Errorのみがスコアに影響。170+チェック項目
- **良好基準**: 80以上=Good、90以上=Excellent

### 6.3 Semrush Site Health

- **方式**: 100点からErrors/Warnings/Noticesの重み付け減点
- **特徴**: 130+チェック項目、問題の種類の多様性もスコアに影響
- **AI Search Health**: 2026年に新設されたAI検索対応の監査カテゴリ

### 6.4 Moz DA/PA

- **方式**: 被リンク量・質の機械学習モデル → 対数スケール1-100
- **特徴**: 外部リンク指標であり技術的SEOは反映しない

### 6.5 業界平均

- 数千サイトの分析で平均SEOスコアは約47/100
- **80+で上位8%**に入る
- 競争の激しい分野（fintech、health）では80+必要

---

## 7. スコアリング設計（SEGO対応）

### 7.1 推奨方式: ハイブリッド

**カテゴリ内**: 項目特性に応じて減点/加点
**カテゴリ間**: 加重平均
**致命的問題**: クリティカル係数でスコア上限を制限

### 7.2 カテゴリ別重み付け（デフォルト）

| カテゴリ | 重み | 根拠 |
|----------|------|------|
| テクニカルSEO | **30%** | クロール・インデックスはSEOの土台 |
| コンテンツ品質 | **25%** | E-E-A-T重視傾向、コアアルゴリズムへの直接影響 |
| UX / 表示速度 | **20%** | Core Web Vitalsがランキング要因 |
| 内部リンク | **15%** | クロールバジェット効率とリンクジュース分配 |
| ローカル / サイテーション | **10%** | 全サイトに該当しないため基本重みは低め |

### 7.3 総合スコア算出式

```
総合スコア = Σ(カテゴリスコア × カテゴリ重み) × クリティカル係数

クリティカル係数:
  - 致命的問題なし: 1.0
  - HTTPS未対応: 0.5
  - 全体noindex: 0.3
  - サーバーダウン: 0.0（診断不可）
```

### 7.4 ランク閾値

| ランク | スコア | 意味 |
|--------|--------|------|
| **A** | 90-100 | 優秀。大きな改善不要 |
| **B** | 70-89 | 良好。軽微な改善余地 |
| **C** | 50-69 | 平均的。改善推奨 |
| **D** | 30-49 | 要改善。重大な問題あり |
| **F** | 0-29 | 致命的。即時対応必要 |

※ SEGOの既存ランク（C=55点）はこの閾値設計と整合する

### 7.5 業種別プロファイル

デフォルト重みに対するオーバーライド:

| 業種 | テクニカル | コンテンツ | UX | 内部リンク | ローカル |
|------|-----------|-----------|-----|-----------|---------|
| メディア/ブログ | 25% | **35%** | 15% | **20%** | 5% |
| EC | **30%** | 20% | **25%** | 15% | 10% |
| コーポレート | 25% | 20% | 20% | 10% | **25%** |
| LP | 20% | 25% | **30%** | 5% | 20% |

### 7.6 致命的問題 vs 改善推奨

| レベル | 例 | 影響 |
|--------|-----|------|
| **Critical** | HTTPS未対応、全体noindex、サーバーエラー | クリティカル係数でスコア上限 |
| **Error** | H1未設定、title未設定、404エラー多数 | カテゴリ内で大幅減点 |
| **Warning** | description未設定、リダイレクトチェーン | カテゴリ内で中度減点 |
| **Notice** | OGP未設定、見出し階層スキップ | カテゴリ内で軽微減点 |

---

## 8. 技術的実装アプローチ

### 8.1 URLからの情報取得

```
HTTP Response → ステータスコード、レスポンスタイム、リダイレクトチェーン
HTTP Headers → Content-Type, Cache-Control, X-Robots-Tag, HSTS, CSP
HTML Parse   → title, meta, canonical, hreflang, H1-H6, img alt,
                a href, JSON-LD, viewport, lang, OGP
DNS Lookup   → A/AAAA, CNAME(CDN判定), TXT(SPF/DMARC), CAA
```

### 8.2 外部API

| API | 用途 | 制限 |
|-----|------|------|
| **PageSpeed Insights API** | Lighthouse + CrUX | 無料、25,000 req/day |
| **CrUX API** | フィールドCWVデータ | 無料 |

### 8.3 30秒以内完了のアーキテクチャ

```
Phase 1（並列、即座開始）:
  ├─ HTML取得 + パース
  ├─ robots.txt取得
  ├─ sitemap.xml取得
  ├─ DNSルックアップ
  └─ PSI API呼び出し（最大ボトルネック: 10-20秒）

Phase 2（Phase 1完了後、並列）:
  ├─ HTML解析（タイトル、メタ、リンク等）
  ├─ ヘッダー解析
  ├─ robots.txt パース
  └─ sitemap.xml パース

Phase 3（集約）:
  └─ スコア算出 + レポート生成
```

**ボトルネック対策**:
- PSI APIが最大のボトルネック → 他解析と完全並列化
- PSI タイムアウト時はHTMLベース結果のみでスコア算出
- 内部リンク解析は対象ページ単体のみ（全体クロール不可）
- HTTPリクエスト: 5秒タイムアウト
- キャッシュ: 同一ドメイン再診断用、TTL 1時間

### 8.4 参考OSSツール

| ツール | 用途 | 特徴 |
|--------|------|------|
| **Lighthouse** | SEO audit実装参考 | `lighthouse-core/audits/seo/` が参考 |
| **SEOnaut** | OSS SEO監査 | Go製、severity別レポート |
| **Yellow Lab Tools** | フロントエンド品質 | カテゴリ別→総合スコア集約 |
| **Sitespeed.io** | パフォーマンス | Coach のスコアリング設計が参考 |
| **seo-audits-toolkit** | SEO+セキュリティ | Lighthouse + Security Headers |

---

## 9. 情報源

### Web検索（2026年4月時点）

- [Lighthouse Performance Scoring](https://developer.chrome.com/docs/lighthouse/performance/performance-scoring)
- [Lighthouse Scoring Docs (GitHub)](https://github.com/GoogleChrome/lighthouse/blob/main/docs/scoring.md)
- [Ahrefs Health Score FAQ](https://help.ahrefs.com/en/articles/1424673-what-is-health-score-and-how-is-it-calculated-in-ahrefs-site-audit)
- [Semrush Site Health Score](https://www.semrush.com/kb/114-total-score)
- [SEO Grade Guide 2026](https://seojuice.com/blog/seo-grade-guide/)
- [GEO Best Practices 2026 (First Page Sage)](https://firstpagesage.com/seo-blog/generative-engine-optimization-best-practices/)
- [GEO Full Guide (Search Engine Land)](https://searchengineland.com/mastering-generative-engine-optimization-in-2026-full-guide-469142)
- [GEO Research Paper (arXiv)](https://arxiv.org/pdf/2311.09735)
- [E-E-A-T Audit: 220+ Markers (Ahrefs)](https://ahrefs.com/blog/eeat-audit/)
- [E-E-A-T Checklist (Backlinko)](https://backlinko.com/eeat-checklist)
- [NAP Audits for Local SEO](https://daltonluka.com/blog/nap-audits)
- [BrightLocal Citation Tracker](https://www.brightlocal.com/local-seo-tools/auditing/citation-tracker/)
- [SEOnaut (GitHub)](https://github.com/StJudeWasHere/seonaut)
- [seo-audits-toolkit (GitHub)](https://github.com/StanGirard/seo-audits-toolkit)
- [Proactive SEO Audit Framework 2026](https://predictadigital.com.au/blog/the-proactive-seo-audit-framework-for-2026-diagnose-predict-win/)
- [Semrush AI Search Health](https://www.semrush.com/kb/1601-ai-search-health-audit)
