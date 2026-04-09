import { NextResponse } from 'next/server';

import { fetchPlanFiles } from '@/lib/github';
import type { PlanFile, RepoError } from '@/lib/types';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const reposParam = searchParams.get('repos');

  if (!reposParam?.trim()) {
    return NextResponse.json({ plans: [], errors: [] });
  }

  const repos = reposParam
    .split(',')
    .map((repo) => repo.trim())
    .filter(Boolean);

  const results = await Promise.allSettled(
    repos.map(async (fullName) => {
      const slashIndex = fullName.indexOf('/');

      if (slashIndex === -1) {
        throw new Error(`Invalid repo format: ${fullName}`);
      }

      const owner = fullName.slice(0, slashIndex);
      const repo = fullName.slice(slashIndex + 1);

      return fetchPlanFiles(owner, repo);
    }),
  );

  const plans: PlanFile[] = [];
  const errors: RepoError[] = [];

  results.forEach((result, index) => {
    if (result.status === 'fulfilled') {
      plans.push(...result.value);
      return;
    }

    errors.push({
      repo: repos[index],
      message:
        result.reason instanceof Error ? result.reason.message : 'Unknown error',
    });
  });

  return NextResponse.json({ plans, errors });
}
