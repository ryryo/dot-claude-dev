# resolve-slug

## 役割

既存のfeature-slugを探索し、今回のストーリーとの類似性を判定して、slug候補を整理する。
新規slug乱立を防ぐ。

## 推奨モデル

**haiku** - 単純な比較・整理タスク

## 入力

- story-analysis.jsonの内容（slugCandidates含む）
- 既存feature-slugの一覧（Globで取得）

## 処理

1. `Glob("docs/features/*/")` で既存feature-slugディレクトリを一覧取得
2. 各既存slugについて、story-analysis.jsonのslugCandidatesと意味的に類似するか判定
3. 類似するものがあれば「既存slugを再利用」を推奨候補の先頭に配置

## 出力

JSON形式:

```json
{
  "existingFeatureSlugs": ["user-auth", "dashboard"],
  "featureOptions": [
    { "slug": "user-auth", "description": "ユーザー認証機能", "isExisting": true, "recommended": true },
    { "slug": "authentication", "description": "認証システム", "isExisting": false, "recommended": false }
  ],
  "storyOptions": [
    { "slug": "login-form", "description": "ログインフォーム実装" }
  ]
}
```

## プロンプト

```
既存のfeature-slugとストーリー分析結果を比較し、slug候補を整理してください。

## 既存feature-slug一覧
{existing_slugs}

## ストーリー分析のslug候補
{slug_candidates}

## ルール

1. 既存slugと意味的に同じ・類似するものがあれば、既存slugを推奨（isExisting: true, recommended: true）
2. 新規slugは既存と重複しない場合のみ候補に含める
3. featureOptionsは推奨順にソート（recommended=true が先頭）
4. storyOptionsはそのまま返す

## 出力形式

JSON形式で出力してください。
```
