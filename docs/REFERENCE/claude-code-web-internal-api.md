# Claude Code Web — 内部 REST API 調査メモ

調査日: 2026-04-15  
調査手法: Claude in Chrome MCP でブラウザを操作し、fetch インターセプターを注入してリクエストを全量捕捉

---

## 結論

**curl 等から直接セッションを作成することは技術的に可能。** ただし認証に `sessionKeyLC` Cookie（Web セッション Cookie）が必要であり、公式サポートの外部 API ではない。

---

## 発見したエンドポイント一覧

すべてのベース URL は `https://claude.ai`。

| メソッド | パス | 用途 |
|---|---|---|
| GET | `/v1/sessions` | セッション一覧取得（ページネーション: `?after_id=session_xxx`） |
| POST | `/v1/sessions` | **セッション作成（本体）** |
| GET | `/v1/sessions/{session_id}/events?limit=1000` | セッション内イベント一覧取得 |
| GET | `/v1/sessions/{session_id}/share-status` | セッションの共有状態取得 |
| GET | `/v1/environment_providers/private/organizations/{org_id}/environments` | 利用可能な実行環境一覧 |
| POST | `/v1/code/sessions/cse_{session_id}/client/presence` | クライアント presence（Heartbeat） |
| POST | `/v1/session_ingress/session/{session_id}/git_proxy/compare` | セッション内 git diff |
| POST | `/v1/code/github/batch-branch-status` | ブランチ状態の一括確認 |
| GET | `/api/organizations/{org_id}` | 組織情報取得 |
| GET | `/api/organizations/{org_id}/code/repos?skip_status=true` | 接続済み GitHub リポジトリ一覧 |
| POST | `/api/organizations/{org_id}/dust/generate_title_and_branch` | セッションタイトル＆ブランチ名の自動生成 |

---

## セッション作成フロー

### Step 1 — 実行環境 ID を取得

```http
GET /v1/environment_providers/private/organizations/{org_id}/environments
```

レスポンスから `environment_id`（例: `env_01AgnTYbWgkEvJy9tGzX87ej`）を取得する。  
この値はアカウント固定で変化しないため、一度取得すれば使い回せる。

---

### Step 2 — タイトル＆ブランチ名を生成（任意）

```http
POST /api/organizations/{org_id}/dust/generate_title_and_branch
Content-Type: application/json

{
  "first_session_message": "YOUR_PROMPT",
  "title_style": "default"
}
```

レスポンス例（推定）:
```json
{
  "title": "HI2 Implementation",
  "branch": "claude/hi2-implementation-of29R"
}
```

タイトルを自分で決める場合はこのステップをスキップして Step 3 で直接 `"title"` を指定すればよい。

---

### Step 3 — セッション作成

```http
POST /v1/sessions
Content-Type: application/json

{
  "title": "任意のタイトル",
  "events": [
    {
      "type": "event",
      "data": {
        "uuid": "<ランダム UUID>",
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
          "branches": ["claude/{suggested-branch-name}"]
        }
      }
    ],
    "model": "claude-sonnet-4-6"
  }
}
```

レスポンスに含まれる `session_id` で `https://claude.ai/code/{session_id}` が有効なセッション URL になる。

#### フィールド説明

| フィールド | 説明 |
|---|---|
| `title` | サイドバーに表示されるセッション名。任意の文字列で OK |
| `events[].data.uuid` | クライアント側で生成するランダム UUID（重複しなければ何でもよい） |
| `events[].data.session_id` | 新規作成時は空文字列 `""` |
| `events[].data.type` | 最初のユーザーメッセージなので `"user"` |
| `events[].data.message.content` | 最初のプロンプト本文 |
| `environment_id` | Step 1 で取得した実行環境 ID |
| `session_context.sources[].revision` | クローン対象ブランチ（`refs/heads/{branch}`形式） |
| `session_context.outcomes[].git_info.branches` | Claude が作業に使うブランチ候補（`claude/` プレフィックス推奨） |
| `session_context.model` | 使用モデル（例: `"claude-sonnet-4-6"`） |

---

## 必須ヘッダー

`/v1/*` エンドポイントには Cookie に加えて以下のヘッダーが必須（JS バンドル解析 + 実行テストで確認）:

