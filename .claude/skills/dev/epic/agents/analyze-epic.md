# analyze-epic

## 役割

フィーチャー要件を分析し、全体設計とストーリー分割を行う。
PLAN.md の内容と plan.json の内容を生成して返す。

## 推奨モデル

**opus** - 複雑なフィーチャーの分析・設計判断に必要

## 入力

- ユーザーのフィーチャー要件（テキスト）
- plan-doc テンプレート構成（`.claude/commands/plan-doc.md` の内容）

## 処理

1. フィーチャー要件を分析し、概要・背景・変更内容・影響範囲を整理
2. フィーチャーをストーリーに分割し、各ストーリーに以下を付与:
   - slug（ハイフンケース、英小文字）
   - title（日本語、20文字以内）
   - description（日本語、100文字以内）
   - executionType（manual / developing / coding）
   - priority（1から順に。数字が小さいほど優先度高）
   - dependencies（依存するストーリーの slug 配列）
3. feature-slug の候補を3つ生成
4. plan-doc のテンプレート構成をベースに PLAN.md の内容を作成
5. plan.json の内容を作成

## executionType 判定基準

| executionType | 判定条件 |
|---------------|----------|
| `developing` | ビジネスロジック、UI実装、テスト可能な機能。TDD/E2E/TASK 分類が意味を持つ |
| `manual` | 外部サービスの GUI 操作、ダッシュボード設定、人間の判断が必要 |
| `coding` | 設定ファイル追加、定型的なコード変更、タスク分解するほどでもない小作業 |

## 出力

JSON形式で以下の構造を返す:

```json
{
  "featureSlugCandidates": [
    { "slug": "user-auth", "description": "ユーザー認証機能" },
    { "slug": "authentication", "description": "認証システム" },
    { "slug": "login-system", "description": "ログインシステム" }
  ],
  "planMdContent": "# フィーチャー名\n\n## 注意書き\n...(PLAN.md の全文)",
  "planJson": {
    "feature": {
      "slug": "",
      "title": "ユーザー認証機能",
      "description": "..."
    },
    "stories": [
      {
        "slug": "login-form",
        "title": "ログインフォーム",
        "description": "...",
        "executionType": "developing",
        "priority": 1,
        "dependencies": [],
        "status": "pending"
      }
    ],
    "metadata": {
      "createdAt": "",
      "status": "active"
    }
  }
}
```

注意: `feature.slug` と `metadata.createdAt` はオーケストレーターが後から設定する（slug 確定後・日付取得後）。

## PLAN.md の構成（plan-doc ベース）

plan-doc（`.claude/commands/plan-doc.md`）の構成をそのまま継承し、ストーリー一覧セクションを追加する:

1. **注意書き** — 実装と並行したタスクリスト管理について
2. **概要** — 何を達成するか（1-2文）
3. **背景** — なぜこの変更が必要か
4. **変更内容** — 具体的な変更点のリスト
5. **影響範囲** — 影響を受けるファイル・機能
6. **ストーリー一覧** — executionType・優先度・依存関係付きのテーブル
7. **実行戦略付きタスクリスト** — plan-doc のモデル選択基準・実行方式記法を継承

### ストーリー一覧セクションの形式

```markdown
## ストーリー一覧

| # | ストーリー | executionType | 優先度 | 依存 | 状態 |
|---|-----------|---------------|--------|------|------|
| 1 | ログインフォーム | developing | 1 | - | pending |
| 2 | OAuth設定 | manual | 2 | - | pending |
| 3 | 環境変数追加 | coding | 2 | - | pending |
| 4 | ソーシャルログイン | developing | 3 | 1, 2, 3 | pending |
```

## プロンプト

```
フィーチャー要件を分析し、全体設計とストーリー分割を行ってください。

## フィーチャー要件
{feature_requirements}

## PLAN.md テンプレート構成（plan-doc ベース）
{plan_doc_content}

## ルール

1. PLAN.md は plan-doc の構成（注意書き、概要、背景、変更内容、影響範囲、実行戦略）をそのまま継承し、「ストーリー一覧」セクションを追加する
2. 各ストーリーに executionType（manual/developing/coding）を付与する
3. ストーリーの粒度は「1つの dev:story セッションで完結できる」サイズにする
4. 依存関係は最小限に。並列実行可能なストーリーを増やす
5. feature-slug 候補は3つ生成（ハイフンケース、英小文字）
6. feature.slug と metadata.createdAt は空文字にしておく（後で設定される）

## 出力形式

JSON形式で出力してください。
```
