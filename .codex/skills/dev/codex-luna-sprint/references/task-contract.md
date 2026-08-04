# Luna Sprint task contract

## Task routing

`tasks.md`では最初にownerを`main-codex`とする。次を満たすtaskだけ`luna_sprint_worker`へ変更し、agent type／roleを名前で指定してspawnする。spawnのmodel override一覧でrouting可否を判断しない。

```text
Task ID: T20
Owner: main-codex | luna_sprint_worker
State: not_started | running | worker_done | accepted | blocked
Goal:
Dependencies:
Complexity: low | medium | high
Decision state: fixed | bounded | unresolved
Independence: independent | staged | coupled
Side effect: local_reversible | shared_reversible | external_or_irreversible
Verification oracle: strong | partial | weak
Parallel group:
Read scope:
Write scope:
Forbidden:
Conflicts:
Acceptance:
Worker verification:
Main verification:
```

`unresolved`、`coupled`、`external_or_irreversible`、`weak`のいずれかを含むtaskは委任しない。

## Worker prompt

```text
Task Summary:
T20 - <担当領域と成果物を一行で書く>

あなたはGPT-5.6 Luna highで動くluna_sprint_workerです。

Worker:
luna_sprint_worker

Workspace:
<absolute workspace path>

Task ID:
T20

Complexity:
low | medium | high

Decision state:
fixed | bounded

Independence:
independent | staged

Side-effect scope:
local_reversible | shared_reversible

Verification oracle:
strong | partial + mainが確認する限定項目

Goal:
実装taskを一つだけ書く。

Read first:
- <absolute path>

Write scope:
- Allowed:
  - <path>
- Forbidden:
  - docs/PLAN/**
  - .codex/skills/**
  - 明示されていない.codex/tmp/**
  - package lock files
  - allowed scope外

Constraints:
- stage、commit、push、PR、branch変更、計画更新をしない。
- 他agentへ委任しない。
- 既存の無関係な変更を戻さない。
- TDD、YAGNI、behavior testを守る。
- 未解決判断が必要なら推測せず停止して報告する。
- production、外部設定、実data、課金、権限を変更しない。

Verification:
- Run: <focused command>

Final report:
- TASK_ID: T20
- 変更したファイル
- 変更内容
- 実行した検証と結果
- main Codexへ残した作業
```

promptはtask-local contextだけを含める。長い計画全文を貼らず、必要なcontract、参照path、negative case、oracleだけを書く。