| ヘッダー | 値 | 備考 |
|---|---|---|
| `anthropic-version` | `2023-06-01` | 欠落時: `"anthropic-version: header is required"` |
| `anthropic-beta` | `ccr-byoc-2025-07-29` | Web UI の正しい値。`managed-agents-2026-04-01` は別スキーマ（POST 不可） |
| `anthropic-client-feature` | `ccr` | Web UI が常に付与 |
| `x-organization-uuid` | `{org_uuid}` | 任意だが Web UI は常に付与 |

`ccr` は Claude Code Relay の略と思われる。`ccr-byoc-2025-07-29` で **POST /v1/sessions の 200 確認済み**（2026-04-15）。

---

## 認証

### Cookie ベース認証

`claude.ai` のすべての `/v1/*` および `/api/*` エンドポイントは、明示的な `Authorization` ヘッダーを使用せず、ブラウザセッション Cookie で認証される。

```
Cookie: sessionKeyLC=<value>
```

- `sessionKeyLC` はブラウザの `document.cookie` から取得可能（HttpOnly ではない）
- curl で使う場合: `--cookie "sessionKeyLC=<value>"`
- 有効期限はブラウザセッションに依存（クリアされると無効）

### curl サンプル

```bash
# 環境 ID 取得
curl -s "https://claude.ai/v1/environment_providers/private/organizations/{org_id}/environments" \
  --cookie "sessionKeyLC=<your_cookie>"

# セッション作成
curl -s -X POST "https://claude.ai/v1/sessions" \
  --cookie "sessionKeyLC=<your_cookie>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Session",
    "events": [{
      "type": "event",
      "data": {
        "uuid": "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx",
        "session_id": "",
        "type": "user",
        "parent_tool_use_id": null,
        "message": {"role": "user", "content": "Fix the failing tests"}
      }
    }],
    "environment_id": "env_01AgnTYbWgkEvJy9tGzX87ej",
    "session_context": {
      "sources": [{"type": "git_repository", "url": "https://github.com/ryryo/dot-claude-dev", "revision": "refs/heads/master"}],
      "outcomes": [{"type": "git_repository", "git_info": {"type": "github", "repo": "ryryo/dot-claude-dev", "branches": ["claude/fix-tests"]}}],
      "model": "claude-sonnet-4-6"
    }
  }'
```

---

## セッション URL の構造

| 状態 | URL パターン |
|---|---|
| 入力前（新規画面） | `https://claude.ai/code/draft_{uuid}` |
| 送信後（セッション確立） | `https://claude.ai/code/session_{id}` |
| 内部セッション ID | `cse_{id}`（presence / heartbeat エンドポイントで使用） |

---

## その他の確認済みエンドポイント

### presence（ハートビート）

```http
POST /v1/code/sessions/cse_{session_id}/client/presence
Content-Type: application/json

{"client_id": "<UUID>"}
```

セッション接続を維持するためのハートビート。定期的に POST する。

### セッションイベント取得

```http
GET /v1/sessions/{session_id}/events?limit=1000
```

セッション内のすべてのイベント（ユーザーメッセージ、ツール呼び出し、AI 応答など）を取得。ポーリングまたはロングポールで UI を更新している模様。

### ブランチステータス一括確認

```http
POST /v1/code/github/batch-branch-status
Content-Type: application/json

{
  "repo_branches": [
    {"repo": "ryryo/dot-claude-dev", "branch": "claude/some-branch"}
  ],
  "discover_session_prs": true,
  "session_ids": ["session_01XXXX"]
}
```

---

## 注意事項

- これらは **非公開の内部 API** であり、予告なく変更・廃止される可能性がある
- `sessionKeyLC` Cookie はブラウザログアウト・パスワード変更で無効になる
- Rate limit やアカウント制限については未確認
- 公式の外部連携には **Routines API** または **`claude --remote` CLI** を使うこと（詳細: `claude-code-web-session-creation.md`）

---

## 関連ドキュメント

- [claude-code-web-session-creation.md](./claude-code-web-session-creation.md) — `claude --remote` CLI と Routines API による公式連携の整理
