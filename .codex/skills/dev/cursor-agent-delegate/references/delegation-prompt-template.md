# 委任 prompt のテンプレート

Cursor CLI worker では `Task Summary:` を先頭に置く。Codex subagent では省略してよい。

```text
Task Summary:
<task id、担当領域、成果物が分かる 180 文字以内の固有文>

あなたはこの repository 内で動く worker agent です。

Worker:
<cursor-cli-agent または codex-subagent>

Model:
<gpt-5.6-sol | gpt-5.6-terra | gpt-5.5 | composer-2.5-fast>

Reasoning effort:
<選定 model の現在の起動 schema が許可する値 | fixed>

Workspace:
<絶対パス>

Task ID:
<一意な task id>

Goal:
<具体的な成果を 1 件だけ>

Read first:
- <絶対パス>
- <絶対パス>

Write scope:
- Allowed:
  - <path>
- Forbidden:
  - <path>
  - docs/PLAN/**
  - planning / progress files
  - 明示されていない lockfile と generated file
  - allowed scope 外のファイル

Constraints:
- commit、push、PR 作成、branch 切替、planning / progress 更新をしない。
- 既存の未コミット変更や担当外の変更を戻さない。
- 他の worker またはユーザーが同じ workspace で作業中の前提で進める。
- <task 固有の制約>

Verification:
- Run: <specific command>
- 実行できない場合は理由と代替確認を具体的に報告する。

Final report:
- TASK_ID: <task id>
- MODEL: <実際に使った model>
- REASONING_EFFORT: <実際に使った reasoning effort>
- 変更したファイル
- 変更内容の要約
- 実行した検証と結果
- main Codex に残した作業
```

## ルール

- 1 prompt に 1 タスクだけを書く。
- workspace と `Read first` は絶対パスにする。
- Cursor CLI prompt の `Task Summary:` は task ごとに一意にする。
- Cursor CLI prompt の `Task ID:` は registry の source of truth とする。
- Codex subagent は prompt の `Model:` と `Reasoning effort:` を起動引数にも設定する。prompt へ書くだけで model を切り替えたことにしない。
- model が fallback された場合は prompt または委任記録を更新し、元の選定と変更理由を final report に残す。
- 実装方針を過剰指定せず、成果、境界、禁止事項、検証を明確にする。
- Codex subagent の read-only task では `Write scope: none` と明記する。
- main Codex が再実行できる具体的な検証コマンドを含める。
