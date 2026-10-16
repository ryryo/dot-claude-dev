# TypeScriptの型と境界を整える

[Codexでの実行規則](../../execution.md)を読んでから使う。

先に `principle-type-system-discipline` を読む。[具体例](patterns.md)を必要な構文で使う。

選択肢は `kind` 等の判別共用体にし、任意項目の袋で矛盾状態を許さない。意味の異なる基本値にはブランドを付け、境界で一度検証する。非空列 `[T, ...T[]]`、ペア列 `[T, T][]`、開始と期間など、不正な値を構築できない形を選ぶ。すべての操作が全域なら通常の `T[]` を維持する。

外部値は `unknown` にし、repoの実行時スキーマで解析して `z.infer` 等から型を導出する。型の断言は検証後だけにする。絞り込みは判別switch、`in`、`typeof`・`instanceof`、検査するtype guard、断言の順を優先する。guardは実際に主張を検査し `isX`・`hasX` で命名する。

default分岐で `const _exhaustive: never = x` を使い、状態追加を型エラーにする。値検証とliteral保持には `as` より `satisfies` を使う。境界で対象の概念の型へ解析し、`Record<string, unknown>` を内部へ残さない。

新interfaceの前に `Pick`・`Omit`・`Parameters`・`ReturnType`・`Awaited`・`typeof` で導出できるか調べる。引数は対象を示すobjectを優先するが、フレーム毎の描画、tokenizer、parserなどの高頻度経路は例外にする。

動かせる処理をモックにせず、フレームワークの検査と資源解放を使い、UIは実ビルドで確認する。出荷コードの診断はIDから追える構造化ログにし、`console.log` を残さない。
