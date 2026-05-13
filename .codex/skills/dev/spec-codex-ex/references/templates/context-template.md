# context.md Template

`docs/PLAN/{YYMMDD}_{slug}/references/context.md` は、PLAN が前提にする確認済み事実を記録する。

```markdown
# Context

## Project Rules

| Source | Confirmed rule | Impact on PLAN |
| --- | --- | --- |

## Relevant Files

| Path | Confirmed fact | Impact on PLAN |
| --- | --- | --- |

## External References

| Source | Local reference path | Confirmed fact | Impact on PLAN |
| --- | --- | --- | --- |

## Commands

| Command | Exists because | Used by |
| --- | --- | --- |

## Excluded Assumptions

| Assumption | Why excluded | Required evidence to include |
| --- | --- | --- |
```

## Contract

- `Project Rules` records repository conventions and constraints.
- `Relevant Files` records code, tests, existing PLANs, and reference implementations that were inspected.
- `External References` records codebase-external materials copied or summarized under `references/`.
- `Commands` records validation commands used by AC or review gates.
- `Excluded Assumptions` records files, APIs, commands, or behaviors not used as PLAN premises.
