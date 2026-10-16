# Codex eval summary

Paired isolated evaluations compared the adapted skill against a no-skill
baseline. Independent grader agents applied the same assertions to both sides.

| Skill | With skill | Baseline | Delta |
| --- | ---: | ---: | ---: |
| `adversarial-review` | 8/8 | 3/8 | +62.5 percentage points |
| `poteto-mode` | 8/8 | 5/8 | +37.5 percentage points |

The review evals measured exact target binding, concrete failure scenarios,
terminal-evidence discipline, prescribed advisory verdicts, and explicit
authority boundaries. The poteto-mode evals measured terminal-path definition,
RED-before-implementation sequencing, semantic impact analysis, root-cause
scope, and separation of implementation, validation, deployment, runtime, and
authority outcomes.

Timing was unavailable from the host's subagent notifications. Reported size
metrics were output-character proxies, not model-token counts.
