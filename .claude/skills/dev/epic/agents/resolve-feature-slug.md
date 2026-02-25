---
name: resolve-feature-slug
description: 既存の feature-slug を探索し、slug 候補との類似性を判定して推奨順位を付ける。新規 slug 乱立を防ぐ。
model: haiku
allowed_tools: Glob
---

# Resolve Feature Slug Agent

既存の feature-slug を探索し、analyze-epic が生成した slug 候補との類似性を判定して、推奨順位を付ける。

## 入力

- analyze-epic の出力（featureSlugCandidates）
- 既存 feature-slug の一覧（Glob で取得）

## 処理

1. `Glob("docs/FEATURES/*/")` で既存 feature-slug ディレクトリを一覧取得
2. 各既存 slug について、analyze-epic の featureSlugCandidates と意味的に類似するか判定
3. 類似するものがあれば「既存 slug を再利用」を推奨候補の先頭に配置

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
既存の feature-slug と新しい slug 候補を比較し、推奨順位を付けてください。

## 既存 feature-slug 一覧
{existing_slugs}

## analyze-epic の slug 候補
{slug_candidates}

## ルール

1. 既存 slug と意味的に同じ・類似するものがあれば、既存 slug を推奨（isExisting: true, recommended: true）
2. 新規 slug は既存と重複しない場合のみ候補に含める
3. featureOptions は推奨順にソート（recommended=true が先頭）
4. 既存 slug がない場合は、候補をそのまま返す（最初の候補を recommended: true に）

## 出力形式

JSON形式で出力してください。
```
