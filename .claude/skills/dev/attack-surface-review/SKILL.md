---
name: dev:attack-surface-review
description: |
  Webサービスを攻撃者目線でレビューし、実在する攻撃ベクターに基づいて脆弱性を発見・整理するスキル。
  このスキル自体は原則「修正実装」ではなく「発見と優先度付け」に集中し、Medium以上の所見がある場合は
  メインセッションでAskUserQuestion（Question Tool）を実行して dev:spec に対策仕様の作成を促す。

  Trigger:
  脆弱性レビュー, セキュリティ診断, 攻撃者目線レビュー, ペネトレーション観点, /dev:attack-surface-review,
  attack surface review, pentest perspective, exploit path
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
  - AskUserQuestion
---

# 攻撃面レビュー（dev:attack-surface-review）

## ゴール

- 攻撃者が実際に取りうる経路を特定し、**再現可能な根拠付き所見**として提示する。
- 無差別なCWE列挙ではなく、**コード経路に紐づく攻撃シナリオ**を示す。
- Medium以上の所見がある場合、**メインセッションの AskUserQuestion で dev:spec に修正仕様作成を誘導**する。

---

## 実行手順

### Step 1: 攻撃対象面の棚卸し

以下を優先順で特定する。

1. 外部公開面（HTTPルート、Webhook、コールバック、管理画面）
2. 認証境界（ログイン・セッション・トークン更新）
3. 認可境界（RBAC/ABAC、所有者チェック、テナント境界）
4. 入力→危険処理の到達（SQL/NoSQL、テンプレート、コマンド実行、ファイルI/O）
5. 秘匿情報取り扱い（APIキー、JWTシークレット、クラウド認証情報）

`rg` とミドルウェア/ルータ定義の読解を先行し、根拠のない推測は書かない。

### Step 2: 既存チェックの活用

リポジトリに既にあるチェックを優先して実行する。

- 依存脆弱性監査（導入済みコマンドがあれば）
- Lint / SAST / 既存のセキュリティテスト
- 認証・認可に関する統合テスト

新規の重量級ツール導入は、ユーザー明示指示がある場合のみ。

### Step 3: 攻撃パス検証

以下の観点を**実際のコード経路で**確認する。

- 認可不備（BOLA/IDOR）
- Injection（SQL/NoSQL/Command/Template）
- SSRF（メタデータ到達・内部ネットワーク到達）
- XSS（Stored/Reflected/DOM）
- CSRF / セッション固定化
- パストラバーサル / 任意ファイル読込
- 署名検証不備（Webhook改ざん・リプレイ）
- CORS / デバッグ機能 / insecure default

各所見は「前提条件」「攻撃ステップ」「影響範囲」を最低限含める。

### Step 4: 所見フォーマット化

報告時は `references/finding-template.md` を読み、同一フォーマットで出力する。

所見がゼロの場合は、次を明記する。

- `確認範囲では再現可能な脆弱性は確認できなかった`
- 未確認範囲・制約（例: 実環境依存、外部連携未接続）

### Step 5: Medium以上の所見を dev:spec にエスカレーション

Medium以上が1件以上ある場合、**その場で修正実装を開始しない**。

1. `Task` で `agents/escalate-to-dev-spec.md` を使い、
   「所見要約 + AskUserQuestion入力案（header/question/options）」を生成する。
2. サブエージェントの結果を受け取り、**メインセッション**で AskUserQuestion を実行する。
3. 回答に応じて dev:spec の実施方針を確定する。

> 注意: AskUserQuestion はサブエージェントで直接実行しない。

---

## 完了条件

- [ ] 全所見にコード根拠と攻撃シナリオがある
- [ ] 所見はテンプレート形式で整形済み
- [ ] Medium以上あり: メインセッションのAskUserQuestionで dev:spec への誘導を実施済み
- [ ] Medium以上なし: 監視/改善バックログ化の提案を記載済み
