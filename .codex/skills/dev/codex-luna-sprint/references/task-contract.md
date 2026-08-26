# Luna Sprint task contract

## Routing registry

全taskを`main-codex`で登録し、Product frameとImplementation planがともに`confirmed`の場合だけLuna routingを検討する。

```text
Task ID:
Owner: main-codex | luna_sprint_worker
State: not_started | running | worker_done | accepted | corrected-by-main | rejected | blocked
Goal:
Main-owned story/UX trace (registry only; workerへ解釈させない):
Input provenance:
Dependencies:
Source of truth:
Fixed decisions:
Forbidden decisions:
Plan invalidation conditions:
Decision state: fixed | bounded | unresolved
Independence: independent | staged | coupled
Side effect: local_reversible | shared_reversible | external_or_irreversible
Verification oracle: strong | partial | weak
Read scope:
Exclusive write scope:
Conflicts:
Positive cases:
Negative cases:
Worker verification:
Main verification:
Delegation benefit:
Mechanical rejection oracle:
Acceptance:
```

Lunaへ委譲できるDecision stateは`fixed`だけとする。`bounded`または`unresolved`を含むtask、`coupled`、`external_or_irreversible`、`weak`を含むtask、user story、UX、UI、文言、accessibility、product/schema/API contract、mutation、状態遷移の判断を含むtask、またはreview負担が実装以上のtaskは委任しない。固定済みAPI adapterは、HTTP method/path、request/response schemaとfield mapping、validation/coercion、auth/authorization/ownership（不要ならmainが`N/A`と明記）、success status、error algebra/body、idempotency、mutation/side-effect semanticsのすべてをmainが完全指定し、workerに残る作業が機械的写像だけの場合に限り候補とする。

## Worker prompt

```text
Task Summary:
T20 - <一つの完全固定済み成果物>

あなたはluna_sprint_workerです。確定済みleafを実装し、product・architecture判断はしません。

Workspace:
<absolute path>

Task ID:
T20

Source of truth — read first:
- <absolute path and section>

Fixed contract:
- <function signature, I/O, error algebra, exact behavior table>

Forbidden decisions:
- user story、UX、UI、文言、accessibility、domain/API/schema contract、mutation、state transitionを判断・補完・推測・変更しない
- user-facing componentを新設・編集しない
- 未指定のfallback、default、汎用化を追加しない

Positive cases:
- <normal case>

Negative cases:
- <malformed, boundary, overflow, conflict等の機械的case>

Write scope:
- Allowed: <exclusive paths>
- Forbidden: docs/PLAN/**, .codex/skills/**, lockfiles, allowed scope外

Stop without changes when:
- source間の矛盾、未解決判断、scope競合、外部副作用、UI/UX/API判断が必要

Constraints:
- version control、remote、計画更新、再委任の操作をしない。
- 無関係な差分を戻さない。
- TDD、YAGNI、behavior testを守る。

Verification:
- Run: <focused command>

Final report:
- TASK_ID
- 変更fileと要約
- verification command/result
- 未解決事項とmainへ残した作業
```
