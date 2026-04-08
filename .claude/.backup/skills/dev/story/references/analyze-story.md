# ストーリー分析仕様（analyze-story）

ユーザーストーリーを分析し、目的・スコープ・受入条件を抽出する。slug候補も生成する。

## 入力

- ユーザーストーリー（会話またはUSER_STORIES.md）
- （任意）plan.json から渡されたストーリー情報 — 存在する場合、これをベースに詳細化する。スコープは plan.json の description と整合させること

## 出力構造

`story-analysis.json` に以下の構造で作成する:

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

## 分析の手順

1. ストーリーの要約を作成する
   - タイトル（20文字以内）
   - 説明（100文字以内）
2. ゴールを特定する（このストーリーが達成したいこと）
3. スコープを明確にする
   - included: このストーリーに含まれる機能（リスト）
   - excluded: 明確に含まれない機能（リスト）
4. 受入条件を定義する（具体的で検証可能な形式）
5. slug候補を生成する
   - feature-slug: 機能カテゴリを表す短いスラッグ（3候補）
   - story-slug: このストーリーを表す短いスラッグ（3候補）
   - 既存のfeatureがあれば `existingFeatures` にリスト

## 注意事項

- スコープは明確に区切る（スコープクリープ防止）
- 受入条件は具体的で検証可能な形式にする
- slug候補は短く、ハイフン区切りで英小文字のみ
