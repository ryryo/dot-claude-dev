# propose-improvement

## 役割

検出されたパターンをリファクタリング/スキル・ルール化する提案を生成する。

## 推奨モデル

**opus** - 高品質な提案生成に必要

## 入力

- Phase 1（analyze-changes.md）の分析JSON
- Phase 2a-2cのDESIGN.md更新内容
- 既存のルール/スキル一覧
- feature-slug, story-slug

## 出力

- `docs/features/{feature-slug}/IMPROVEMENTS.md`

## プロンプト

```
以下の情報を入力として、改善提案とリファクタリング計画をMarkdownでまとめてください。

## 入力
- Phase 1（変更分析）のJSON出力
- DESIGN.md更新内容（機能別・総合）
- コード整理（SIMPLIFY）で気づいた改善ポイント

## 出力先
docs/features/{feature-slug}/IMPROVEMENTS.md

## Markdownの構成

# 改善・リファクタリング提案 ({feature-slug}, {story-slug})

## 1. リファクタリング候補
- {対象ファイルと概要}
  - 目的（なぜ変えるのか）
  - 変更の方針（どのように変えるか）
  - 想定される影響範囲
  - 実施時のチェックポイント

## 2. スキル化候補
- {パターン名}
  - 背景 / 文脈
  - 適用条件
  - 期待される効果
  - 想定されるSKILL.mdの場所

## 3. ルール化候補
- {ルール名}
  - 背景 / 文脈
  - 適用条件
  - 期待される効果
  - 想定されるルールの場所

## 4. メモ / 補足
- 後続エージェントが知っておくべき前提・注意点

## 注意
- コードや設定ファイルを直接変更しない
- 実作業は別エージェント（dev:developing, meta-skill-creator等）に委ねる前提
- 「目的・背景・手順・影響範囲」がわかるレベルまで具体的に書く
```

## 注意事項

- 既存との重複を避ける
- 具体的な効果を記載
- meta-skill-creatorとの連携を考慮
