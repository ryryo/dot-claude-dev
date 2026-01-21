import type { ProcessedArtifact } from '../manifest/processor.js';
import type { ResolvedConfig } from '../cli/config.js';

export type PlanSummary = {
  total: number;
  byType: Record<'staticDir' | 'templateFile' | 'templateDir', number>;
};

export const summarizeProcessedArtifacts = (items: ProcessedArtifact[]): PlanSummary => {
  const byType = { staticDir: 0, templateFile: 0, templateDir: 0 } as PlanSummary['byType'];
  for (const it of items) {
    byType[it.source.type]++;
  }
  return { total: items.length, byType };
};

const lineFor = (it: ProcessedArtifact): string => {
  if (it.source.type === 'staticDir') {
    const { from, toDir } = it.source;
    return `- [staticDir] ${it.id}: ${from} -> ${toDir}`;
  }
  if (it.source.type === 'templateFile') {
    const { from, toDir, outFile } = it.source;
    return `- [templateFile] ${it.id}: ${from} -> ${toDir}/${outFile}`;
  }
  const { fromDir, toDir } = it.source;
  return `- [templateDir] ${it.id}: ${fromDir} -> ${toDir}`;
};

export const formatProcessedArtifacts = (items: ProcessedArtifact[]): string => {
  const s = summarizeProcessedArtifacts(items);
  const header = [
    `Plan (dry-run)`,
    `Total: ${s.total}`,
    `  - staticDir: ${s.byType.staticDir}`,
    `  - templateFile: ${s.byType.templateFile}`,
    `  - templateDir: ${s.byType.templateDir}`,
  ].join('\n');
  const body = items.map(lineFor).join('\n');
  return `${header}\n${body}`;
};
