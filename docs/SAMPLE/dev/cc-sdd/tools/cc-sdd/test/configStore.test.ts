import { describe, it, expect } from 'vitest';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { mkdtemp, writeFile, readFile, stat } from 'node:fs/promises';
import { loadUserConfig, saveUserConfig } from '../src/cli/store';
import type { UserConfig } from '../src/cli/config';

const prefix = join(tmpdir(), 'ccsdd-store-');

const mkTmp = async () => {
  const dir = await mkdtemp(prefix);
  return dir;
};

describe('config store', () => {
  it('returns empty object when config file does not exist', async () => {
    const dir = await mkTmp();
    const cfg = await loadUserConfig(dir);
    expect(cfg).toEqual({});
  });

  it('saves and loads config round-trip', async () => {
    const dir = await mkTmp();
    const input: UserConfig = {
      agent: 'gemini-cli',
      lang: 'en',
      os: 'linux',
      kiroDir: '.work/kiro',
      overwrite: 'skip',
      backupDir: 'bk',
      agentLayouts: {
        'gemini-cli': { commandsDir: '.gemini/commands/custom' },
      },
    };
    await saveUserConfig(dir, input);

    const file = join(dir, '.cc-sdd.json');
    const st = await stat(file);
    expect(st.isFile()).toBe(true);

    const raw = await readFile(file, 'utf8');
    expect(raw.trim().startsWith('{')).toBe(true);

    const loaded = await loadUserConfig(dir);
    expect(loaded).toEqual(input);
  });

  it('throws a helpful error when JSON is invalid', async () => {
    const dir = await mkTmp();
    const file = join(dir, '.cc-sdd.json');
    await writeFile(file, '{ invalid json', 'utf8');
    await expect(loadUserConfig(dir)).rejects.toThrow(/Invalid JSON/);
  });
});
