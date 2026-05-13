# Cursor Delegation Protocol

Cursor Agent へ委任する場合は、期待成果物、編集範囲、禁止事項、検証、報告形式を明示した詳細な作業契約を渡す。

## 委任の判断

`tasks.json` の `preDelegation[]` に項目がある場合に委任候補となる。使用するかは実行開始時にユーザーへ確認する。

委任しない場合は Codex 単独で該当作業を実行する。

実行コマンドの基本形:

```bash
cursor-agent -p --mode ask --output-format text --workspace <workspace> --model <model> "<prompt>"
```

調査・読み取りのみなら `--mode ask`、編集を伴う場合は write scope と禁止事項を明示する。

## 委任できる作業

次の条件を**全て満たす**作業のみ `preDelegation[]` に切り出す。

- 他の Gate の完了を待たずに**今すぐ先行実行できる**（依存する状態・ファイルが未生成でも作業できる）
- write scope が単一または少数のファイルに限定されており、他 Gate・共通 state と干渉しない
- 検証コマンドが明確で、結果の正誤を機械的に判定できる

具体例: 純粋関数・validator・formatter・schema・単体テスト・小さな adapter

## 委任してはいけない作業

- `docs/PLAN` 更新・`tasks.json` 更新・`spec.md` generated 領域同期
- Gate PASS 判定・最終統合・commit / push
- routing・共通 state・export pipeline など複数 Gate にまたがる高結合な作業
- 実ブラウザ最終検証

## 指示書に必ず含める項目

Cursor 向けプロンプトには必ず含める。

- 作業場所。
- 対象 Gate / Todo / AC。
- 読むべき参照ファイル。
- 変更してよいファイルまたはディレクトリ。
- 触ってはいけないファイル。
- 既存変更を戻さないこと。
- 検証コマンド。
- 完了報告フォーマット。

実装結論を過剰に誘導しない。期待する結果、制約、検証条件を渡し、具体的な局所実装は担当エージェントに任せる。

## tasks.json の preDelegation フィールド

先行実行させたい作業は Todo から切り出して `preDelegation[]` に記載する。フィールド定義は [tasks-schema-v3-codex.md](templates/tasks-schema-v3-codex.md) の `PreDelegation` セクションを参照。

`preDelegation[]` が空または省略されていても `spec-codex-run` は通常 v3 として実行する。
