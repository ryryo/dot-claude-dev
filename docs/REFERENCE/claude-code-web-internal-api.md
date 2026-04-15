# Claude Code Web — 内部 REST API リファレンス

調査日: 2026-04-15  
調査手法: Claude in Chrome MCP + fetch/XHR インターセプター + JS バンドル解析

---

## 結論

**`sessionKeyLC` Cookie + 正しいヘッダーで `POST /v1/sessions` → 200 を実証済み。**  
Vercel サーバーレス関数から `fetch` でセッションを作成できる（永続サーバー不要）。

> ⚠️ 非公開の内部 API。予告なく変更される可能性がある。

---

## 認証

### sessionKeyLC Cookie

すべての `/v1/*` エンドポイントはブラウザセッション Cookie で認証する。

| 項目 | 内容 |
|---|---|
| Cookie 名 | `sessionKeyLC` |
| HttpOnly | ❌（`document.cookie` から取得可能） |
| 失効条件 | ログアウト / パスワード変更 / セッション期限切れ |
| 取得方法 | ブラウザで claude.ai にログイン後、DevTools または `document.cookie` で取得 |

---

## 必須リクエストヘッダー

JS バンドル解析 + ブラウザ実行テストで確認済み（2026-04-15）。

| ヘッダー | 値 | 欠落時のエラー |
|---|---|---|
| `anthropic-version` | `2023-06-01` | `"anthropic-version: header is required"` |
| `anthropic-beta` | `ccr-byoc-2025-07-29` | `"no schema found for anthropic-beta header value"` |
| `anthropic-client-feature` | `ccr` | Web UI が常に付与（ccr = Claude Code Relay と思われる） |
| `x-organization-uuid` | `{org_uuid}` | 任意だが Web UI は常に付与 |

> `anthropic-beta: managed-agents-2026-04-01` は別スキーマ（GET の valid チェックには使えるが POST /v1/sessions は不可）。

---

## セッション作成

### 完全なリクエスト例

```http
POST https://claude.ai/v1/sessions
Cookie: sessionKeyLC=<value>
Content-Type: application/json
anthropic-version: 2023-06-01
anthropic-beta: ccr-byoc-2025-07-29
anthropic-client-feature: ccr
x-organization-uuid: <org_uuid>

{
  "title": "任意のタイトル",
  "events": [
    {
      "type": "event",
      "data": {
        "uuid": "<random-uuid>",
        "session_id": "",
        "type": "user",
        "parent_tool_use_id": null,
        "message": {
          "role": "user",
          "content": "YOUR_PROMPT"
        }
      }
    }
  ],
  "environment_id": "env_01AgnTYbWgkEvJy9tGzX87ej",
  "session_context": {
    "sources": [
      {
        "type": "git_repository",
        "url": "https://github.com/{owner}/{repo}",
        "revision": "refs/heads/{branch}"
      }
    ],
    "outcomes": [
      {
        "type": "git_repository",
        "git_info": {
          "type": "github",
          "repo": "{owner}/{repo}",
          "branches": ["claude/{suggested-branch}"]
        }
      }
    ],
    "model": "claude-sonnet-4-6"
  }
}
```

レスポンスの `id` フィールドがセッション ID。`https://claude.ai/code/{id}` でアクセス可能。

### フィールド説明

| フィールド | 説明 |
|---|---|
| `title` | サイドバーに表示されるセッション名（任意の文字列） |
| `events[].data.uuid` | クライアント生成のランダム UUID（`crypto.randomUUID()` で可） |
| `events[].data.session_id` | 新規作成時は `""` |
| `events[].data.type` | ユーザー最初のメッセージなので `"user"` |
| `environment_id` | 実行環境 ID（アカウント固定。下記エンドポイントで取得） |
| `session_context.sources[].revision` | `refs/heads/{branch}` 形式 |
| `session_context.outcomes[].git_info.branches` | Claude の作業ブランチ候補（`claude/` プレフィックス推奨） |
| `session_context.model` | `"claude-sonnet-4-6"` 等 |

### タイトル自動生成（任意）

```http
POST https://claude.ai/api/organizations/{org_id}/dust/generate_title_and_branch
Content-Type: application/json

{"first_session_message": "YOUR_PROMPT", "title_style": "default"}
```

スキップして `title` を直接指定しても動作する。

---

## セッション有効性チェック

```http
GET https://claude.ai/v1/sessions
anthropic-version: 2023-06-01
anthropic-beta: managed-agents-2026-04-01
Cookie: sessionKeyLC=<value>
```

