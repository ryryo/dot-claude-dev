# 委任 prompt

1 prompt に 1 task だけを書く。Cursor CLI prompt は一意な `Task Summary:` を先頭に置き、`Task ID:` を必ず含める。Codex subagent は `Task Summary:` を省略できる。

```text
Task Summary:
<task id、担当領域、成果物が分かる 180 文字以内の文>

Worker: <cursor-cli-agent | codex-subagent>
Model: <selected model>
Reasoning effort: <selected effort | fixed>
Routing policy: <policy_id>
Routing class: <high | medium | low>
Routing reason: <task type / escalation or low-route conditions>
Workspace: <absolute path>
Task ID: <unique id>

Goal:
<具体的な成果 1 件>

Read first:
- <absolute path>

Write scope:
- Allowed: <paths | none>
- Forbidden: allowed scope 外、planning / progress、commit、branch、remote、未許可の lockfile / generated file

Constraints:
- 既存の未コミット変更や担当外の変更を戻さない。
- 他の worker またはユーザーが同じ workspace で作業中の前提で進める。
- <task 固有の制約>

UI / UX contract:
- <surface / user flow / existing pattern / states / interaction-accessibility / verification | not_applicable>

Verification:
- Run: <specific command>
- 実行できない場合は理由と代替確認を報告する。

Final report:
- TASK_ID / MODEL / REASONING_EFFORT
- 変更ファイルと要約
- 検証結果
- main Codex に残した作業
```

Codex subagent の model / reasoning は prompt と起動引数を一致させる。指定値が使えない場合はfallbackせずmain Codexへ戻す。UI taskはplanのUI / UX contractを要約し、worker scope外のproduct-level visual verificationはmain Codexへ残す。
