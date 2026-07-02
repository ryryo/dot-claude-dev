---
name: release-checklist-audit
description: Webサービス公開前チェックリストに沿って、サイトやWebアプリの公開前診断を行い、抜けを実装するための計画を作る。Zennの公開前チェックリスト、セキュリティ、SEO、OGP、アクセシビリティ、パフォーマンス、複数環境、ログイン、メール、バックアップ、決済、エラー検知などの公開前確認を依頼されたときに使う。
---

# release-checklist-audit

Webサービス公開前のチェックリスト診断を行い、必要な実装計画を作るためのスキル。プロジェクトの既存ルール、既存計画、既存テストに合わせて、読みやすく実行可能な計画を作る。

## 基本方針

- まずユーザーの対象範囲と対象外を読む。ユーザーが「ログインは除外」「メールは除外」など指定した場合はそれを優先する。
- 指定がない場合は、このスキルの「完全チェックリスト」を対象にする。
- 診断は推測で完了にしない。コード、設定、ビルド結果、ローカル/本番 runtime の観測で確認する。
- 変更はすぐ実装せず、ユーザーが計画作成を求めている場合は計画作成までに留める。
- 実装計画はシンプルに書く。目的、診断結果、実装タスク、検証方法、対象外、残リスクが分かればよい。
- サブエージェントが使える状況であれば、並列調査にする。security/API、SEO/OGP/a11y、performance/UI、ops/runtime のように独立した read-only 診断へ分割してよい。最終判断と計画への反映は main Codex が行う。

## ワークフロー

### 1. 入力と除外範囲を確定する

- ユーザーが参照記事やチェックリスト URL を示した場合は、その内容を確認する。
- 「完全版」と言われた場合はログイン、メール、バックアップ、決済も含める。
- 「今回は除外」と言われたものは診断表で `対象外` として扱う。
- 高額な本番操作、secret 出力、production 変更は行わない。必要なら確認手順として計画に残す。

### 2. リポジトリを読む

### 3. 実行できる診断を行う

UI変更や表示診断では、可能なら browser で desktop / mobile を確認する。確認する代表ページは、top、list/search、detail、login、admin/settings、404/error。

production-only の確認は、無理に実行せず計画に残す。例: Cloudflare Cache Rules、R2 public access、HSTS、error alert、メール DNS、DB backup。

### 4. 診断表を作る

各項目に次のどれかを付ける:

- `PASS`: コードまたは runtime で確認済み。
- `GAP`: 実装・設定が不足。
- `NEEDS_RUNTIME_CHECK`: code では判断できず本番/環境確認が必要。
- `N/A`: サービス要件上不要、またはユーザーが除外。

GAP には根拠となるファイル、route、設定、観測結果を添える。

### 5. 実装計画を作る

計画ファイルは、プロジェクトに既存方針があればそれに合わせる。指定がなければ `docs/PLAN/{YYMMDD}_release_checklist_remediation.md` のような名前で作る。

## 完全チェックリスト

### セキュリティ

- 認証 Cookie の `HttpOnly`, `Secure`, `SameSite`, `Domain` が適切。
- Cookie の domain 共有範囲と subdomain risk を理解している。
- クライアントだけでなくサーバー側でも validation している。
- URL 入力は `http:` / `https:`、private IP、localhost、link-local、protocol-relative、CR/LF を検証している。
- SSRF risk がある外部取得、browser capture、metadata extraction の直前でも URL policy を確認している。
- 受け取った HTML / Markdown / 外部メタデータを危険に表示していない。
- SQL injection risk がない。raw SQL は bind されている。
- `UPDATE` / `DELETE` に適切な `WHERE` がある。
- user-controlled slug / handle / path segment が予約語や framework reserved path と衝突しない。
- `Strict-Transport-Security` が production HTTPS で付く。
- `Content-Security-Policy` または `frame-ancestors` で clickjacking 対策をしている。
- `X-Content-Type-Options: nosniff` が付く。
- user/session で内容が変わる HTML/API が CDN/KV に誤 cache されない。
- object storage bucket/listing が公開されていない。
- private asset が ID 推測や direct object URL で読めない。
- open redirect がない。
- 未認証/権限なしで作成・更新・削除できない。
- user-derived string を response header にそのまま入れない。
- internal error message、stack、secret、外部 API detail を public response に出さない。
- file upload は content type、magic/header、file size、pixel count、filename/key を検証する。
- cloud account / deploy account の 2FA が有効。
- secrets は source、plan、log、test fixture に出さない。

### ログイン・アカウント

- メールアドレス本人確認が必要な要件なら実装されている。
- IdP 由来 email の verified 状態を確認している。
- login / signup / password reset で登録 email の列挙ができない。
- 複数 login 方法の account linking 仕様が決まっている。
- メールアドレス変更、連携アカウント変更、退会の仕様が決まっている。
- 重要操作では直前 login / re-auth を要求する。
- logout 後に private data が cache/back navigation で見えない。

