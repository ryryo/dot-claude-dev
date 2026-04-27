import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { fetchFileContent, fetchPlanFiles, fetchUserRepos } from '../lib/github';
import type { GitHubContent, GitHubRepo, TasksJsonV3 } from '../lib/types';

describe('github', () => {
  const originalToken = process.env.GITHUB_TOKEN;

  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    if (originalToken === undefined) {
      delete process.env.GITHUB_TOKEN;
    } else {
      process.env.GITHUB_TOKEN = originalToken;
    }
  });

  it('GITHUB_TOKEN が未設定のときエラーを投げる', async () => {
    delete process.env.GITHUB_TOKEN;

    await expect(fetchUserRepos()).rejects.toThrow('GITHUB_TOKEN is not set');
    expect(fetch).not.toHaveBeenCalled();
  });

  it('docs/PLAN が 404 のとき空配列を返す', async () => {
    process.env.GITHUB_TOKEN = 'test-token';
    vi.mocked(fetch).mockResolvedValueOnce(
      createJsonResponse([], { status: 404, statusText: 'Not Found' })
    );

    await expect(fetchPlanFiles('octocat', 'hello-world')).resolves.toEqual([]);
    expect(fetch).toHaveBeenCalledWith(
      'https://api.github.com/repos/octocat/hello-world/contents/docs/PLAN',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
          Accept: 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
        }),
        next: expect.objectContaining({ revalidate: 300 }),
      })
    );
  });

  it('base64 コンテンツを UTF-8 としてデコードする', async () => {
    process.env.GITHUB_TOKEN = 'test-token';
    vi.mocked(fetch).mockResolvedValueOnce(
      createJsonResponse({
        content: Buffer.from('# こんにちは\n', 'utf-8').toString('base64'),
        encoding: 'base64',
      })
    );

    await expect(fetchFileContent('octocat', 'hello-world', 'docs/PLAN/spec.md')).resolves.toBe(
      '# こんにちは\n'
    );
  });

  it('v3 tasks.json を持つディレクトリエントリのみを返す（.md ファイルエントリは無視）', async () => {
    process.env.GITHUB_TOKEN = 'test-token';

    const contents: GitHubContent[] = [
      { name: 'feature-beta', path: 'docs/PLAN/feature-beta', type: 'dir', sha: '2' },
      { name: '250101_alpha.md', path: 'docs/PLAN/250101_alpha.md', type: 'file', sha: '1' },
    ];

    const tasksJson: TasksJsonV3 = makeV3Sample('feature-beta', 'Beta Spec');

    vi.mocked(fetch)
      .mockResolvedValueOnce(createJsonResponse(contents))
      // dir entry: tasks.json
      .mockResolvedValueOnce(
        createJsonResponse({
          content: Buffer.from(JSON.stringify(tasksJson), 'utf-8').toString('base64'),
          encoding: 'base64',
        })
      )
      // dir entry: spec.md
      .mockResolvedValueOnce(
        createJsonResponse({
          content: Buffer.from('# Beta Spec\n', 'utf-8').toString('base64'),
          encoding: 'base64',
        })
      );

    const result = await fetchPlanFiles('octocat', 'hello-world');

    expect(result).toHaveLength(1);
    expect(result[0].filePath).toBe('docs/PLAN/feature-beta/spec.md');
    expect(result[0].title).toBe('Beta Spec');
    expect(result[0].projectName).toBe('octocat/hello-world');
  });

  it('ディレクトリエントリの tasks.json が 404 ならスキップする', async () => {
    process.env.GITHUB_TOKEN = 'test-token';

    const contents: GitHubContent[] = [
      { name: 'feature-beta', path: 'docs/PLAN/feature-beta', type: 'dir', sha: '2' },
    ];

    vi.mocked(fetch)
      .mockResolvedValueOnce(createJsonResponse(contents))
      // tasks.json → 404
      .mockResolvedValueOnce(
        createJsonResponse({ message: 'Not Found' }, { status: 404, statusText: 'Not Found' })
      );

    await expect(fetchPlanFiles('octocat', 'hello-world')).resolves.toEqual([]);
  });

  it('ディレクトリエントリの tasks.json が 404 以外なら再 throw する', async () => {
    process.env.GITHUB_TOKEN = 'test-token';

    const contents: GitHubContent[] = [
      { name: 'feature-beta', path: 'docs/PLAN/feature-beta', type: 'dir', sha: '2' },
    ];

    vi.mocked(fetch)
      .mockResolvedValueOnce(createJsonResponse(contents))
      // tasks.json → 500
      .mockResolvedValueOnce(
        createJsonResponse(
          { message: 'Internal Server Error' },
          { status: 500, statusText: 'Internal Server Error' }
        )
      );

    await expect(fetchPlanFiles('octocat', 'hello-world')).rejects.toThrow(
      'Failed to fetch file at docs/PLAN/feature-beta/tasks.json: 500'
    );
  });

  it('ユーザーのリポジトリ一覧を取得する', async () => {
    process.env.GITHUB_TOKEN = 'test-token';
    const repos: GitHubRepo[] = [
      {
        id: 1,
        name: 'hello-world',
        full_name: 'octocat/hello-world',
        private: false,
        description: 'sample',
        updated_at: '2026-04-09T00:00:00Z',
        html_url: 'https://github.com/octocat/hello-world',
        default_branch: 'main',
      },
    ];

    vi.mocked(fetch).mockResolvedValueOnce(createJsonResponse(repos));

    await expect(fetchUserRepos()).resolves.toEqual(repos);
    expect(fetch).toHaveBeenCalledWith(
      'https://api.github.com/user/repos?per_page=100&sort=updated&type=all',
      expect.objectContaining({ next: expect.objectContaining({ revalidate: 300 }) })
    );
  });
});

function createJsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    statusText: 'OK',
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
}

function makeV3Sample(slug: string, title: string): TasksJsonV3 {
  return {
    schemaVersion: 3,
    spec: {
      slug,
      title,
      summary: '',
      createdDate: '2026-04-14',
      specPath: `docs/PLAN/${slug}/spec.md`,
    },
    status: 'in-progress',
    reviewChecked: false,
    progress: {
      gatesPassed: 0,
      gatesTotal: 1,
      currentGate: 'A',
      currentGateAC: { passed: 0, total: 1 },
    },
    preflight: [],
    gates: [
      {
        id: 'A',
        title: 'Gate A',
        summary: '',
        dependencies: [],
        goal: { what: '', why: '' },
        constraints: { must: [], mustNot: [] },
        acceptanceCriteria: [{ id: 'A.AC1', description: 'tested', checked: false }],
        todos: [],
        review: null,
        passed: false,
      },
    ],
    metadata: {
      createdAt: '2026-04-14T00:00:00Z',
      totalGates: 1,
      totalTodos: 0,
    },
  };
}
