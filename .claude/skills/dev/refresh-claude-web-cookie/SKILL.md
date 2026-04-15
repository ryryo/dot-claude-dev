---
name: dev:refresh-claude-web-cookie
description: |
  claude.ai の sessionKey Cookie を Chrome プロファイルから抽出し、有効性確認後に
  Vercel 環境変数（Production / Development）と dashboard/.env.local の両方を
  即時更新するスキル。再デプロイ不要でゼロダウンタイム更新が可能。

  Trigger:
  Cookie更新, sessionKey更新, Cookie切れ, /dev:refresh-claude-web-cookie, /refresh-claude-web-cookie
---

# refresh-claude-web-cookie

`sessionKey` Cookie（claude.ai の認証トークン）を Chrome プロファイルから抽出し、
**Vercel 環境変数** と **`dashboard/.env.local`** の両方を即時更新するスキル。
再デプロイ不要（Vercel）／dev サーバー再起動のみ（ローカル）で反映可能。

## トリガー

`/refresh-claude-web-cookie` または「Cookie更新」「sessionKey更新」「Cookie切れ」

## 前提条件

### 必須ツール

| ツール | 用途 | 取得方法 |
|---|---|---|
| `uvx` | Python パッケージ `browser-cookie3` を一時実行 | `brew install uv` |
| `vercel` CLI | Vercel 環境変数を更新（ログイン + プロジェクト link 済み） | `npm i -g vercel` |
| Google Chrome | claude.ai にログイン済みであること | — |

初回実行時、`browser-cookie3` が macOS Keychain にアクセスするため、
Keychain パスワード入力プロンプトが出る可能性あり（許可すると以後は通る）。

### 環境変数

| 環境変数 | 説明 | 必須 |
|---|---|---|
| `CLAUDE_WEB_VERCEL_PROJECT_DIR` | `vercel env` 実行時の作業ディレクトリ。ローカル env ファイル `<dir>/.env.local` の更新先も同じディレクトリを使う | ❌ デフォルト: `dashboard/`（`.vercel/project.json` と `.env.local` が存在する場所） |

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

### Step 2: 有効性チェック（Node.js fetch で CF を素通り）

取得した Cookie がサーバーで有効か `GET /v1/sessions` で確認:

```bash
node -e "
fetch('https://claude.ai/v1/sessions', {
  method: 'GET',
  headers: {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0',
    'anthropic-version': '2023-06-01',
    'anthropic-beta': 'managed-agents-2026-04-01',
    'anthropic-client-feature': 'ccr',
    'x-organization-uuid': process.env.CLAUDE_ORG_UUID,
    'Cookie': 'sessionKey=' + process.env.COOKIE_VALUE,
  },
}).then(r => console.log(r.status))
"
```

> **注意**: 素の curl は Cloudflare に 403 で弾かれる。必ず **Node.js native fetch**
> を使うこと（CF 素通り、実測 200/401 応答）。

- **200** → Step 3 へ
- **401/403** → ユーザーに「claude.ai に再ログインしてから再実行してください」と伝えて終了

**必須ヘッダー（実測確認済み）:**
- `anthropic-version: 2023-06-01` — ないと `"header is required"` エラー
- `anthropic-beta: ccr-byoc-2025-07-29` — POST /v1/sessions 用の正しい値
  - GET の有効性確認のみ `managed-agents-2026-04-01` でも可
- `anthropic-client-feature: ccr` — Web UI と同じ値
- `x-organization-uuid: {org_uuid}` — Web UI は常に付与

### Step 3: Vercel 環境変数を更新

`vercel env rm` → `vercel env add` で Production と Development に投入する
（Encrypted 自動、再デプロイ不要で即時反映）。

```bash
cd "${CLAUDE_WEB_VERCEL_PROJECT_DIR:-dashboard}"

for ENV in production development; do
  vercel env rm CLAUDE_SESSION_KEY "$ENV" --yes 2>/dev/null || true
  vercel env add CLAUDE_SESSION_KEY "$ENV" --value "$COOKIE_VALUE" --yes
done
```

**Preview について**: プロジェクトが Git 連携されている場合のみ追加可能。未連携の場合は
`vercel env add CLAUDE_SESSION_KEY preview --value "$COOKIE_VALUE" --yes` がエラーで
落ちるので、その場合はスキップする（Production が本番用なので問題ない）。

確認:

```bash
vercel env ls 2>&1 | grep CLAUDE_SESSION_KEY
```

### Step 4: ローカル `dashboard/.env.local` を更新

Next.js dev server (`pnpm dev`) が読むのは `dashboard/.env.local` のみ。
`CLAUDE_SESSION_KEY` 行を冪等に置換する。他のキー（GITHUB_TOKEN 等）は触らない。

```bash
ENV_FILE="${CLAUDE_WEB_VERCEL_PROJECT_DIR:-dashboard}/.env.local"
touch "$ENV_FILE"

if grep -q "^CLAUDE_SESSION_KEY=" "$ENV_FILE" 2>/dev/null; then
  # 既存行を置換
  sed -i '' "s|^CLAUDE_SESSION_KEY=.*|CLAUDE_SESSION_KEY=${COOKIE_VALUE}|" "$ENV_FILE"
else
  # 末尾に追記
  echo "CLAUDE_SESSION_KEY=${COOKIE_VALUE}" >> "$ENV_FILE"
fi
```

> **注意**: `dashboard/.env.local` は `.gitignore` 済み（コミット対象外）。
> dev server 起動中なら **再起動が必要**（Next.js は env を起動時にしか読まない）。

### Step 5: 完了報告

```
✅ sessionKey を更新しました

  取得元:                Chrome Cookie DB (browser-cookie3)
  有効性確認:            ✅ HTTP 200
  Vercel env:            ✅ Production / Development
  dashboard/.env.local:  ✅ 更新済み

  Vercel の本番環境には再デプロイ不要で即時反映されます。
  ローカル dev サーバーが起動中の場合は再起動してください。
```

## Vercel サーバーレス関数での読み取り方

```typescript
// app/api/sessions/launch/route.ts
export const runtime = 'nodejs'

export async function POST(req: Request) {
  const sessionKey = process.env.CLAUDE_SESSION_KEY
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
