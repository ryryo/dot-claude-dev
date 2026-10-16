---
name: release-checklist-audit
description: "Webサービスの公開前チェックリスト診断と、不足を埋める実装計画を作る。公開準備の総合確認や指定項目の診断に使う。"
---

# release-checklist-audit

Webサービス公開前のチェックリスト診断を行い、必要な実装計画を作るためのスキル。プロジェクトの既存ルール、既存計画、既存テストに合わせて、読みやすく実行可能な計画を作る。

## 基本方針

- まずユーザーの対象範囲と対象外を読む。ユーザーが「ログインは除外」「メールは除外」など指定した場合はそれを優先する。
- 指定がない場合は、[公開前チェックリスト](references/checklist.md)の全カテゴリを対象にする。
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

適用される指示と既存差分を確認し、診断対象のroute、設定、実装、既存テスト・計画を読む。診断だけの依頼でStoryや別の開発Gateを追加しない。

### 3. 実行できる診断を行う

UI変更や表示診断では、可能なら browser で desktop / mobile を確認する。対象範囲に実在する代表ページをtop、list/search、detail、login、admin/settings、404/errorから選ぶ。除外された機能や存在しない画面を追加対象にしない。

production-only の項目も、既存権限で可能な読み取り専用確認は進める。権限や環境がなく確認できないものを計画に残す。例: Cloudflare Cache Rules、R2 public access、HSTS、error alert、メール DNS、DB backup。

### 4. 診断表を作る

各項目に次のどれかを付ける:

- `PASS`: コードまたは runtime で確認済み。
- `GAP`: 実装・設定が不足。
- `NEEDS_RUNTIME_CHECK`: code では判断できず本番/環境確認が必要。
- `N/A`: サービス要件上不要、またはユーザーが除外。

GAP には根拠となるファイル、route、設定、観測結果を添える。

### 5. 実装計画を作る

計画ファイルは、プロジェクトに既存方針があればそれに合わせる。指定がなければ `docs/PLAN/{YYMMDD}_release_checklist_remediation.md` のような名前で作る。

## チェックリストの選択

[公開前チェックリスト](references/checklist.md)から依頼範囲の節を読む。全体診断では全カテゴリの適用性を確認し、機能や要件が存在しない項目は理由付きでN/Aにする。項目を満たすためだけに新機能を追加しない。

カテゴリは、セキュリティ、ログイン・アカウント、メール、SEO、OGP／SNS、決済、アクセシビリティ、パフォーマンス、複数環境・UI、バックアップ・復旧、監視・運用、その他。ログインや決済を除外された依頼では、その詳細を読まない。

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
