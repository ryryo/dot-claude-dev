# update-design

## 役割

DESIGN.mdを更新し、設計判断と学習事項を蓄積する。

## 推奨モデル

**opus** - 高品質な設計ドキュメント生成に必要

## 入力

- analyze-changes.mdの出力
- 既存のDESIGN.md（あれば）
- feature-slug, story-slug

## 出力

- `docs/features/{feature-slug}/DESIGN.md` の更新
- `docs/features/DESIGN.md` の更新（重要な判断のみ）

## プロンプト

```
DESIGN.mdを更新してください。

## 変更分析結果
{analysis_result}

## 既存のDESIGN.md
{existing_design}

## 更新ルール

1. **機能別DESIGN.md** (`docs/features/{feature-slug}/DESIGN.md`)
   - このストーリーの全ての学習事項を追記
   - 更新履歴セクションに日付とストーリー名を記載

2. **総合DESIGN.md** (`docs/features/DESIGN.md`)
   - 重要な設計判断のみを追記
   - プロジェクト全体に影響する内容のみ

## 更新フォーマット

```markdown
## 更新履歴

### {date}: {story-slug}

**設計判断**:
- {決定内容}（理由: {理由}）

**学んだこと**:
- {発見内容}

**注意点**:
- {警告内容}
```

## 重要

- 既存の内容は削除しない（追記のみ）
- 日付は YYYY-MM-DD 形式
- 重複する内容は統合
```

## 注意事項

- 追記のみ、既存内容は変更しない
- 重要度に応じて総合DESIGN.mdへの反映を判断
- 将来の開発者が読むことを意識
