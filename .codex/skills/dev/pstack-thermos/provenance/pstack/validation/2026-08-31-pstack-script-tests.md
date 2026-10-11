# pstack script test receipt

- Date: 2026-08-31
- Upstream source commit: `fd878692de15a3069c21c8f429eb0b9f2fe178fa`
- Candidate predecessor: `ba11091d50e1dab123feba91d6bd1f5fd22fa395`
- Bun: `1.3.13`
- Scope: upstream `poteto-mode/scripts` copied byte-for-byte into the Codex
  plugin.

## Byte-parity check

```sh
diff -qr \
  "$UPSTREAM_PSTACK/skills/poteto-mode/scripts" \
  plugins/pstack-codex/skills/poteto-mode/scripts
```

`UPSTREAM_PSTACK` was the temporary read-only checkout pinned to the upstream
commit above. Result: exit `0`, no differences.

## Final isolated test command

The first local attempt inherited a global Git checkout hook and failed two
temporary-repository fixture commits despite successful branch creation. The
final command isolated test repositories from user and system Git config and
supplied an ephemeral fixture-only author identity. It did not change user Git
configuration.

```sh
GIT_CONFIG_NOSYSTEM=1 \
GIT_CONFIG_GLOBAL=/dev/null \
GIT_AUTHOR_NAME=pstack-eval \
GIT_AUTHOR_EMAIL=pstack-eval@invalid \
GIT_COMMITTER_NAME=pstack-eval \
GIT_COMMITTER_EMAIL=pstack-eval@invalid \
bun test orch watch-pr
```

Terminal summary:

```text
52 pass
0 fail
206 expect() calls
Ran 52 tests across 4 files. [2.36s]
```

Covered files:

- `orch/orch.test.ts`
- `watch-pr/policy.test.ts`
- `watch-pr/github.test.ts`
- `watch-pr/cli.test.ts`
