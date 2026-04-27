import { NextResponse } from 'next/server';

import { fetchFileContent } from '@/lib/github';
import type { TasksJsonV3 } from '@/lib/types';

// GitHub owner names: must start with alphanumeric, may contain hyphens/dots/underscores
const OWNER_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
// GitHub repo names: may start with dot (e.g. .github), no slashes or URL metacharacters
const REPO_PATTERN = /^[A-Za-z0-9._-]+$/;
const SLUG_PATTERN = /^[A-Za-z0-9_-]+$/;

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const owner = searchParams.get('owner')?.trim();
  const repo = searchParams.get('repo')?.trim();
  const slug = searchParams.get('slug')?.trim();

  if (!owner || !repo || !slug) {
    return NextResponse.json(
      { error: 'owner, repo, slug are required' },
      { status: 400 },
    );
  }

  if (!OWNER_PATTERN.test(owner) || !REPO_PATTERN.test(repo)) {
    return NextResponse.json({ error: 'invalid owner or repo' }, { status: 400 });
  }

  if (!SLUG_PATTERN.test(slug)) {
    return NextResponse.json({ error: 'invalid slug' }, { status: 400 });
  }

  const path = `docs/PLAN/${slug}/tasks.json`;

  let raw: string;
  try {
    raw = await fetchFileContent(owner, repo, path);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'unknown';
    // fetchFileContent throws "Failed to fetch file at {path}: {status}" — match the trailing status number
    if (/:\s*404$/.test(message)) {
      return NextResponse.json({ error: 'tasks.json not found' }, { status: 404 });
    }
    return NextResponse.json({ error: message }, { status: 502 });
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return NextResponse.json({ error: 'invalid JSON' }, { status: 422 });
  }

  if (
    typeof parsed !== 'object' ||
    parsed === null ||
    (parsed as { schemaVersion?: unknown }).schemaVersion !== 3
  ) {
    return NextResponse.json(
      { error: 'tasks.json is not v3 (schemaVersion === 3 required)' },
      { status: 422 },
    );
  }

  return NextResponse.json(parsed as TasksJsonV3);
}
