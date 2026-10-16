# 独立した視点で反証レビューする

[実行条件](../../execution.md)を読んでから使う。

計画・設計・検証資料を反証する。コード差分のレビューは [thermos](../../thermos/guide.md)へ進む。

この配布物の [adversarial-review](../adversarial-review/guide.md) を使う。対象の固定、読み取り専用、証拠、判定、権限の規則を維持する。

正しさを疑うSkeptic、構造を調べるArchitect、不要な複雑さを調べるMinimalistを必要な範囲で独立させる。コメントには任意で `comment-sicko` を追加する。レビュー担当を実装担当にせず、担当の意見が一致したことを独立した受入検査の代わりにしない。

[採点基準](rubric.md)、[担当への指示](reviewer-prompt.md)、[コード品質](code-quality-review.md)、[親の判断](lead-judgment.md)を必要なレビューで読む。統合した判定と親の判断を返し、対象を変更しない。
