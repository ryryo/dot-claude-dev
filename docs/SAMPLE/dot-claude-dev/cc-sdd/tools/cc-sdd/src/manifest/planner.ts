import type { ResolvedConfig } from '../cli/config.js';
import type { Manifest, ProcessedArtifact } from './processor.js';
import { processManifest } from './processor.js';
import { loadManifest } from './loader.js';
import { contextFromResolved } from '../template/fromResolved.js';

export const planFromManifest = (manifest: Manifest, resolved: ResolvedConfig): ProcessedArtifact[] => {
  const ctx = contextFromResolved(resolved);
  return processManifest(manifest, resolved.agent, ctx, resolved.resolvedOs);
};

export const planFromFile = async (manifestPath: string, resolved: ResolvedConfig): Promise<ProcessedArtifact[]> => {
  const manifest = await loadManifest(manifestPath);
  return planFromManifest(manifest, resolved);
};
