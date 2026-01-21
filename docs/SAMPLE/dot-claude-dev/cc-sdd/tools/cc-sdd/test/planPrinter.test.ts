import { describe, it, expect } from 'vitest';
import { summarizeProcessedArtifacts, formatProcessedArtifacts } from '../src/plan/printer';
import type { ProcessedArtifact } from '../src/manifest/processor';

describe('plan printer', () => {
  it('summarizes by type', () => {
    const items: ProcessedArtifact[] = [
      { id: 's1', source: { type: 'staticDir', from: 'a', toDir: 'b' } },
      { id: 'f1', source: { type: 'templateFile', from: 'a.tpl.md', toDir: 'b', outFile: 'a.md' } },
      { id: 'd1', source: { type: 'templateDir', fromDir: 'x', toDir: 'y' } },
    ];
    const s = summarizeProcessedArtifacts(items);
    expect(s.total).toBe(3);
    expect(s.byType.staticDir).toBe(1);
    expect(s.byType.templateFile).toBe(1);
    expect(s.byType.templateDir).toBe(1);
  });

  it('formats a human-readable plan', () => {
    const items: ProcessedArtifact[] = [
      { id: 's1', source: { type: 'staticDir', from: 'a', toDir: 'b' } },
      { id: 'f1', source: { type: 'templateFile', from: 'a.tpl.md', toDir: 'b', outFile: 'a.md' } },
      { id: 'd1', source: { type: 'templateDir', fromDir: 'x', toDir: 'y' } },
    ];
    const out = formatProcessedArtifacts(items);
    expect(out).toMatch(/Plan \(dry-run\)/);
    expect(out).toMatch(/Total: 3/);
    expect(out).toMatch(/staticDir: 1/);
    expect(out).toMatch(/templateFile: 1/);
    expect(out).toMatch(/templateDir: 1/);
    expect(out).toMatch(/\- \[staticDir\] s1: a -> b/);
    expect(out).toMatch(/\- \[templateFile\] f1: a\.tpl\.md -> b\/a\.md/);
    expect(out).toMatch(/\- \[templateDir\] d1: x -> y/);
  });
});
