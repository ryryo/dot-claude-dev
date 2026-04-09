import type {
  GitHubContent,
  GitHubRepo,
  ProjectConfig,
  ProjectsConfig,
  RepoError,
} from '../lib/types';

const project: ProjectConfig = {
  name: 'dot-claude-dev',
  repo: 'ryryo/dot-claude-dev',
};

const config: ProjectsConfig = {
  projects: [project],
};

const repo: GitHubRepo = {
  id: 1,
  name: 'dot-claude-dev',
  full_name: 'ryryo/dot-claude-dev',
  private: false,
  description: 'Codex dashboard',
  updated_at: '2026-04-09T00:00:00Z',
  html_url: 'https://github.com/ryryo/dot-claude-dev',
};

const content: GitHubContent = {
  name: 'docs',
  path: 'docs',
  type: 'dir',
  sha: 'abc123',
};

const repoError: RepoError = {
  repo: 'ryryo/dot-claude-dev',
  message: 'Failed to fetch repository contents',
};

const legacyProject: ProjectConfig = {
  name: 'dot-claude-dev',
  // @ts-expect-error ProjectConfig should no longer accept path.
  path: '/Users/example/dot-claude-dev',
};

void config;
void repo;
void content;
void repoError;
void legacyProject;
