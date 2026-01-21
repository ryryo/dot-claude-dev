import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import type { UserConfig } from './config.js';

export const CONFIG_FILE = '.cc-sdd.json';

export const resolveConfigPath = (cwd: string): string => join(cwd, CONFIG_FILE);

export const loadUserConfig = async (cwd: string): Promise<UserConfig> => {
  const file = resolveConfigPath(cwd);
  try {
    const raw = await readFile(file, 'utf8');
    try {
      const parsed = JSON.parse(raw) as UserConfig;
      return parsed ?? {};
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      throw new Error(`Invalid JSON in ${CONFIG_FILE}: ${msg}`);
    }
  } catch (e: any) {
    if (e && (e.code === 'ENOENT' || e.code === 'ENOTDIR')) return {};
    throw e;
  }
};

export const saveUserConfig = async (cwd: string, cfg: UserConfig): Promise<void> => {
  const file = resolveConfigPath(cwd);
  const json = JSON.stringify(cfg, null, 2) + '\n';
  await writeFile(file, json, 'utf8');
};
