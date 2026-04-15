# refresh-claude-web-cookie

`sessionKeyLC` Cookie の有効性を確認し、期限切れなら Claude in Chrome でブラウザから
再取得して **Vercel KV**（本番）と**ローカル env ファイル**の両方を即時更新するスキル。
再デプロイ不要でゼロダウンタイム更新が可能。

## トリガー

`/refresh-claude-web-cookie` または「Cookie更新」「sessionKeyLC更新」「Cookie切れ」

## 前提条件

| 環境変数 | 説明 | 必須 |
|---|---|---|
| `VERCEL_KV_REST_API_URL` | Vercel KV の REST API エンドポイント | Vercel更新時のみ |
| `VERCEL_KV_REST_API_TOKEN` | Vercel KV の認証トークン | Vercel更新時のみ |
| `CLAUDE_WEB_ENV_FILE` | ローカル env ファイルパス | ❌ デフォルト: `~/.claude-web-session.env` |

Vercel KV のセットアップ: Vercel ダッシュボード → Storage → Create KV Database →
`KV_REST_API_URL` と `KV_REST_API_TOKEN` を取得して環境変数に設定する。

## 実行フロー

### Step 1: ブラウザセッションの確認（Claude in Chrome MCP）

`tabs_context_mcp` でタブを取得し、既存の `claude.ai` タブがあれば再利用、なければ新規タブで開く。

ブラウザ内から現在のセッション有効性を確認:

```javascript
// 必須ヘッダーを付けてテスト（credentials: 'include' でブラウザの実Cookie を使用）
fetch('https://claude.ai/v1/sessions', {
  credentials: 'include',
  headers: {
    'anthropic-beta': 'managed-agents-2026-04-01',
    'anthropic-version': '2023-06-01'
  }
}).then(r => window._sessionStatus = r.status)
```

**必須ヘッダー（実行テストで確認済み）:**
- `anthropic-beta: managed-agents-2026-04-01` — ないと `"this API is in beta"` エラー
- `anthropic-version: 2023-06-01` — ないと `"anthropic-version: header is required"` エラー

- **200** → セッション有効。Step 2 へ（Cookie値を取得して保存）
- **401/403/その他** → ユーザーに「claude.ai にログインしてから再実行してください」と伝えて終了

### Step 2: sessionKeyLC の値を取得

```javascript
document.cookie
  .split(';')
  .map(c => c.trim())
  .find(c => c.startsWith('sessionKeyLC='))
  ?.split('=').slice(1).join('=')  // = を含む値に対応
```

取得できない場合（HttpOnly 等）: ユーザーに以下を案内して終了

```
ブラウザの DevTools → Application → Cookies → claude.ai → sessionKeyLC
の値をコピーして教えてください
```

### Step 3: Vercel KV に保存

`VERCEL_KV_REST_API_URL` が設定されている場合のみ実行:

```bash
# Vercel KV REST API (Upstash 互換)
curl -s -X POST "${VERCEL_KV_REST_API_URL}/set/sessionKeyLC" \
  -H "Authorization: Bearer ${VERCEL_KV_REST_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "[\"${COOKIE_VALUE}\"]"
```

保存確認:

```bash
curl -s "${VERCEL_KV_REST_API_URL}/get/sessionKeyLC" \
  -H "Authorization: Bearer ${VERCEL_KV_REST_API_TOKEN}"
```

レスポンスの `result` が取得した値と一致すれば ✅

### Step 4: ローカル env ファイルに保存

```bash
ENV_FILE="${CLAUDE_WEB_ENV_FILE:-$HOME/.claude-web-session.env}"

# ファイルが存在しない場合は作成
touch "$ENV_FILE"

# 既存行を置換、なければ追記
if grep -q "^CLAUDE_AI_SESSION_KEY_LC=" "$ENV_FILE" 2>/dev/null; then
  sed -i '' "s|^CLAUDE_AI_SESSION_KEY_LC=.*|CLAUDE_AI_SESSION_KEY_LC=${COOKIE_VALUE}|" "$ENV_FILE"
else
  echo "CLAUDE_AI_SESSION_KEY_LC=${COOKIE_VALUE}" >> "$ENV_FILE"
fi
```

### Step 5: 完了報告

以下のサマリーを表示:

```
✅ sessionKeyLC を更新しました

  Vercel KV 更新:     ✅ / ❌ (エラー内容)
  ローカル env 更新:   ✅ ${ENV_FILE}

  Vercel の本番環境には再デプロイ不要で即時反映されます。
```

## Vercel サーバーレス関数での読み取り方

```typescript
// app/api/sessions/launch/route.ts
import { kv } from '@vercel/kv'

export async function POST(req: Request) {
  // KV から動的に取得（毎リクエストで最新値を読む）
  const sessionKeyLC = await kv.get<string>('sessionKeyLC')
  if (!sessionKeyLC) {
    return Response.json({ error: 'Cookie not configured. Run /refresh-claude-web-cookie' }, { status: 500 })
  }

  // ... セッション作成リクエスト
}
```

## 参考

内部 API の詳細: `docs/REFERENCE/claude-code-web-internal-api.md`
