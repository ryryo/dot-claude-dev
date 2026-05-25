# Front-end Design Patterns References

JavaScript / React の設計・実装・レビュー・リファクタリングで使う reference 群。
このディレクトリは Patterns.dev 由来の個別 SKILL.md を、統合スキルから参照しやすい形へ変換したもの。

## 使い方

1. まず [decision-matrix.md](decision-matrix.md) を読む。
2. 依頼内容とコード上の症状から、必要な React / JavaScript reference を 1〜4 件に絞る。
3. [react/index.md](react/index.md) または [javascript/index.md](javascript/index.md) で対象 reference を確認する。
4. 個別 reference の `Original Skill Metadata` と `original-skill-body` を読んで判断する。

## Scope

- React references: [react/index.md](react/index.md)
- JavaScript references: [javascript/index.md](javascript/index.md)
- Vue: out of scope。この統合スキルでは Vue 由来の元資料を参照しない。

## Lossless Conversion Policy

- 元の YAML frontmatter は各 reference の `Original Skill Metadata` に fenced `yaml` block として保持する。
- 元の Markdown 本文は `<!-- original-skill-body:start -->` / `<!-- original-skill-body:end -->` の間に保持する。
- 元本文の削除、圧縮、意訳、統合要約は行わない。
