const CLAUDE_API_URL = 'https://claude.ai/v1/sessions';
const DEFAULT_MODEL = 'claude-sonnet-4-6';
const USER_AGENT =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36';

export interface CreateSessionInput {
  sessionKey: string;
  orgUuid: string;
  environmentId: string;
  repo: string;
  branch: string;
  prompt: string;
  model?: string;
  fetchImpl?: typeof fetch;
}

export type CreateSessionErrorCode =
  | 'missing-env'
  | 'invalid-input'
  | 'cookie-expired'
  | 'forbidden'
  | 'rate-limit'
  | 'upstream-error'
  | 'network';

export type CreateSessionResult =
  | { ok: true; sessionId: string; sessionUrl: string }
  | { ok: false; code: CreateSessionErrorCode; message: string };

export async function createClaudeWebSession(
  input: CreateSessionInput
): Promise<CreateSessionResult> {
  const { sessionKey, orgUuid, environmentId, repo, branch, prompt } = input;

  if (!sessionKey || !orgUuid || !environmentId) {
    return {
      ok: false,
      code: 'missing-env',
      message:
        'CLAUDE_SESSION_KEY / CLAUDE_ORG_UUID / CLAUDE_ENV_ID env が未設定です',
    };
  }

  if (!repo || !branch || !prompt) {
    return {
      ok: false,
      code: 'invalid-input',
      message: 'repo / branch / prompt は必須です',
    };
  }

  const fetchImpl = input.fetchImpl ?? fetch;
  const model = input.model ?? DEFAULT_MODEL;

  const body = {
    title: prompt.slice(0, 60),
    events: [
      {
        type: 'event',
        data: {
          uuid: crypto.randomUUID(),
          session_id: '',
          type: 'user',
          parent_tool_use_id: null,
          message: { role: 'user', content: prompt },
        },
      },
    ],
    environment_id: environmentId,
    session_context: {
      sources: [
        {
          type: 'git_repository',
          url: `https://github.com/${repo}`,
          revision: `refs/heads/${branch}`,
        },
      ],
      outcomes: [
        {
          type: 'git_repository',
          git_info: {
            type: 'github',
            repo,
            branches: [`claude/${branch}`],
          },
        },
      ],
      model,
    },
  };

  let response: Response;
  try {
    response = await fetchImpl(CLAUDE_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Cookie: `sessionKey=${sessionKey}`,
        'anthropic-version': '2023-06-01',
        'anthropic-beta': 'ccr-byoc-2025-07-29',
        'anthropic-client-feature': 'ccr',
        'x-organization-uuid': orgUuid,
        'User-Agent': USER_AGENT,
      },
      body: JSON.stringify(body),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, code: 'network', message: `network error: ${message}` };
  }

  if (response.status === 401) {
    return {
      ok: false,
      code: 'cookie-expired',
      message:
        'sessionKey が無効です。/refresh-claude-web-cookie を実行してください',
    };
  }
  if (response.status === 403) {
    return {
      ok: false,
      code: 'forbidden',
      message: 'claude.ai が 403 を返しました (Cloudflare or organization 制限の可能性)',
    };
  }
  if (response.status === 429) {
    return {
      ok: false,
      code: 'rate-limit',
      message: 'claude.ai から 429 (rate limit) が返りました',
    };
  }

  if (!response.ok) {
    const detail = await safeReadErrorMessage(response);
    return {
      ok: false,
      code: 'upstream-error',
      message: `claude.ai upstream error (status=${response.status})${detail ? `: ${detail}` : ''}`,
    };
  }

  let session: { id?: unknown };
  try {
    session = (await response.json()) as { id?: unknown };
  } catch {
    return {
      ok: false,
      code: 'upstream-error',
      message: 'claude.ai のレスポンスを JSON としてパースできませんでした',
    };
  }

  if (typeof session.id !== 'string' || session.id.length === 0) {
    return {
      ok: false,
      code: 'upstream-error',
      message: 'claude.ai のレスポンスに id フィールドがありません',
    };
  }

  return {
    ok: true,
    sessionId: session.id,
    sessionUrl: `https://claude.ai/code/${session.id}`,
  };
}

async function safeReadErrorMessage(response: Response): Promise<string | null> {
  try {
    const data = (await response.json()) as { error?: unknown };
    if (typeof data.error === 'string') return data.error;
    if (data.error && typeof data.error === 'object' && 'message' in data.error) {
      const m = (data.error as { message?: unknown }).message;
      if (typeof m === 'string') return m;
    }
    return null;
  } catch {
    try {
      const text = await response.text();
      return text.slice(0, 200) || null;
    } catch {
      return null;
    }
  }
}
