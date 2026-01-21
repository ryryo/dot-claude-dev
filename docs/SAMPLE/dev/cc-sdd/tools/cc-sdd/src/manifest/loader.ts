import { readFile } from 'node:fs/promises';
import type { Manifest } from './processor.js';

export const loadManifest = async (filePath: string): Promise<Manifest> => {
  let raw: string;
  try {
    raw = await readFile(filePath, 'utf8');
  } catch (e: any) {
    if (e && e.code === 'ENOENT') throw new Error(`Manifest not found: ${filePath}`);
    throw e;
  }

  let json: unknown;
  try {
    json = JSON.parse(raw);
  } catch (e: any) {
    const msg = e?.message ?? String(e);
    throw new Error(`Invalid JSON in manifest: ${msg}`);
  }

  if (!json || typeof json !== 'object') throw new Error('Manifest must be an object');
  const m = json as Manifest;
  if (typeof (m as any).version !== 'number') throw new Error('Manifest.version must be a number');
  if (!Array.isArray((m as any).artifacts)) throw new Error('Manifest.artifacts must be an array');
  return m;
};
