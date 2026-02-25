---
name: analyze-epic
description: フィーチャー要件を分析し、全体設計とストーリー分割を行う。配置済みの PLAN.md と plan.json を更新する内容を生成して返す。
model: opus
allowed_tools: Read, Glob, Grep
---

# Analyze Epic Agent

フィーチャー要件を分析し、全体設計とストーリー分割を行う。

## 入力

- ユーザーのフィーチャー要件（テキスト）
- 確定済みの feature-slug
- 配置済みの PLAN.md（`docs/FEATURES/{feature-slug}/PLAN.md` — テンプレート構成が入っている）

## 処理

1. 配置済みの PLAN.md を Read して構成を把握
2. フィーチャー要件を分析し、概要・背景・変更内容・影響範囲を整理
3. フィーチャーをストーリーに分割し、各ストーリーに以下を付与:
   - slug（ハイフンケース、英小文字）
   - title（日本語、20文字以内）
   - description（日本語、100文字以内）
   - executionType（manual / developing / coding）
   - phase（所属フェーズ番号。1から順に）
   - dependencies（依存するストーリーの slug 配列）
4. ストーリーをフェーズにグルーピングする（依存関係に基づく実行順序）
5. PLAN.md のテンプレート構成に従って内容を作成
6. plan.json の内容を作成（phases 配列を含む）

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
  "planMdContent": "# フィーチャー名\n\n## 注意書き\n...(PLAN.md の全文)",
  "planJson": {
    "feature": {
      "slug": "user-auth",
      "title": "ユーザー認証機能",
      "description": "..."
    },
    "stories": [
      {
        "slug": "login-form",
        "title": "ログインフォーム",
        "description": "...",
        "executionType": "developing",
        "phase": 1,
        "dependencies": [],
        "status": "pending"
      },
      {
        "slug": "oauth-setup",
        "title": "OAuthプロバイダー設定",
        "description": "...",
        "executionType": "manual",
        "phase": 1,
        "dependencies": [],
        "status": "pending"
      },
      {
        "slug": "social-login",
        "title": "ソーシャルログイン",
        "description": "...",
        "executionType": "developing",
        "phase": 2,
        "dependencies": ["login-form", "oauth-setup"],
        "status": "pending"
      }
    ],
    "phases": [
      { "number": 1, "name": "基盤構築", "description": "認証基盤とOAuth設定" },
      { "number": 2, "name": "拡張機能", "description": "Phase 1 の完了が前提" }
    ],
    "metadata": {
      "createdAt": "",
      "status": "active"
    }
  }
}
```

注意: `metadata.createdAt` はオーケストレーターが後から設定する（日付取得後）。

## PLAN.md の構成

配置済みの PLAN.md（テンプレート）の構成に従って生成する:

1. **注意書き** — 実装と並行したタスクリスト管理について
2. **概要** — 何を達成するか（1-2文）
3. **背景** — なぜこの変更が必要か
4. **変更内容** — 具体的な変更点のリスト
5. **影響範囲** — 影響を受けるファイル・機能
6. **ストーリー一覧** — executionType・フェーズ・依存関係付きの概要テーブル
7. **実行戦略付きタスクリスト** — フェーズ別・executionType アイコン付きのチェックリスト

## プロンプト

```
フィーチャー要件を分析し、全体設計とストーリー分割を行ってください。

## フィーチャー要件
{feature_requirements}

## 確定済み feature-slug
{feature_slug}

## 配置済み PLAN.md の内容
{placed_plan_md_content}

## ルール

1. PLAN.md は配置済みテンプレートの構成（注意書き、概要、背景、変更内容、影響範囲、ストーリー一覧、実行戦略）に従って生成する
2. 各ストーリーに executionType（manual/developing/coding）と phase（フェーズ番号）を付与する
3. ストーリーの粒度は「1つの dev:story セッションで完結できる」サイズにする
4. 依存関係に基づいてフェーズを分割する。同一フェーズ内のストーリーは並列実行可能
5. 実行戦略付きタスクリストはフェーズ別に構成し、各ストーリーに executionType アイコン（🔧/👤/💻）を付ける
6. feature.slug には確定済みの slug を設定する
7. metadata.createdAt は空文字にしておく（後で設定される）
8. plan.json には stories 配列に加えて phases 配列も含める

## 出力形式

JSON形式で出力してください。
```
