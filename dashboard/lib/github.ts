import { loadPlanFromTasksJson } from './plan-json-loader';
import { parsePlanFile } from './plan-parser';
import type { GitHubContent, GitHubRepo, PlanFile, TasksJsonV2 } from './types';

const GITHUB_API_BASE = 'https://api.github.com';
const GITHUB_REVALIDATE_SECONDS = 300;
export const GITHUB_CACHE_TAG = 'github';

type GitHubRequestInit = RequestInit & {
  next: {
    revalidate: number;
    tags: string[];
  };
};

function getHeaders(): HeadersInit {
  const token = process.env.GITHUB_TOKEN;

  if (!token) {
    throw new Error('GITHUB_TOKEN is not set');
  }

  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
  };
}

function getRequestOptions(): GitHubRequestInit {
  return {
    headers: getHeaders(),
    next: { revalidate: GITHUB_REVALIDATE_SECONDS, tags: [GITHUB_CACHE_TAG] },
  };
}

/** ユーザーの全リポジトリ一覧を取得 */
export async function fetchUserRepos(): Promise<GitHubRepo[]> {
  const response = await fetch(
    `${GITHUB_API_BASE}/user/repos?per_page=100&sort=updated&type=all`,
    getRequestOptions()
  );

  if (!response.ok) {
    throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<GitHubRepo[]>;
}

/** リポジトリの docs/PLAN に含まれる全 PlanFile を取得 */
export async function fetchPlanFiles(owner: string, repo: string): Promise<PlanFile[]> {
  const contents = await fetchContents(owner, repo, 'docs/PLAN');

  if (contents.length === 0) {
    return [];
  }

  const projectName = `${owner}/${repo}`;
  const sorted = [...contents].sort((left, right) => left.name.localeCompare(right.name));

  const plans = await Promise.all(
    sorted.map(async (entry) => {
      if (entry.type === 'file' && entry.name.endsWith('.md')) {
        const content = await fetchFileContent(owner, repo, entry.path);
        return parsePlanFile(content, entry.path, projectName);
      }

      if (entry.type === 'dir') {
        const tasksJsonPath = `${entry.path}/tasks.json`;
        const specPath = `${entry.path}/spec.md`;

        // 1. tasks.json を試す（v2 対応）
        const v2Plan = await tryLoadV2(owner, repo, tasksJsonPath, specPath, projectName);
        if (v2Plan) {
          return v2Plan;
        }

        // 2. レガシー spec.md パス
        try {
          const content = await fetchFileContent(owner, repo, specPath);
          return parsePlanFile(content, specPath, projectName);
        } catch (error) {
          if (isFileNotFoundError(error)) {
            return null;
          }

          throw error;
        }
      }

      return null;
    })
  );

  return plans.filter((plan): plan is PlanFile => plan !== null);
}

function isFileNotFoundError(error: unknown): boolean {
  return (
    error instanceof Error &&
    error.message.includes('Failed to fetch file') &&
    error.message.includes('404')
  );
}

/**
 * ディレクトリ内容を取得する。
 *
 * GitHub Contents API は、リポジトリ自体が存在しない場合と `path` が存在しない場合の
 * どちらも 404 を返すため、この関数単体では区別できない。現状はどちらも空配列として扱う。
 */
async function fetchContents(owner: string, repo: string, path: string): Promise<GitHubContent[]> {
  const response = await fetch(
    `${GITHUB_API_BASE}/repos/${owner}/${repo}/contents/${path}`,
    getRequestOptions()
  );

  if (response.status === 404) {
    return [];
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch contents at ${path}: ${response.status}`);
  }

  return response.json() as Promise<GitHubContent[]>;
}

/** ファイルの内容を文字列として取得（base64 デコード） */
export async function fetchFileContent(owner: string, repo: string, path: string): Promise<string> {
  const response = await fetch(
    `${GITHUB_API_BASE}/repos/${owner}/${repo}/contents/${path}`,
    getRequestOptions()
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch file at ${path}: ${response.status}`);
  }

  const data = (await response.json()) as { content: string; encoding: string };
  return Buffer.from(data.content, 'base64').toString('utf-8');
}

/**
 * tasks.json を試行し、schemaVersion >= 2 なら PlanFile を返す。
 * v1 または 404 の場合は null を返してフォールバック。
 */
async function tryLoadV2(
  owner: string,
  repo: string,
  tasksJsonPath: string,
  specPath: string,
  projectName: string
): Promise<PlanFile | null> {
  let rawContent: string;
  try {
    rawContent = await fetchFileContent(owner, repo, tasksJsonPath);
  } catch (error) {
    if (isFileNotFoundError(error)) {
      return null;
    }
    throw error;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(rawContent);
  } catch {
    return null;
  }

  if (!isV2TasksJson(parsed)) {
    return null;
  }

  let specContent = '';
  try {
    specContent = await fetchFileContent(owner, repo, specPath);
  } catch {
    // spec.md が無い場合は空文字のまま
  }

  return loadPlanFromTasksJson(parsed, specPath, projectName, specContent);
}

function isV2TasksJson(value: unknown): value is TasksJsonV2 {
  if (typeof value !== 'object' || value === null) return false;
  const v = value as Record<string, unknown>;
  return typeof v.schemaVersion === 'number' && v.schemaVersion >= 2;
}
