import { describe, it, expect, vi, beforeEach } from 'vitest';

import {
  createClaudeWebSession,
  type CreateSessionInput,
} from '../../lib/claude-web-client';

const baseInput: CreateSessionInput = {
  sessionKey: 'sk-ant-sid02-test-key',
  orgUuid: '72f15ec8-6c9f-4c94-9014-5021153382bb',
  environmentId: 'env_01RqJFrxgn6poGNpyCTFWHh5',
  repo: 'octocat/hello-world',
  branch: 'main',
  prompt: 'タスクを実行してください',
};

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    status: init.status ?? 200,
    headers: { 'Content-Type': 'application/json', ...(init.headers ?? {}) },
  });
}

describe('createClaudeWebSession', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('1. missing-env: sessionKey が空なら code=missing-env を返し fetch を呼ばない', async () => {
    const fetchImpl = vi.fn();
    const result = await createClaudeWebSession({
      ...baseInput,
      sessionKey: '',
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.code).toBe('missing-env');
      expect(result.message).toMatch(/CLAUDE_SESSION_KEY|CLAUDE_ORG_UUID|CLAUDE_ENV_ID/);
    }
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it('2. invalid-input: repo が空なら code=invalid-input を返し fetch を呼ばない', async () => {
    const fetchImpl = vi.fn();
    const result = await createClaudeWebSession({
      ...baseInput,
      repo: '',
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.code).toBe('invalid-input');
    }
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it('3. happy path: 200 で id を受け取って ok:true と sessionUrl を返す', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({ id: 'session_xyz' }));

    const result = await createClaudeWebSession({
      ...baseInput,
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.sessionId).toBe('session_xyz');
      expect(result.sessionUrl).toBe('https://claude.ai/code/session_xyz');
    }

    expect(fetchImpl).toHaveBeenCalledTimes(1);
    const [url, init] = fetchImpl.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('https://claude.ai/v1/sessions');
    expect(init.method).toBe('POST');

    const headers = init.headers as Record<string, string>;
    expect(headers['Cookie']).toBe('sessionKey=sk-ant-sid02-test-key');
    expect(headers['anthropic-version']).toBe('2023-06-01');
    expect(headers['anthropic-beta']).toBe('ccr-byoc-2025-07-29');
    expect(headers['anthropic-client-feature']).toBe('ccr');
    expect(headers['x-organization-uuid']).toBe('72f15ec8-6c9f-4c94-9014-5021153382bb');
    expect(headers['Content-Type']).toBe('application/json');
    expect(headers['User-Agent']).toMatch(/Chrome/);

    const body = JSON.parse(init.body as string);
    expect(body.environment_id).toBe('env_01RqJFrxgn6poGNpyCTFWHh5');
    expect(body.events).toHaveLength(1);
    expect(body.events[0].data.uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
    expect(body.events[0].data.session_id).toBe('');
    expect(body.events[0].data.type).toBe('user');
    expect(body.events[0].data.message).toEqual({ role: 'user', content: 'タスクを実行してください' });
    expect(body.session_context.sources[0]).toEqual({
      type: 'git_repository',
      url: 'https://github.com/octocat/hello-world',
      revision: 'refs/heads/main',
    });
    expect(body.session_context.outcomes[0].git_info).toEqual({
      type: 'github',
      repo: 'octocat/hello-world',
      branches: ['claude/main'],
    });
    expect(body.session_context.model).toBe('claude-sonnet-4-6');
  });

  it('4. cookie-expired: 401 が返ったら code=cookie-expired', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      jsonResponse({ error: { message: 'unauthorized' } }, { status: 401 })
    );

    const result = await createClaudeWebSession({
      ...baseInput,
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.code).toBe('cookie-expired');
      expect(result.message).toMatch(/refresh-claude-web-cookie/);
    }
  });

  it('5. forbidden: 403 が返ったら code=forbidden', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      jsonResponse({ error: 'cf-block' }, { status: 403 })
    );

    const result = await createClaudeWebSession({
      ...baseInput,
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.code).toBe('forbidden');
    }
  });

  it('6. rate-limit: 429 が返ったら code=rate-limit', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      jsonResponse({ error: 'too many requests' }, { status: 429 })
    );

    const result = await createClaudeWebSession({
      ...baseInput,
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.code).toBe('rate-limit');
    }
  });

  it('7. network throw: fetch が throw したら code=network', async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new TypeError('network down'));

    const result = await createClaudeWebSession({
      ...baseInput,
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.code).toBe('network');
      expect(result.message).toMatch(/network down/);
    }
  });
});
