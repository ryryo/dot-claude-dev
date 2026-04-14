import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, renderHook, waitFor } from '@testing-library/react';

import type { TasksJsonV2 } from '../lib/types';

function makeSample(slug = 'demo'): TasksJsonV2 {
  return {
    schemaVersion: 2,
    spec: {
      slug,
      title: 'デモ仕様',
      summary: 'summary',
      createdDate: '2026-04-14',
      specPath: 'spec.md',
    },
    status: 'in-progress',
    reviewChecked: false,
    progress: { completed: 1, total: 2 },
    preflight: [],
    gates: [],
    todos: [],
    metadata: {
      createdAt: '2026-04-14T00:00:00Z',
      totalGates: 0,
      totalTodos: 0,
    },
  };
}

type MockFetchResponse = {
  ok: boolean;
  status: number;
  json: () => Promise<unknown>;
};

function okResponse(data: TasksJsonV2): MockFetchResponse {
  return {
    ok: true,
    status: 200,
    json: async () => data,
  };
}

function errorResponse(status: number, error: string): MockFetchResponse {
  return {
    ok: false,
    status,
    json: async () => ({ error }),
  };
}

function createDeferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

async function loadHookModule() {
  return import('../lib/use-tasks-json');
}

beforeEach(() => {
  vi.resetModules();
  global.fetch = vi.fn() as typeof fetch;
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('useTasksJson', () => {
  it('enabled=false のとき fetch せず idle のまま', async () => {
    const { useTasksJson } = await loadHookModule();

    const { result } = renderHook(() =>
      useTasksJson({
        owner: 'openai',
        repo: 'dashboard',
        slug: 'plan-a',
        enabled: false,
      }),
    );

    expect(result.current!.state).toEqual({ status: 'idle' });
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('enabled=true 初回は loading を経て success になる', async () => {
    const sample = makeSample('plan-a');
    const deferred = createDeferred<MockFetchResponse>();
    vi.mocked(global.fetch).mockReturnValueOnce(
      deferred.promise as ReturnType<typeof fetch>,
    );

    const { useTasksJson } = await loadHookModule();
    const { result } = renderHook(() =>
      useTasksJson({
        owner: 'openai',
        repo: 'dashboard',
        slug: 'plan-a',
        enabled: true,
      }),
    );

    await waitFor(() => {
      expect(result.current!.state.status).toBe('loading');
    });

    deferred.resolve(okResponse(sample));

    await waitFor(() => {
      expect(result.current!.state).toEqual({ status: 'success', data: sample });
    });

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/plans/tasks?owner=openai&repo=dashboard&slug=plan-a',
    );
  });

  it('同じキーの 2 回目はキャッシュ命中で fetch せず即 success', async () => {
    const sample = makeSample('plan-a');
    vi.mocked(global.fetch).mockResolvedValueOnce(
      okResponse(sample) as Awaited<ReturnType<typeof fetch>>,
    );

    const { useTasksJson } = await loadHookModule();

    const first = renderHook(() =>
      useTasksJson({
        owner: 'openai',
        repo: 'dashboard',
        slug: 'plan-a',
        enabled: true,
      }),
    );

    await waitFor(() => {
      expect(first.result.current!.state).toEqual({
        status: 'success',
        data: sample,
      });
    });

    expect(global.fetch).toHaveBeenCalledTimes(1);
    first.unmount();

    const second = renderHook(() =>
      useTasksJson({
        owner: 'openai',
        repo: 'dashboard',
        slug: 'plan-a',
        enabled: true,
      }),
    );

    expect(second.result.current!.state).toEqual({
      status: 'success',
      data: sample,
    });
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it('404 エラー時は error 状態とメッセージを返す', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce(
      errorResponse(404, 'tasks.json not found') as Awaited<ReturnType<typeof fetch>>,
    );

    const { useTasksJson } = await loadHookModule();
    const { result } = renderHook(() =>
      useTasksJson({
        owner: 'openai',
        repo: 'dashboard',
        slug: 'missing-plan',
        enabled: true,
      }),
    );

    await waitFor(() => {
      expect(result.current!.state).toEqual({
        status: 'error',
        message: 'tasks.json not found',
      });
    });
  });

  it('reload は cache をクリアして再 fetch する', async () => {
    const firstSample = makeSample('plan-a');
    const reloadedSample = {
      ...makeSample('plan-a'),
      progress: { completed: 2, total: 2 },
      metadata: {
        createdAt: '2026-04-14T00:00:00Z',
        totalGates: 1,
        totalTodos: 1,
      },
    } satisfies TasksJsonV2;
    const reloadDeferred = createDeferred<MockFetchResponse>();

    vi.mocked(global.fetch)
      .mockResolvedValueOnce(
        okResponse(firstSample) as Awaited<ReturnType<typeof fetch>>,
      )
      .mockReturnValueOnce(reloadDeferred.promise as ReturnType<typeof fetch>);

    const { useTasksJson } = await loadHookModule();
    const { result } = renderHook(() =>
      useTasksJson({
        owner: 'openai',
        repo: 'dashboard',
        slug: 'plan-a',
        enabled: true,
      }),
    );

    await waitFor(() => {
      expect(result.current!.state).toEqual({
        status: 'success',
        data: firstSample,
      });
    });

    act(() => {
      result.current!.reload();
    });

    await waitFor(() => {
      expect(result.current!.state.status).toBe('loading');
    });

    reloadDeferred.resolve(okResponse(reloadedSample));

    await waitFor(() => {
      expect(result.current!.state).toEqual({
        status: 'success',
        data: reloadedSample,
      });
    });

    expect(global.fetch).toHaveBeenCalledTimes(2);
  });
});
