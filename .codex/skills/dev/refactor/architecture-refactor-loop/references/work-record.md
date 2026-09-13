# 複数goalの作業記録

複数goalや再開管理が必要で、同じ役割の既存PLANがない場合に使う。

`mktemp -d`等で作業ごとに独立した一時ディレクトリを作り、短い`progress.md`と必要なgoal契約を置く。repository名だけの固定一時pathを並行作業で共有しない。一時領域を使えない場合は`.codex/tmp/`配下の固有ディレクトリを使う。

## Progress

- 対象scope、既存差分、維持する契約
- Architecture mapと全適用観点のfinding／なしの根拠
- 採用goal、依存、owner、状態
- deferした候補と理由
- 変更path、検証・レビュー結果、残リスク

## Goal contract

```markdown
# Gxx: <改善する構造上の問題>

- 根拠: <path、到達経路、architecture pain>
- 維持する契約:
- 望む責務・依存・state／副作用境界:
- Owner:
- Read/write scopeと禁止範囲:
- 依存と実装方針:
- 受け入れ条件:
- 検証方法とrollback上の注意:
- 委譲する場合の理由・worker検証・main検収:
- 結果: <変更path、検証、Codexレビュー、残リスク>
```

同じ契約をprogressとgoalへ全文転記しない。progressは一覧、goalは個別の実行契約を持つ。ユーザーが`/goal`実行を明示した環境ではこの契約を入力に使い、それ以外はmainが直接実行する。
