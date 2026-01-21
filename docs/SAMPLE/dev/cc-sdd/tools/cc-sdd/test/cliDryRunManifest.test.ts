import { describe, it, expect } from 'vitest';
import { runCli } from '../src/index';
import { mkdtemp, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const runtime = { platform: 'darwin' } as const;

const makeIO = () => {
  const logs: string[] = [];
  const errs: string[] = [];
  return {
    io: {
      log: (m: string) => logs.push(m),
      error: (m: string) => errs.push(m),
      exit: (_c: number) => {},
    },
    get logs() {
      return logs;
    },
    get errs() {
      return errs;
    },
  };
};

const mkTmp = async () => mkdtemp(join(tmpdir(), 'ccsdd-cli-plan-'));

describe('CLI dry-run with manifest', () => {
  it('prints a formatted plan from manifest', async () => {
    const dir = await mkTmp();
    const file = join(dir, 'manifest.json');
    const m = {
      version: 1,
      artifacts: [
        {
          id: 'doc',
          source: {
            type: 'templateFile' as const,
            from: 'doc.tpl.md',
            toDir: '{{AGENT_DIR}}',
            rename: '{{AGENT_DOC}}',
          },
        },
      ],
    };
    await writeFile(file, JSON.stringify(m), 'utf8');

    const ctx = makeIO();
    const code = await runCli(['--dry-run', '--manifest', file], runtime, ctx.io, {});
    expect(code).toBe(0);
    const out = ctx.logs.join('\n');
    expect(out).toMatch(/Plan \(dry-run\)/);
    expect(out).toMatch(/\[templateFile\] doc: doc\.tpl\.md -> \.claude\/CLAUDE\.md/);
  });
});
