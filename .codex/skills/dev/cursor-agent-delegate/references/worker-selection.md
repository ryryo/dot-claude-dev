# Worker Selection

Main Codex chooses the worker. Do not pick a worker until the goal, ownership, write scope, and verification are clear.

## Worker types

| Worker | Use for | Do not use for |
|--------|---------|----------------|
| `codex-subagent` | Complex domain logic, algorithms, state transitions, design comparison, risk analysis, difficult reviews, test strategy | Final integration, completion decisions, commits, push, PR |
| `cursor-agent` | Localized implementation, pure functions, adapters, schemas, validators, unit tests, existing-pattern edits | Ambiguous specs, cross-cutting state/routing/auth/migrations, deep architecture |
| `main-codex` | Orchestration, scope decisions, final review, integration, progress updates, commits, PRs | Parallel side work that can be safely delegated |

## Decision rules

- Use `codex-subagent` when the task needs reasoning depth more than speed.
- Use `cursor-agent` when the task is bounded, mechanical enough to implement quickly, and easy to verify with commands.
- Keep the task in `main-codex` when requirements are ambiguous, the next local step is blocked by the result, or final integration judgment is required.
- Split work only when worker write scopes are disjoint.
- Treat every worker output as untrusted until main Codex reviews it.

## Codex subagent prompt requirements

Include:

- Ownership of files or responsibility.
- Whether edits are allowed.
- Other workers may be active; do not revert or overwrite unrelated changes.
- Read-first paths and relevant constraints.
- Verification command or expected review output.
- Final report format.

For coding work, tell the subagent to edit directly in its forked workspace when the tooling supports it, and to list changed files in the final report.

## Cursor Agent prompt requirements

Use [delegation-prompt-template.md](delegation-prompt-template.md). Prefer Cursor Agent for tasks where a short implementation plus command verification is enough.