- **200** `{"data": []}` → Cookie 有効
- **401** → Cookie 期限切れ

> GET では `managed-agents-2026-04-01` でも動く。POST は `ccr-byoc-2025-07-29` が必須。

---

## Vercel サーバーレス実装サンプル

Cookie を Vercel KV に保存し、サーバーレス関数から動的に読んでセッション作成する構成。

```typescript
// app/api/sessions/launch/route.ts
import { kv } from '@vercel/kv'

const ORG_UUID = process.env.CLAUDE_ORG_UUID!
const ENV_ID   = process.env.CLAUDE_ENV_ID!   // env_01AgnTYbWgkEvJy9tGzX87ej

export async function POST(req: Request) {
  const { repo, branch, prompt } = await req.json()

  const sessionKeyLC = await kv.get<string>('sessionKeyLC')
  if (!sessionKeyLC) {
    return Response.json({ error: 'Cookie not set. Run /refresh-claude-web-cookie' }, { status: 500 })
  }

  const res = await fetch('https://claude.ai/v1/sessions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Cookie': `sessionKeyLC=${sessionKeyLC}`,
      'anthropic-version': '2023-06-01',
      'anthropic-beta': 'ccr-byoc-2025-07-29',
      'anthropic-client-feature': 'ccr',
      'x-organization-uuid': ORG_UUID,
    },
    body: JSON.stringify({
      title: prompt.slice(0, 60),
      events: [{
        type: 'event',
        data: {
          uuid: crypto.randomUUID(),
          session_id: '',
          type: 'user',
          parent_tool_use_id: null,
          message: { role: 'user', content: prompt }
        }
      }],
      environment_id: ENV_ID,
      session_context: {
        sources: [{ type: 'git_repository', url: `https://github.com/${repo}`, revision: `refs/heads/${branch}` }],
        outcomes: [{ type: 'git_repository', git_info: { type: 'github', repo, branches: [`claude/${branch}`] } }],
        model: 'claude-sonnet-4-6'
      }
    })
  })

  if (!res.ok) {
    const err = await res.text()
    // 401 の場合は Cookie 切れ → /refresh-claude-web-cookie を実行するよう通知
    return Response.json({ error: err, cookieExpired: res.status === 401 }, { status: res.status })
  }

  const session = await res.json()
  return Response.json({ sessionUrl: `https://claude.ai/code/${session.id}` })
}
```

---

## その他の確認済みエンドポイント

### 環境 ID 取得

```http
GET /v1/environment_providers/private/organizations/{org_id}/environments
```

アカウント固定値。一度取得すれば使い回せる。

### セッションイベント取得（ポーリング）

```http
GET /v1/sessions/{session_id}/events?limit=1000
anthropic-version: 2023-06-01
anthropic-beta: ccr-byoc-2025-07-29
anthropic-client-feature: ccr
```

セッション内の全イベント（ユーザー入力・ツール呼び出し・AI 応答）を取得。

### Presence（ハートビート）

```http
POST /v1/code/sessions/cse_{session_id}/client/presence
Content-Type: application/json

{"client_id": "<UUID>"}
```

### ブランチステータス一括確認

```http
POST /v1/code/github/batch-branch-status
Content-Type: application/json

{
  "repo_branches": [{"repo": "owner/repo", "branch": "claude/xxx"}],
  "discover_session_prs": true,
  "session_ids": ["session_01XXXX"]
}
```

---

## URL パターン

| 状態 | URL |
|---|---|
| 入力前（新規画面） | `https://claude.ai/code/draft_{uuid}` |
| セッション確立後 | `https://claude.ai/code/session_{id}` |
| 内部 ID（presence 用） | `cse_{id}` |

---

## 注意事項

- Cloudflare の Bot Protection により **素の curl からは 403**（ブラウザ TLS フィンガープリントが必要）。サーバーサイド `fetch` は通る
- `CLAUDE_CODE_OAUTH_TOKEN`（CLI 用 OAuth）は `/v1/sessions` では使えない（Cloudflare がブロック）
- Cookie の有効期限は未確認（ログアウトで即無効）
- Rate limit は未確認

---

## 関連

- [claude-code-web-session-creation.md](./claude-code-web-session-creation.md) — 公式経路（`claude --remote` / Routines API）の整理
- `.claude/skills/dev/refresh-claude-web-cookie/SKILL.md` — Cookie 期限切れ時の自動更新スキル
