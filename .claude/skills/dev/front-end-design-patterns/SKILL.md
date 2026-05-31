---
name: dev:front-end-design-patterns
description: |
  JavaScript / React / Vue のフロントエンドコードを実装・レビュー・リファクタリングするときに、
  現在のコードベースを調査し、適切な設計・パフォーマンス・レンダリングパターンを
  エージェントが自律的に選んで適用する。ユーザーが hooks-pattern や dynamic-import などの
  個別パターンを指定しなくても、必要な reference を選択する。

  Trigger:
  front-end-design-patterns, frontend design patterns, React設計, Vue設計, JavaScript設計,
  Reactリファクタリング, Vueリファクタリング, フロントエンドパフォーマンス改善,
  bundle改善, レンダリング戦略, Reactレビュー, Vueレビュー
user-invocable: true
---

# front-end-design-patterns

JavaScript / React / Vue の設計・実装・レビュー・リファクタリングで、Patterns.dev 由来の参照知識を必要な分だけ読み、対象プロジェクトの既存コードに合わせて適用する。
このスキルはパターン名を増やすための教育スキルではなく、コードベース上の具体的な問題を Inspect / Classify / Select references / Apply or Review / Verify の流れで扱うための実務スキル。

## ゴール

- ユーザーが個別パターンを選ばなくても、現在のプロジェクトに必要な JavaScript / React / Vue パターンを判断する。
- 新規 UI 実装、既存コンポーネント整理、重複ロジック抽出、React render 最適化、Vue component / composable 整理、bundle / loading 改善、レンダリング戦略判断、PR レビューを支援する。
- Patterns.dev 由来の original reference を要約ではなく根拠として読み、既存コードの規約に沿って最小限の変更へ落とす。

## 基本方針

- まずコードベースを読む。`package.json`、build tool、routing、component 構成、data fetching、state 管理、既存の類似実装を確認してから判断する。
- `references/decision-matrix.md` で参照候補を絞り、必要な original reference だけを読む。大量の reference を一括で読み込まない。
- パターン適用を目的化しない。既存コードで問題になっている責務分離、再利用性、性能、bundle、hydration、review risk に対応する場合だけ適用する。
- 対象プロジェクトの既存規約を優先する。framework、package manager、routing、CSS、component API、query/cache ライブラリ、lint/test コマンドを勝手に置き換えない。
- 要約だけで実装判断しない。必要なときは `references/react/*.md`、`references/vue/*.md`、または `references/javascript/*.md` の `original-skill-body` を読んでから判断する。

## 実行手順

### Step 1: Inspect 対象コードとプロジェクト構成を読む

依頼対象が明確な場合は対象ファイルと周辺利用箇所から読む。
対象が曖昧な場合は、プロジェクトの entrypoint、router、主要 component、package scripts、build tool を確認して作業範囲を絞る。

最低限確認する観点:

- React / Vue / plain JavaScript / Vite / Next.js / Nuxt / Remix などの stack
- component 配置、state 管理、data fetching、routing、CSS の既存パターン
- `lint` / `test` / `typecheck` / `build` などの検証コマンド
- パフォーマンス依頼の場合は render cost、runtime hot path、bundle / loading cost のどれが問題か

### Step 2: Classify 依頼を user story と問題領域へ分類する

次のいずれか、または複数に分類する。

- 新規 UI 機能を、既存コードに合う React / Vue / JS 設計で実装したい
- 肥大化した React / Vue コンポーネントや重複ロジックをリファクタリングしたい
- 入力・スクロール・再レンダリングなどの UI パフォーマンスを改善したい
- 初期ロード、bundle、lazy loading、third-party script を改善したい
- CSR / SSR / SSG / ISR / Streaming / RSC などのレンダリング戦略を判断したい
- PR や差分を React / Vue / JS 設計・保守性・性能観点でレビューしたい

分類できない場合は、まずコード上の症状を確認する。設計変更・性能改善・レビュー観点がない一般的な実装では、既存コードの規約だけを優先し、このスキルの pattern reference を無理に使わない。

### Step 3: Select references 参照候補を絞る

`references/decision-matrix.md` を読み、問題領域から参照候補を 1〜4 件に絞る。
React 固有の話は `references/react/index.md`、Vue 固有の話は `references/vue/index.md`、framework-agnostic な JavaScript / loading / bundle / web platform の話は `references/javascript/index.md` を入口にする。

典型例:

- props drilling、prop-heavy API、shared UI API: React composition references
- Vue SFC、Composition API、provide/inject、renderless component: Vue references
- 不要再レンダリング、入力遅延、scroll jank: React render optimization / virtual lists
- data fetching、cache、optimistic update: React data fetching
- 初期 JS が大きい、route ごとの重い機能: dynamic import / bundle splitting / Vite optimization
- SSR、RSC、hydration、streaming: React rendering references

### Step 4: Original reference を読む

選んだ reference の `Original Skill Metadata` と `original-skill-body` を読む。
`index.md` や `decision-matrix.md` は入口であり、実装判断の根拠は個別 reference に置く。

複数 reference が必要な場合も、まず最小数で判断する。
例えば React の render 問題に bundle 問題が混ざっているときは、render optimization と dynamic import の両方を読むが、無関係な design pattern reference は読まない。

### Step 5: Apply or Review 既存コードに合わせて適用する

実装・リファクタリングの場合:

- 既存の component API、file layout、naming、state/query library に合わせる。
- custom hook、compound component、container/presentational、dynamic import、virtualization、render strategy などは、問題に対して必要な範囲だけ使う。
- 大きな抽象化や framework 移行を勝手に始めない。
- パターン名を説明するより、コードの責務・データフロー・性能特性がどう改善したかを重視する。

レビューの場合:

- 一般論ではなく、差分と周辺コードに対する bug risk、regression risk、性能 risk、保守性 risk を指摘する。
- 指摘は「このパターンに反している」ではなく「このコードだとこう壊れる / 重くなる / 保守しづらい」という形にする。
- 修正案を出す場合は、既存コードに合わせた最小変更にする。

### Step 6: Verify 変更内容に合う検証を行う

変更後は対象プロジェクトに存在するコマンドを確認し、変更内容に合う検証を行う。

候補:

```bash
npm run lint
npm run test
npm run typecheck
npm run build
```

UI や browser behavior を変更した場合は、可能ならローカル実行とブラウザ確認も行う。
検証できない場合は、実行できなかった理由と未検証範囲を報告する。

## 完了条件

- [ ] 対象コードと周辺利用箇所を読んでいる
- [ ] 依頼を user story / 問題領域へ分類している
- [ ] `references/decision-matrix.md` から必要な reference を選んでいる
- [ ] 必要な個別 reference の `original-skill-body` を読んでいる
- [ ] 既存コードの規約を優先し、パターン適用を目的化していない
- [ ] 変更内容に合う lint / test / typecheck / build / browser verification を実施、または未実施理由を報告している

## References

- [references/index.md](references/index.md)
- [references/decision-matrix.md](references/decision-matrix.md)
- [references/react/index.md](references/react/index.md)
- [references/vue/index.md](references/vue/index.md)
- [references/javascript/index.md](references/javascript/index.md)