### メール

- user input がメール本文や件名に入る場合、spam 悪用されない。
- 不特定多数への大量メールが user 操作で連発されない。
- SPF / DKIM / DMARC が設定されている。
- batch / queue が at-least-once でも重複送信しない。
- メルマガ/キャンペーンメールは login なしで購読解除できる。
- 大量送信する場合は List-Unsubscribe / One-Click 要件を確認している。
- bounce / complaint / unsubscribe の運用がある。

### SEO

- 全ページに適切な `title` がある。
- 主要ページに `meta description` がある。
- canonical URL が必要なページにある。
- search / filtered list / query URL の index 方針が決まっている。
- error page は 40x/50x status、または `noindex`。
- サイト全体に誤った `noindex` がない。
- public detail など動的公開ページがある場合、sitemap がある。
- `robots.txt` が sitemap を指し、必要な範囲を block しすぎていない。

### OGP / SNS

- share されるページに `og:title`, `og:description`, `og:url`, `og:image` がある。
- `twitter:card` がある。
- OGP URL は absolute URL。
- OGP image は public に取得でき、適切なサイズ/形式。

### 決済

- 会計処理、売上計上、返金、日割り、領収書の方針が確認済み。
- 決済成功/失敗と app DB の不整合を検知・復旧できる。
- webhook は署名検証し、idempotent。
- 重複決済が起きない。
- subscription 更新失敗、解約、退会、凍結時の挙動が決まっている。
- 支払い情報更新導線がある。
- 適格請求書要件が必要なら満たしている。

### アクセシビリティ

- `<img>` の `alt` が適切。
- 装飾画像は空 `alt` や `aria-hidden`。
- icon-only button/link に accessible name がある。
- form controls に label がある。
- keyboard focus、focus trap、modal close が成立する。
- 色 contrast と focus indicator が最低限確認されている。

### パフォーマンス

- bundle analyzer などで重い JS / 不要 dependency を確認できる。
- static assets が CDN cache される。
- user/session dependent response は cache されない。
- image CLS 対策として width/height/aspect-ratio がある。
- 表示サイズに対して過大画像を読み込まない。
- lazy loading / eager loading が適切。
- 検索・一覧・絞り込みの index が現状データと想定データ量に対して妥当。
- full image viewer や markdown viewer の重い依存は必要な route だけに載る。

### 複数環境・UI

- mobile / tablet / desktop で主要画面が崩れない。
- Chrome / Safari / Firefox で致命的な差がない。
- OS別 font fallback が不自然でない。
- scrollbar always visible でも layout が大きくずれない。
- 長い title / URL / tag / note / email / filename で overflow しない。
- loading / empty / error / not found state がある。

### バックアップ・復旧

- DB の定期 backup が有効。
- object storage の backup / versioning / lifecycle 方針がある。
- migration rollback または復旧手順がある。
- seed / fixture / production data の扱いが分離されている。
- 復旧テストまたは少なくとも復旧手順の dry-run 方針がある。

### 監視・運用

- server error を検知できる。Cloudflare observability、logs、alert、log drain、Sentry 等の方針がある。
- 404/50x page が user に次の行動を示す。
- deploy dry-run / smoke check がある。
- rate limit / abuse 対策が必要な公開 API にある。
- analytics は必要なら入っている。不要なら理由がある。

### その他

- localStorage や http-only でない Cookie が消えても致命的に壊れない。
- third-party Cookie に依存しない。
- 日本語サイトなら `<html lang="ja">`。
- favicon がある。
- apple-touch-icon がある。
- PWA manifest が必要ならある。
- サービス名が他言語で問題ないか確認している。
- 法務/規約/プライバシーポリシー/特商法/電気通信事業者届出など、サービス要件に応じた確認がある。

## 計画タスク化の目安

優先順:

1. 外部入力と authz: redirect、SSRF、upload limit、権限、error leak。
2. response / runtime headers: HSTS、CSP、nosniff、cache policy。
3. public discovery: SEO、OGP、robots、sitemap、favicon。
4. user-facing failure: 404/50x、empty/error state。
5. performance and multi-env: bundle、image、responsive、font、overflow。
6. operations: backup、monitoring、email DNS、payment webhook、production-only checks。

タスクごとに書くこと:

- 目的
- 読むファイル
- 書くファイル
- 受入基準
- 検証コマンド
- 並列化できるか
- production-only か

## 完了報告

完了時は次を短く報告する:

- 作成した計画ファイル path。
- 診断で見つかった主要 GAP。
- 実行した検証。
- production-only として残した確認。
- サブエージェントを使った場合は、担当領域と採用した結果。
