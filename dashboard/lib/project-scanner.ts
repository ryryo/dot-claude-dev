import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

import { parsePlanFile } from './plan-parser';
import type { PlanFile, ProjectsConfig } from './types';

export function scanProjectPlans(projectPath: string, projectName: string): PlanFile[] {
  const planDir = join(projectPath, 'docs', 'PLAN');
  const planPaths = collectPlanPaths(planDir);

  return planPaths.flatMap((filePath) => {
    try {
      const content = readFileSync(filePath, 'utf-8');
      return [parsePlanFile(content, filePath, projectName)];
    } catch {
      return [];
    }
  });
}

export function scanAllProjects(config: ProjectsConfig): PlanFile[] {
  return config.projects.flatMap((project) => scanProjectPlans(project.path, project.name));
}

function collectPlanPaths(planDir: string): string[] {
  try {
    return readdirSync(planDir, { withFileTypes: true })
      .sort((left, right) => left.name.localeCompare(right.name))
      .flatMap((entry) => {
        if (entry.isFile() && entry.name.endsWith('.md')) {
          return [join(planDir, entry.name)];
        }

        if (entry.isDirectory()) {
          return resolveDirectoryModePlan(planDir, entry.name);
        }

        return [];
      });
  } catch {
    return [];
  }
}

function resolveDirectoryModePlan(planDir: string, directoryName: string): string[] {
  const directoryPath = join(planDir, directoryName);
  const specPath = join(directoryPath, 'spec.md');

  try {
    const nestedEntries = readdirSync(directoryPath, { withFileTypes: true });
    return nestedEntries.some((entry) => entry.isFile() && entry.name === 'spec.md') ? [specPath] : [];
  } catch {
    return [];
  }
}
