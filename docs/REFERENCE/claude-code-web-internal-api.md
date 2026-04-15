# Claude Code Web — 内部 REST API リファレンス

調査日: 2026-04-15（初版）/ 2026-04-15 改訂（Node.js fetch エンドツーエンド検証 + 誤記訂正）
調査手法: Claude in Chrome MCP + fetch/XHR インターセプター + JS バンドル解析 + Node.js fetch 実測 + `browser-cookie3` での Cookie DB 抽出

---

## 結論

**`sessionKey` Cookie + 正しいヘッダーで `POST /v1/sessions` → 200 を実測済み（ブラウザ・Node.js の両方）。**
Vercel サーバーレス関数から Node.js 標準 `fetch` でセッションを作成できる（永続サーバー不要）。

> ⚠️ 非公開の内部 API。予告なく変更される可能性がある。

### 実測結果サマリー（2026-04-15）

| 経路 | GET /v1/sessions | POST /v1/sessions |
|---|---|---|
| ブラウザ (credentials: 'include') | ✅ 200 `{"data":[]}` | ✅ 200 `id: session_01APqYtgoJjzWojSZbfw8rLC` |
| Node.js native fetch + `sessionKey` Cookie | ✅ 200 `{"data":[]}` | ✅ 200 `id: session_01QcDhNJ4BGtRcir36WDXhhW` |
| Node.js native fetch, **Cookie 無し** | 401 (Anthropic 認証層に到達) | 401 (同上) |
| `curl` (UA 偽装あり, Cookie 無し) | ❌ 403 (Cloudflare challenge) | ❌ 403 (同上) |

Node.js の `fetch` (Undici) は Cloudflare を素通りするが、curl は TLS フィンガープリントで 403。
**Vercel の Node.js serverless runtime なら問題なく動作する。**

---

## 認証

### sessionKey Cookie

すべての `/v1/*` エンドポイントはブラウザセッション Cookie で認証する。

| 項目 | 内容 |
|---|---|
| Cookie 名 | **`sessionKey`** |
| 値の形式 | `sk-ant-sid02-...`（131 文字） |
| HttpOnly | ✅（`document.cookie` からは取得 **不可**） |
| Domain / Path | `.claude.ai` / `/` |
| 失効条件 | ログアウト / パスワード変更 / セッション期限切れ |
| 取得方法 | ①DevTools → Application → Cookies → `https://claude.ai` → `sessionKey` の Value をコピー ②`browser-cookie3` で Chrome プロファイルから自動抽出（下記参照） |

> ⚠️ **紛らわしい兄弟 Cookie**: `sessionKeyLC` という似た名前の Cookie も存在するが、これは **13 桁のタイムスタンプ**（最終確認時刻の目印）で **認証には使えない**。
> `document.cookie` から見える `sessionKeyLC=1775793546778` のような値を使うと 401 になる。実際の認証 Cookie は HttpOnly な `sessionKey`。

### `browser-cookie3` による自動抽出（macOS / Linux）

Chrome が管理する HttpOnly Cookie を、macOS Keychain 連携で自動復号して取り出せる。

```bash
uvx --from browser-cookie3 python -c "
import browser_cookie3
cj = browser_cookie3.chrome(domain_name='claude.ai')
for c in cj:
    if c.name == 'sessionKey':
        print(c.value)
        break
"
# => sk-ant-sid02-TEaA5nFoRauAkjr3r...（131 chars）
```

`uvx` は `brew install uv` で入る。初回は Keychain パスワードのプロンプトが出ることがある。

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
Cookie: sessionKey=<value>
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
Cookie: sessionKey=<value>
```

- **200** `{"data": []}` → Cookie 有効
- **401** → Cookie 期限切れ

> GET では `managed-agents-2026-04-01` でも動く。POST は `ccr-byoc-2025-07-29` が必須。

---

## Vercel サーバーレス実装サンプル

`sessionKey` Cookie を Vercel KV に保存し、Node.js serverless runtime の `fetch`
で動的に読んでセッション作成する構成。Vercel の Node runtime は TLS フィンガー
プリントが Cloudflare に通るため、永続サーバー不要で動く（実測: 2026-04-15）。

```typescript
// app/api/sessions/launch/route.ts
import { kv } from '@vercel/kv'

export const runtime = 'nodejs' // ★ Edge runtime ではなく Node.js runtime で

const ORG_UUID = process.env.CLAUDE_ORG_UUID!
const ENV_ID   = process.env.CLAUDE_ENV_ID!

export async function POST(req: Request) {
  const { repo, branch, prompt } = await req.json()

  const sessionKey = await kv.get<string>('sessionKey')
  if (!sessionKey) {
    return Response.json(
      { error: 'Cookie not set. Run /refresh-claude-web-cookie' },
      { status: 500 }
    )
  }

  const res = await fetch('https://claude.ai/v1/sessions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Cookie': `sessionKey=${sessionKey}`,
      'anthropic-version': '2023-06-01',
      'anthropic-beta': 'ccr-byoc-2025-07-29',
      'anthropic-client-feature': 'ccr',
      'x-organization-uuid': ORG_UUID,
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36',
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

- **Cloudflare 通過性**: 素の `curl` は 403（"Just a moment..." チャレンジ）。**Node.js の標準 `fetch` (Undici) は素通りする**（実測: 2026-04-15、認証無しでも 401 = Anthropic 認証層まで到達）。Vercel Node runtime はこの挙動なので利用可能。
- `CLAUDE_CODE_OAUTH_TOKEN`（CLI 用 OAuth）は `/v1/sessions` では使えない
- Cookie の有効期限は未確認（ログアウトで即無効）
- Rate limit は未確認
- **SessionKey の混同注意**: Cookie 一覧には `sessionKey`（認証用, HttpOnly）と `sessionKeyLC`（タイムスタンプ, 非 HttpOnly）が併存する。`document.cookie` から見えるのは後者だけで、後者では認証できない。

---

## 関連

- [claude-code-web-session-creation.md](./claude-code-web-session-creation.md) — 公式経路（`claude --remote` / Routines API）の整理
- `.claude/skills/dev/refresh-claude-web-cookie/SKILL.md` — Cookie 期限切れ時の自動更新スキル
