# 委任 prompt のテンプレート

Cursor Agent または Codex subagent に渡す prompt は、実装方針を過剰に誘導せず、期待する成果・制約・検証条件を明示する。

```text
あなたはこの repository 内で動く worker agent です。

ワーカー種別:
<codex-subagent または cursor-agent>

作業 workspace:
<絶対パス>

タスク ID:
<一意な task id>

目的:
<具体的な作業を 1 件だけ>

最初に読むもの:
- <絶対パス>
- <絶対パス>

編集範囲:
- 編集してよいファイル:
  - <path>
  - <path>
- 編集してはいけないファイル:
  - <path>
  - docs/PLAN/**
  - progress / state / generated planning files
- 明示された write scope にないものは変更しない（commit・branch・remote・package lockfile・generated planning docs を含む）
- 既存の未コミット変更や、自分の担当外のファイルを元に戻さない
- 他の worker やユーザーが変更中のファイルがある前提で、無関係な作業を上書きしない

実装制約:
- <constraint>
- <constraint>

検証:
- 実行するコマンド: <command>
- 実行できない場合は、理由と代わりに確認した内容を具体的に報告する

最終報告:
- 変更したファイル
- 変更内容の要約
- 実行した検証コマンドと結果
- main Codex に残した作業
```

## ルール

- workspace と「最初に読むもの」には絶対パスを使う。
- 1 つの worker prompt には 1 つのタスクだけを書く。
- 並列実行では worker ごとに別のファイルを割り当てる。同じファイルを 2 つの worker に編集させない。
- Git worktree の作成・切替・管理を worker に依頼しない。
- 最終統合・Gate PASS 判定・commit・push・PR・progress ファイルの更新を worker に任せない。
- main Codex が再実行できる検証コマンドを含める。
- Codex subagent には、担当範囲と、実装・設計・レビュー・テスト戦略のどれを依頼するのかを明示する。
