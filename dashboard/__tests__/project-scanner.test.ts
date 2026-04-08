import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import { join } from 'node:path';

import { describe, expect, it, afterEach, beforeEach } from 'vitest';

import { scanAllProjects, scanProjectPlans } from '../lib/project-scanner';
import type { ProjectsConfig } from '../lib/types';

let tmpDir: string;

beforeEach(() => {
  tmpDir = mkdtempSync(join(os.tmpdir(), 'scanner-test-'));
});

afterEach(() => {
  rmSync(tmpDir, { recursive: true, force: true });
});

describe('project-scanner', () => {
  it('指定パスの docs/PLAN/ から .md ファイルを収集する', () => {
    const projectPath = createProject(tmpDir, 'alpha');
    writePlanFile(projectPath, 'overview.md', '# Overview\n\nBody\n');
    writePlanFile(projectPath, 'release.md', '# Release Plan\n\nBody\n');
    writePlanFile(projectPath, 'notes.txt', 'ignore me');

    const result = scanProjectPlans(projectPath, 'alpha');

    expect(result).toHaveLength(2);
    expect(result.map((plan) => plan.fileName)).toEqual(['overview.md', 'release.md']);
    expect(result.map((plan) => plan.title)).toEqual(['Overview', 'Release Plan']);
    expect(result.map((plan) => plan.projectName)).toEqual(['alpha', 'alpha']);
  });

  it('docs/PLAN/ が存在しないプロジェクトは空配列を返す', () => {
    const projectPath = createProject(tmpDir, 'no-plan');

    const result = scanProjectPlans(projectPath, 'no-plan');

    expect(result).toEqual([]);
  });

  it('パス不正などのアクセスエラーはスキップして空配列を返す', () => {
    expect(() => scanProjectPlans('\0invalid-path', 'broken')).not.toThrow();
    expect(scanProjectPlans('\0invalid-path', 'broken')).toEqual([]);
  });

  it('docs/PLAN/{slug}/spec.md 形式も検出する', () => {
    const projectPath = createProject(tmpDir, 'dir-mode');
    writeDirectoryPlanFile(projectPath, 'feature-auth', '# Auth Spec\n\nBody\n');

    const result = scanProjectPlans(projectPath, 'dir-mode');

    expect(result).toHaveLength(1);
    expect(result[0]?.fileName).toBe('spec.md');
    expect(result[0]?.title).toBe('Auth Spec');
    expect(result[0]?.filePath).toBe(join(projectPath, 'docs', 'PLAN', 'feature-auth', 'spec.md'));
  });

  it('全プロジェクトの PLAN を統合して返す', () => {
    const alphaPath = createProject(tmpDir, 'alpha');
    const betaPath = createProject(tmpDir, 'beta');

    writePlanFile(alphaPath, 'overview.md', '# Alpha Overview\n\nBody\n');
    writeDirectoryPlanFile(betaPath, 'feature-auth', '# Beta Auth\n\nBody\n');

    const config: ProjectsConfig = {
      projects: [
        { name: 'alpha', path: alphaPath },
        { name: 'beta', path: betaPath },
      ],
    };

    const result = scanAllProjects(config);

    expect(result).toHaveLength(2);
    expect(result.map((plan) => `${plan.projectName}:${plan.title}`)).toEqual([
      'alpha:Alpha Overview',
      'beta:Beta Auth',
    ]);
  });
});

function createProject(baseDir: string, name: string): string {
  const projectPath = join(baseDir, name);
  mkdirSync(projectPath, { recursive: true });
  return projectPath;
}

function writePlanFile(projectPath: string, fileName: string, content: string): void {
  const planDir = join(projectPath, 'docs', 'PLAN');
  mkdirSync(planDir, { recursive: true });
  writeFileSync(join(planDir, fileName), content);
}

function writeDirectoryPlanFile(projectPath: string, slug: string, content: string): void {
  const planDir = join(projectPath, 'docs', 'PLAN', slug);
  mkdirSync(planDir, { recursive: true });
  writeFileSync(join(planDir, 'spec.md'), content);
}
