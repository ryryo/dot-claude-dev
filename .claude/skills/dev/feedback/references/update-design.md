# DESIGN.md更新仕様（update-design）

DESIGN.mdを更新し、設計判断と学習事項を蓄積する。
機能別DESIGN.md + 総合DESIGN.mdの両方を更新する。

## 入力

- review-analyze の分析JSON
- 既存のDESIGN.md（あれば）
- feature-slug

## 出力

- `docs/FEATURES/{feature-slug}/DESIGN.md` の更新
- `docs/FEATURES/DESIGN.md` の更新（重要な判断のみ）

## 実行フロー

### 1. 既存DESIGN.md読み込み

```
Read("docs/FEATURES/{feature-slug}/DESIGN.md")  // なければ新規作成
Read("docs/FEATURES/DESIGN.md")                  // なければ新規作成
```

### 2. 機能別DESIGN.md更新

分析JSONから更新履歴セクションに追記する。

### 3. 総合DESIGN.md更新

機能DESIGN.mdの内容から、プロジェクト全体に影響する設計判断を抽出して追記する。

### 4. 重複統合

同じ内容が複数回記録された場合は統合する。

## テンプレート

init スクリプトで配置済みの `docs/FEATURES/{feature-slug}/DESIGN.md` を Read し、各セクションの内容を埋めて Write で上書きする。新規作成の場合はテンプレート構造が既に入っている。

## 粒度ルール

| 項目 | 総合DESIGN.mdに記載 | 機能DESIGN.mdのみ |
|------|---------------------|-------------------|
| アーキテクチャ決定 | YES | - |
| 技術スタック選定 | YES | - |
| 共通パターン発見 | YES | - |
| 機能固有の実装詳細 | - | YES |
| 一時的なワークアラウンド | - | YES |

## 更新フォーマット

配置済み DESIGN.md の「更新履歴」セクションのフォーマットに準拠する。

## 注意事項

- 追記のみ、既存内容は変更しない
- 日付は YYYY-MM-DD 形式
- 重複する内容は統合
- 将来の開発者が読むことを意識
- 参照リンクを維持
