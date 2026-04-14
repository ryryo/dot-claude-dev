import { beforeEach, describe, expect, it, vi } from 'vitest';

import { GET } from '../app/api/plans/tasks/route';
import { fetchFileContent } from '../lib/github';
import type { TasksJsonV2 } from '../lib/types';

vi.mock('@/lib/github', () => ({
  fetchFileContent: vi.fn(),
}));

describe('GET /api/plans/tasks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('クエリが欠落しているとき 400 を返す', async () => {
    const response = await GET(new Request('http://localhost/api/plans/tasks?owner=octocat&repo='));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      error: 'owner, repo, slug are required',
    });
    expect(fetchFileContent).not.toHaveBeenCalled();
  });

  it('不正な slug のとき 400 を返す', async () => {
    const response = await GET(
      new Request('http://localhost/api/plans/tasks?owner=octocat&repo=hello-world&slug=../etc/passwd'),
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ error: 'invalid slug' });
    expect(fetchFileContent).not.toHaveBeenCalled();
  });

  it('不正な owner/repo のとき 400 を返す', async () => {
    const response = await GET(
      new Request(
        'http://localhost/api/plans/tasks?owner=o&repo=r/contents/other/tasks.json%23&slug=feature',
      ),
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ error: 'invalid owner or repo' });
    expect(fetchFileContent).not.toHaveBeenCalled();
  });

  it('.github のようなドット始まりのリポジトリ名を許可する', async () => {
    vi.mocked(fetchFileContent).mockRejectedValueOnce(
      new Error('Failed to fetch file at docs/PLAN/feature/tasks.json: 404'),
    );

    const response = await GET(
      new Request('http://localhost/api/plans/tasks?owner=octocat&repo=.github&slug=feature'),
    );

    // fetchFileContent が呼ばれていること（バリデーションで弾かれていないこと）
    expect(fetchFileContent).toHaveBeenCalledWith('octocat', '.github', 'docs/PLAN/feature/tasks.json');
    expect(response.status).toBe(404);
  });

  it('tasks.json が 404 のとき 404 を返す', async () => {
    vi.mocked(fetchFileContent).mockRejectedValueOnce(
      new Error('Failed to fetch file at docs/PLAN/feature/tasks.json: 404'),
    );

    const response = await GET(
      new Request('http://localhost/api/plans/tasks?owner=octocat&repo=hello-world&slug=feature'),
    );

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({ error: 'tasks.json not found' });
    expect(fetchFileContent).toHaveBeenCalledWith(
      'octocat',
      'hello-world',
      'docs/PLAN/feature/tasks.json',
    );
  });

  it('JSON の parse に失敗したとき 422 を返す', async () => {
    vi.mocked(fetchFileContent).mockResolvedValueOnce('{invalid json');

    const response = await GET(
      new Request('http://localhost/api/plans/tasks?owner=octocat&repo=hello-world&slug=feature'),
    );

    expect(response.status).toBe(422);
    await expect(response.json()).resolves.toEqual({ error: 'invalid JSON' });
  });

  it('schemaVersion=1 のとき 422 を返す', async () => {
    vi.mocked(fetchFileContent).mockResolvedValueOnce(
      JSON.stringify({ schemaVersion: 1, status: 'in-progress' }),
    );

    const response = await GET(
      new Request('http://localhost/api/plans/tasks?owner=octocat&repo=hello-world&slug=feature'),
    );

    expect(response.status).toBe(422);
    await expect(response.json()).resolves.toEqual({
      error: 'tasks.json is not v2 (schemaVersion >= 2 required)',
    });
  });

  it('schemaVersion=2 のとき tasks.json を返す', async () => {
    const tasksJson: TasksJsonV2 = {
      schemaVersion: 2,
      spec: {
        slug: 'feature',
        title: 'Feature Spec',
        summary: 'Summary',
        createdDate: '2026-04-14',
        specPath: 'spec.md',
      },
      status: 'in-progress',
      reviewChecked: false,
      progress: {
        completed: 1,
        total: 2,
      },
      preflight: [],
      gates: [
        {
          id: 'G1',
          title: 'Gate 1',
          description: 'desc',
          dependencies: [],
          passCondition: 'done',
        },
      ],
      todos: [
        {
          id: 'T1',
          gate: 'G1',
          title: 'Task 1',
          description: 'desc',
          tdd: false,
          dependencies: [],
          affectedFiles: [],
          impl: 'impl',
          relatedIssues: [],
          steps: [
            {
              kind: 'impl',
              title: 'Implement',
              checked: true,
            },
          ],
        },
      ],
      metadata: {
        createdAt: '2026-04-14T00:00:00Z',
        totalGates: 1,
        totalTodos: 1,
      },
    };

    vi.mocked(fetchFileContent).mockResolvedValueOnce(JSON.stringify(tasksJson));

    const response = await GET(
      new Request('http://localhost/api/plans/tasks?owner=octocat&repo=hello-world&slug=feature'),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(tasksJson);
  });
});
