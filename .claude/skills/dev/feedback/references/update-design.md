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

### 機能別DESIGN.md (`docs/FEATURES/{feature-slug}/DESIGN.md`)

```markdown
# {機能名} 設計ドキュメント

## 概要
{機能の目的と概要}

## アーキテクチャ

### コンポーネント構成
{コンポーネント図}

### 技術スタック
- フロントエンド: {React, Vue.js等}
- バックエンド: {Node.js, Go, Python等}
- その他: {使用ライブラリ}

## 設計判断

### {判断項目}
- **決定**: {決定内容}
- **理由**: {理由}
- **代替案**: {検討した代替案}

## 更新履歴

### {YYYY-MM-DD}: {story-slug}

**設計判断**:
- {決定内容}（理由: {理由}）

**学んだこと**:
- {発見内容}

**注意点**:
- {警告内容}
```

### 総合DESIGN.md (`docs/FEATURES/DESIGN.md`)

```markdown
# プロジェクト設計ドキュメント

## 概要
{プロジェクトの目的と概要}

## アーキテクチャ概要

### 主要コンポーネント
| コンポーネント | 責務 | 参照 |
|---------------|------|------|
| {コンポーネント名} | {責務} | [詳細](FEATURES/{feature-slug}/DESIGN.md) |

## 全体設計判断

### {重要な判断}
- **決定**: {決定内容}
- **理由**: {理由}
- **影響範囲**: {影響を受けるコンポーネント}

## 機能別ドキュメント
- [{機能名}](FEATURES/{feature-slug}/DESIGN.md)

## 更新履歴

### {YYYY-MM-DD}: {feature-slug}
- {重要な設計判断のサマリー}
```

## 粒度ルール

| 項目 | 総合DESIGN.mdに記載 | 機能DESIGN.mdのみ |
|------|---------------------|-------------------|
| アーキテクチャ決定 | YES | - |
| 技術スタック選定 | YES | - |
| 共通パターン発見 | YES | - |
| 機能固有の実装詳細 | - | YES |
| 一時的なワークアラウンド | - | YES |

## 更新フォーマット

```markdown
### {YYYY-MM-DD}: {story-slug}

**設計判断**:
- {決定内容}（理由: {理由}）

**学んだこと**:
- {発見内容}

**注意点**:
- {警告内容}
```

## 注意事項

- 追記のみ、既存内容は変更しない
- 日付は YYYY-MM-DD 形式
- 重複する内容は統合
- 将来の開発者が読むことを意識
- 参照リンクを維持
