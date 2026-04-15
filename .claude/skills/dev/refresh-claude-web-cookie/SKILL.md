---
name: dev:refresh-claude-web-cookie
description: |
  claude.ai の sessionKey Cookie を Chrome プロファイルから抽出し、有効性確認後に
  Vercel 環境変数（本番）とローカル env ファイルの両方を即時更新するスキル。
  再デプロイ不要でゼロダウンタイム更新が可能。

  Trigger:
  Cookie更新, sessionKey更新, Cookie切れ, /dev:refresh-claude-web-cookie, /refresh-claude-web-cookie
---

# refresh-claude-web-cookie

`sessionKey` Cookie（claude.ai の認証トークン）を Chrome プロファイルから抽出し、
**Vercel 環境変数**（本番）と**ローカル env ファイル**の両方を即時更新するスキル。
再デプロイ不要でゼロダウンタイム更新が可能。

## トリガー

`/refresh-claude-web-cookie` または「Cookie更新」「sessionKey更新」「Cookie切れ」

## 前提条件

### 必須ツール

| ツール | 用途 | 取得方法 |
|---|---|---|
| `uvx` | Python パッケージ `browser-cookie3` を一時実行 | `brew install uv` |
| Google Chrome | claude.ai にログイン済みであること | — |

初回実行時、`browser-cookie3` が macOS Keychain にアクセスするため、
Keychain パスワード入力プロンプトが出る可能性あり（許可すると以後は通る）。

### 環境変数

| 環境変数 | 説明 | 必須 |
|---|---|---|
| `VERCEL_KV_REST_API_URL` | Vercel KV の REST API エンドポイント | Vercel 更新時のみ |
| `VERCEL_KV_REST_API_TOKEN` | Vercel KV の認証トークン | Vercel 更新時のみ |
| `CLAUDE_WEB_ENV_FILE` | ローカル env ファイルパス | ❌ デフォルト: `~/.claude-web-session.env` |

Vercel KV のセットアップ: Vercel ダッシュボード → Storage → Create KV Database →
`KV_REST_API_URL` と `KV_REST_API_TOKEN` を取得して環境変数に設定する。

## 実行フロー

### Step 1: Chrome から sessionKey を自動抽出

Claude.ai の認証 Cookie `sessionKey` は **HttpOnly** のため `document.cookie` から
取得不可。代わりに Chrome のローカル Cookie DB (`~/Library/Application Support/
Google/Chrome/Default/Cookies`) を `browser-cookie3` で読む（macOS Keychain 連携で
自動復号）。

```bash
COOKIE_VALUE=$(uvx --quiet --from browser-cookie3 python -c "
import browser_cookie3
cj = browser_cookie3.chrome(domain_name='claude.ai')
for c in cj:
    if c.name == 'sessionKey':
        print(c.value)
        break
")
```

取得できない場合:
- Chrome で claude.ai にログインしていない → ユーザーにログインを案内して終了
- Keychain アクセス拒否 → 許可を依頼して再実行

### Step 2: 有効性チェック（Claude in Chrome MCP）

取得した Cookie がサーバーで有効か `GET /v1/sessions` で確認:

```bash
curl -s -o /dev/null -w "%{http_code}" https://claude.ai/v1/sessions \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: managed-agents-2026-04-01" \
  -H "Cookie: sessionKey=${COOKIE_VALUE}"
```

> **注意**: 素の curl は Cloudflare にブロックされる (403) ことがあるため、実装側は
> **Node.js native fetch** を使うこと。Node の `fetch` は Cloudflare を素通りできる
> (実測 200 / 401 応答、curl は 403)。上の curl は UA を偽装している前提の確認用。

- **200** → Step 3 へ
- **401/403** → ユーザーに「claude.ai に再ログインしてから再実行してください」と伝えて終了

**必須ヘッダー（実測確認済み）:**
- `anthropic-version: 2023-06-01` — ないと `"header is required"` エラー
- `anthropic-beta: ccr-byoc-2025-07-29` — POST /v1/sessions 用の正しい値
  - GET の有効性確認のみ `managed-agents-2026-04-01` でも可
- `anthropic-client-feature: ccr` — Web UI と同じ値
- `x-organization-uuid: {org_uuid}` — Web UI は常に付与

### Step 3: Vercel KV に保存

`VERCEL_KV_REST_API_URL` が設定されている場合のみ実行:

```bash
curl -s -X POST "${VERCEL_KV_REST_API_URL}/set/sessionKey" \
  -H "Authorization: Bearer ${VERCEL_KV_REST_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "[\"${COOKIE_VALUE}\"]"
```

保存確認:

```bash
curl -s "${VERCEL_KV_REST_API_URL}/get/sessionKey" \
  -H "Authorization: Bearer ${VERCEL_KV_REST_API_TOKEN}"
```

レスポンスの `result` が取得した値と一致すれば ✅

### Step 4: ローカル env ファイルに保存

```bash
ENV_FILE="${CLAUDE_WEB_ENV_FILE:-$HOME/.claude-web-session.env}"
touch "$ENV_FILE"

if grep -q "^CLAUDE_AI_SESSION_KEY=" "$ENV_FILE" 2>/dev/null; then
  sed -i '' "s|^CLAUDE_AI_SESSION_KEY=.*|CLAUDE_AI_SESSION_KEY=${COOKIE_VALUE}|" "$ENV_FILE"
else
  echo "CLAUDE_AI_SESSION_KEY=${COOKIE_VALUE}" >> "$ENV_FILE"
fi
```

### Step 5: 完了報告

```
✅ sessionKey を更新しました

  取得元:             Chrome Cookie DB (browser-cookie3)
  有効性確認:         ✅ HTTP 200
  Vercel KV 更新:     ✅ / ❌ (エラー内容)
  ローカル env 更新:   ✅ ${ENV_FILE}

  Vercel の本番環境には再デプロイ不要で即時反映されます。
```

## Vercel サーバーレス関数での読み取り方

```typescript
// app/api/sessions/launch/route.ts
import { kv } from '@vercel/kv'

export async function POST(req: Request) {
  const sessionKey = await kv.get<string>('sessionKey')
  if (!sessionKey) {
    return Response.json(
      { error: 'Cookie not configured. Run /refresh-claude-web-cookie' },
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
      'x-organization-uuid': process.env.CLAUDE_ORG_UUID!,
    },
    body: JSON.stringify({ /* events, environment_id, session_context, ... */ }),
  })

  if (res.status === 401) {
    return Response.json(
      { error: 'sessionKey expired. Run /refresh-claude-web-cookie', cookieExpired: true },
      { status: 401 }
    )
  }
  // ...
}
```

## 参考

- 実測検証レポート: `docs/REFERENCE/claude-code-web-internal-api.md`
- `sessionKey` vs `sessionKeyLC`: `sessionKey` が実際の認証トークン (`sk-ant-sid02-...`, HttpOnly)。
  `sessionKeyLC` は単なる 13 桁タイムスタンプのコンパニオン値で認証には使えない
