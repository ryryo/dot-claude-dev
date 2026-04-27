'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import type { TasksJsonV3 } from './types';

export type UseTasksJsonState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: TasksJsonV3 }
  | { status: 'error'; message: string };

export interface UseTasksJsonArgs {
  owner: string;
  repo: string;
  slug: string;
  enabled: boolean;
}

const cache = new Map<string, TasksJsonV3>();

function cacheKey(args: { owner: string; repo: string; slug: string }) {
  return `${args.owner}/${args.repo}#${args.slug}`;
}

export function clearTasksJsonCache() {
  cache.clear();
}

export function useTasksJson(
  args: UseTasksJsonArgs,
): { state: UseTasksJsonState; reload: () => void } {
  const { owner, repo, slug, enabled } = args;
  const key = cacheKey({ owner, repo, slug });

  const initial: UseTasksJsonState = cache.has(key)
    ? { status: 'success', data: cache.get(key)! }
    : { status: 'idle' };
  const [state, setState] = useState<UseTasksJsonState>(initial);
  const tickRef = useRef(0);

  const fetchOnce = useCallback(async () => {
    const ticket = ++tickRef.current;
    setState({ status: 'loading' });

    try {
      const params = new URLSearchParams({ owner, repo, slug });
      const res = await fetch(`/api/plans/tasks?${params.toString()}`);

      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        throw new Error(body.error ?? `HTTP ${res.status}`);
      }

      const data = (await res.json()) as TasksJsonV3;
      if (ticket !== tickRef.current) return;

      cache.set(key, data);
      setState({ status: 'success', data });
    } catch (error) {
      if (ticket !== tickRef.current) return;

      const message = error instanceof Error ? error.message : 'unknown error';
      setState({ status: 'error', message });
    }
  }, [owner, repo, slug, key]);

  useEffect(() => {
    if (!enabled) return;

    const cached = cache.get(key);
    if (cached) {
      setState({ status: 'success', data: cached });
      return;
    }

    void fetchOnce();
  }, [enabled, key, fetchOnce]);

  const reload = useCallback(() => {
    cache.delete(key);
    void fetchOnce();
  }, [key, fetchOnce]);

  return { state, reload };
}
