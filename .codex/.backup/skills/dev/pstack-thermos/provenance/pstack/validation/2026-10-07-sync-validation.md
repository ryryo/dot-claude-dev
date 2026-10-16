# Classified sync validation

Runtime target commit: `a1d279dd0beda5e7b0730874d36da0f0c145932d`.
Native CLI: `codex-cli 0.159.3`.

| Gate | Outcome |
| --- | --- |
| Structural discovery | PASS, 53 skills and five agents |
| Python regression suite | PASS, 15 tests |
| Bundled orch/watch-pr suite | PASS, 52 tests |
| Strict helper typecheck | PASS |
| Published plan, log, worktree behavior | PASS, 17 Node tests |
| Bounded upstream inventory | PASS, all 104 changed source paths at 0.15.5 |
| Five-agent live smoke | PASS, exact child/parent sentinels for every native role |
| Release dry-run | PASS, calculates and verifies 1.1.0 on the proposed branch |
| Whitespace and relative resources | PASS; the source example URL placeholder is not a local resource |

The initial independent native review found stale generated plan paths, an unsafe copied VM-isolation claim, and no-op model-choice tests. All three were fixed. A focused recheck confirmed those corrections and independently reproduced rejection of a placeholder in the perf probe. Its remaining test-coverage finding was fixed by populating and mutating the actual perf probe, with an assertion that the intended command exists before mutation.

Live probes ran from the exact trusted checkout in fresh persistent native parent tasks, with read-only sandbox and strict configuration. Agent files, role permissions, and inherited model/effort settings remain unchanged. Command-line trust overrides alone did not activate project configuration discovery; the setup's documented exact-path trust requirement was applied. No extra role registry was needed.

The smoke receipt records the runtime target SHA. Later changes only tighten the perf test fixture and attach validation evidence; they do not change the tested runtime instructions or agent definitions. The CI run on the final PR head is the final structural/helper gate.

Git test fixtures used isolated Git configuration to avoid the user's global commit hooks. The worktree regression test covers canonical paths with spaces, cached-ref preservation, no fetch, and preservation of untracked files. Automation scheduling, live forge mutations, bridge/Benny installation, and cap writes were not exercised or claimed.

## GitHub review closure

The two review findings on PR #3 were reproduced with failing tests before the fixes. Upstream comparisons now use NUL-delimited, rename-disabled records so a rename yields separate delete and add paths, including filenames with tabs and newlines. Validation checks only the current required smoke receipt against the current agent roster; historical receipts remain present and immutable. The regression test preserves a historical retired roster and still rejects failure in the current receipt. All 15 Python tests and the 104-path pinned inventory check pass. Native agent definitions and runtime workflows were unchanged by these review fixes.

The follow-up GitHub review found false positives for inline generic types, HTML markup, and Markdown autolinks. Three failing regression cases reproduced them. Placeholder detection now uses the shipped scaffold vocabulary while still rejecting known unfilled model and command fields. All 14 Node behavior tests pass. Live host coverage remains CLI-only; Codex desktop app discovery and agent spawning have not yet been exercised.

The next review found an SVG tag collision and a Cursor-only liveness instruction. The file placeholder is now explicitly named `<file path>`, eliminating the collision with SVG `<path>` without weakening the populated-field gate. Regressions cover raw and inline SVG markup and an unfilled file action. Orchestration now uses available native collaboration state and waits, reports unavailable state as unknown, and reconciles ownership after either CLI or desktop restart. These guide changes do not claim an exercised desktop app run.
