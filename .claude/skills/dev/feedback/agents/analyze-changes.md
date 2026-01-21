# analyze-changes

## 役割

git diffから変更内容を分析し、学習事項を抽出する。

## 推奨モデル

**sonnet** - 変更分析に適切なバランス

## 入力

- git diff --stat
- git log --oneline
- 変更されたファイル

## 出力

```json
{
  "changedFiles": [
    {
      "path": "src/auth/validate.ts",
      "type": "added",
      "description": "バリデーション関数を追加"
    }
  ],
  "addedFeatures": [
    "メールアドレスバリデーション",
    "パスワード強度チェック"
  ],
  "designDecisions": [
    {
      "decision": "Zodを使用したバリデーション",
      "reason": "型安全性と表現力の両立",
      "alternatives": ["手動バリデーション", "Yup"]
    }
  ],
  "discoveries": [
    {
      "topic": "Zodのエラーメッセージカスタマイズ",
      "detail": ".message()でカスタムエラーメッセージを設定可能"
    }
  ],
  "warnings": [
    {
      "topic": "パスワードバリデーションの順序",
      "detail": "長さチェックを先にしないとエラーメッセージが不適切になる"
    }
  ]
}
```

## プロンプト

```
以下のgit diffから変更内容を分析してください。

## git diff
{git_diff}

## git log
{git_log}

## 抽出項目

1. **変更されたファイル**
   - パス
   - 変更タイプ（added/modified/deleted）
   - 説明

2. **追加された機能**
   - 機能名のリスト

3. **設計判断**
   - どのような判断をしたか
   - なぜその判断をしたか
   - 代替案は何があったか

4. **技術的な発見**
   - 新しく学んだこと
   - ライブラリの使い方
   - パターン

5. **注意点・ハマりどころ**
   - 注意すべきポイント
   - 将来の開発者への警告

## 出力形式

JSON形式で出力してください。
```

## 注意事項

- 設計判断は「なぜ」を重視
- 発見は具体的に記録
- 警告は将来の開発者のために
