import { NextResponse } from 'next/server';

import { createClaudeWebSession } from '@/lib/claude-web-client';

export const runtime = 'nodejs';

interface LaunchRequestBody {
  repo?: string;
  branch?: string;
  prompt?: string;
}

export async function POST(req: Request) {
  let body: LaunchRequestBody;
  try {
    body = (await req.json()) as LaunchRequestBody;
  } catch {
    return NextResponse.json({ error: '不正な JSON です' }, { status: 400 });
  }

  const { repo, branch, prompt } = body;
  if (!repo || !branch || !prompt) {
    return NextResponse.json(
      { error: 'repo / branch / prompt は必須です' },
      { status: 400 }
    );
  }

  const sessionKey = process.env.CLAUDE_SESSION_KEY ?? '';
  const orgUuid = process.env.CLAUDE_ORG_UUID ?? '';
  const environmentId = process.env.CLAUDE_ENV_ID ?? '';

  const result = await createClaudeWebSession({
    sessionKey,
    orgUuid,
    environmentId,
    repo,
    branch,
    prompt,
  });

  if (result.ok) {
    return NextResponse.json({
      sessionId: result.sessionId,
      sessionUrl: result.sessionUrl,
    });
  }

  switch (result.code) {
    case 'missing-env':
      return NextResponse.json({ error: result.message }, { status: 500 });
    case 'invalid-input':
      return NextResponse.json({ error: result.message }, { status: 400 });
    case 'rate-limit':
      return NextResponse.json({ error: result.message }, { status: 429 });
    case 'cookie-expired':
      return NextResponse.json(
        { error: result.message, cookieExpired: true },
        { status: 401 }
      );
    case 'forbidden':
    case 'network':
    case 'upstream-error':
    default:
      return NextResponse.json({ error: result.message }, { status: 502 });
  }
}
