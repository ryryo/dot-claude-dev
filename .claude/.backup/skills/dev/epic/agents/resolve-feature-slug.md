---
name: resolve-feature-slug
description: フィーチャー要件から slug 候補を生成し、既存 feature-slug との類似性を判定して推奨順位を付ける。
model: haiku
allowed_tools: Glob
---

# Resolve Feature Slug Agent

フィーチャーの基本要件から slug 候補を生成し、既存の feature-slug と比較して推奨順位を付ける。

## 入力

- ユーザーのフィーチャー要件（テキスト）
- 既存 feature-slug の一覧（Glob で取得）

## 処理

1. フィーチャー要件から slug 候補を3つ生成（ハイフンケース、英小文字）
2. `Glob("docs/FEATURES/*/")` で既存 feature-slug ディレクトリを一覧取得
3. 各既存 slug について、生成した候補と意味的に類似するか判定
4. 類似するものがあれば「既存 slug を再利用」を推奨候補の先頭に配置

## 出力

JSON形式:

```json
{
  "existingFeatureSlugs": ["user-auth", "dashboard"],
  "featureOptions": [
    { "slug": "user-auth", "description": "ユーザー認証機能", "isExisting": true, "recommended": true },
    { "slug": "authentication", "description": "認証システム", "isExisting": false, "recommended": false },
    { "slug": "login-system", "description": "ログインシステム", "isExisting": false, "recommended": false }
  ]
}
```

## プロンプト

```
フィーチャー要件から slug 候補を生成し、既存 slug と比較して推奨順位を付けてください。

## フィーチャー要件
{feature_requirements}

## 既存 feature-slug 一覧
{existing_slugs}

## ルール

1. フィーチャー要件の内容を端的に表す slug 候補を3つ生成する（ハイフンケース、英小文字、2-4語）
2. 既存 slug と意味的に同じ・類似するものがあれば、既存 slug を推奨（isExisting: true, recommended: true）
3. 新規 slug は既存と重複しない場合のみ候補に含める
4. featureOptions は推奨順にソート（recommended=true が先頭）
5. 既存 slug がない場合は、生成した候補をそのまま返す（最初の候補を recommended: true に）

## 出力形式

JSON形式で出力してください。
```
