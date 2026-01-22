# analyze-story

## 役割

ユーザーストーリーを分析し、目的・スコープ・受入条件を抽出する。
slug候補も生成する。

## 推奨モデル

**opus** - 複雑なストーリーの理解と分析に必要

## 入力

- ユーザーストーリー（会話またはUSER_STORIES.md）

## 出力

`story-analysis.json`:

```json
{
  "story": {
    "title": "ログインフォームを作成する",
    "description": "ユーザーがメールアドレスとパスワードでログインできるようにする"
  },
  "goal": "ユーザー認証機能の提供",
  "scope": {
    "included": [
      "メールアドレス入力フィールド",
      "パスワード入力フィールド",
      "ログインボタン",
      "バリデーション",
      "エラーメッセージ表示"
    ],
    "excluded": [
      "パスワードリセット",
      "ソーシャルログイン",
      "二要素認証"
    ]
  },
  "acceptanceCriteria": [
    "有効なメールアドレス形式のみ受け付ける",
    "パスワードは8文字以上",
    "ログイン成功時はダッシュボードにリダイレクト",
    "ログイン失敗時はエラーメッセージを表示"
  ],
  "slugCandidates": {
    "feature": [
      { "slug": "user-auth", "description": "ユーザー認証機能" },
      { "slug": "authentication", "description": "認証システム" },
      { "slug": "login", "description": "ログイン機能" }
    ],
    "story": [
      { "slug": "login-form", "description": "ログインフォーム実装" },
      { "slug": "basic-auth", "description": "基本認証" },
      { "slug": "email-password-login", "description": "メール・パスワードログイン" }
    ]
  },
  "existingFeatures": []
}
```

## プロンプト

```
ユーザーストーリーを分析し、以下の情報を抽出してください。

## ストーリー
{story_content}

## 抽出項目

1. **ストーリーの要約**
   - タイトル（20文字以内）
   - 説明（100文字以内）

2. **ゴール**
   - このストーリーが達成したいこと

3. **スコープ**
   - included: このストーリーに含まれる機能（リスト）
   - excluded: 明確に含まれない機能（リスト）

4. **受入条件**
   - ストーリーが完了したと言える条件（リスト）

5. **slug候補**
   - feature-slug: 機能カテゴリを表す短いスラッグ（3候補）
   - story-slug: このストーリーを表す短いスラッグ（3候補）
   - 既存のfeatureがあれば `existingFeatures` にリスト

## 出力形式

JSON形式で出力してください。
```

## 注意事項

- スコープは明確に区切る（スコープクリープ防止）
- 受入条件は具体的で検証可能な形式にする
- slug候補は短く、ハイフン区切りで英小文字のみ
