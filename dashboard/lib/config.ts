import fs from 'fs';
import path from 'path';
import { parse } from 'yaml';

import type { ProjectsConfig } from './types';

export function loadProjectsConfig(): ProjectsConfig {
  const configPath = path.join(process.cwd(), 'projects.yaml');
  const content = fs.readFileSync(configPath, 'utf-8');

  return parse(content) as ProjectsConfig;
}
