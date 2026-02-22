# MCPで外部ツールに接続する

Model Context Protocol (MCP) は、AIエージェントを外部ツールやデータソースに接続するためのオープンスタンダード。データベースクエリ、Slack/GitHub等のAPI統合、その他のサービス接続をカスタムツール実装なしで実現する。

## クイックスタート

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Use the docs MCP server to explain what hooks are in Claude Code",
  options: {
    mcpServers: {
      "claude-code-docs": {
        type: "http",
        url: "https://code.claude.com/docs/mcp"
      }
    },
    allowedTools: ["mcp__claude-code-docs__*"]
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def main():
    options = ClaudeAgentOptions(
        mcp_servers={
            "claude-code-docs": {
                "type": "http",
                "url": "https://code.claude.com/docs/mcp"
            }
        },
        allowed_tools=["mcp__claude-code-docs__*"]
    )

    async for message in query(prompt="Use the docs MCP server to explain what hooks are in Claude Code", options=options):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(message.result)

asyncio.run(main())
```

## MCPサーバーの設定方法

### コード内で設定

`mcpServers` オプションにMCPサーバーを直接渡す。

### 設定ファイル (.mcp.json) から

プロジェクトルートに `.mcp.json` ファイルを作成。SDKが自動的に読み込む:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/me/projects"]
    }
  }
}
```

## ツールの命名規則

MCPツールは `mcp__<server-name>__<tool-name>` のパターンに従う。

例: `"github"` サーバーの `list_issues` ツール → `mcp__github__list_issues`

## allowedToolsでアクセスを制御

```typescript
options: {
  mcpServers: { /* your servers */ },
  allowedTools: [
    "mcp__github__*",              // githubサーバーのすべてのツール
    "mcp__db__query",              // dbサーバーのqueryツールのみ
    "mcp__slack__send_message"     // slackサーバーのsend_messageのみ
  ]
}
```

ワイルドカード（`*`）でサーバーの全ツールを許可可能。

## パーミッションモードの代替

| モード | 動作 |
|:------|:-----|
| `permissionMode: "acceptEdits"` | ツール使用を自動承認（破壊的操作はプロンプト表示） |
| `permissionMode: "bypassPermissions"` | すべての安全プロンプトをスキップ。サブエージェントにも伝播 |

## トランスポートタイプ

| タイプ | 用途 | 設定 |
|:------|:-----|:-----|
| **stdio** | ローカルプロセス（stdin/stdout通信） | `command`, `args`, `env` |
| **HTTP/SSE** | リモートサーバー、クラウドAPI | `type: "http"` or `"sse"`, `url`, `headers` |
| **SDK MCPサーバー** | アプリケーション内で直接定義 | `createSdkMcpServer()` を使用 |

### stdioサーバーの例

```typescript
options: {
  mcpServers: {
    "github": {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-github"],
      env: {
        GITHUB_TOKEN: process.env.GITHUB_TOKEN
      }
    }
  },
  allowedTools: ["mcp__github__list_issues", "mcp__github__search_issues"]
}
```

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### HTTP/SSEサーバーの例

```typescript
options: {
  mcpServers: {
    "remote-api": {
      type: "sse",
      url: "https://api.example.com/mcp/sse",
      headers: {
        Authorization: `Bearer ${process.env.API_TOKEN}`
      }
    }
  },
  allowedTools: ["mcp__remote-api__*"]
}
```

## MCPツール検索

大量のMCPツールがある場合、ツール定義がコンテキストウィンドウを圧迫する。ツール検索はオンデマンドで動的にツールをロードする。

### 仕組み

- デフォルトでautoモード（MCPツールの説明がコンテキストの10%以上で発動）
- ツールを `defer_loading: true` としてマーク
- Claudeが検索ツールで必要なツールのみを発見してロード

**要件**: Sonnet 4以降、またはOpus 4以降。Haikuはツール検索非対応。

### 設定: ENABLE_TOOL_SEARCH

| 値 | 動作 |
|:------|:---------|
| `auto` | MCPツールがコンテキストの10%を超えるとアクティブ（デフォルト） |
| `auto:5` | 5%のしきい値でアクティブ |
| `true` | 常に有効 |
| `false` | 無効、すべてのMCPツールを事前ロード |

```typescript
const options = {
  mcpServers: { /* your MCP servers */ },
  env: {
    ENABLE_TOOL_SEARCH: "auto:5"
  }
};
```

## 認証

### 環境変数で認証情報を渡す

```typescript
options: {
  mcpServers: {
    "github": {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-github"],
      env: {
        GITHUB_TOKEN: process.env.GITHUB_TOKEN
      }
    }
  },
  allowedTools: ["mcp__github__list_issues"]
}
```

### リモートサーバー用のHTTPヘッダー

```typescript
options: {
  mcpServers: {
    "secure-api": {
      type: "http",
      url: "https://api.example.com/mcp",
      headers: {
        Authorization: `Bearer ${process.env.API_TOKEN}`
      }
    }
  },
  allowedTools: ["mcp__secure-api__*"]
}
```

### OAuth2認証

MCP仕様はOAuth 2.1をサポート。SDKはOAuthフローを自動処理しないが、取得済みトークンをヘッダー経由で渡せる:

```typescript
const accessToken = await getAccessTokenFromOAuthFlow();

const options = {
  mcpServers: {
    "oauth-api": {
      type: "http",
      url: "https://api.example.com/mcp",
      headers: {
        Authorization: `Bearer ${accessToken}`
      }
    }
  },
  allowedTools: ["mcp__oauth-api__*"]
};
```

## エラーハンドリング

SDKはクエリ開始時にサブタイプ `init` の `system` メッセージを発行。`status` フィールドで接続失敗を検出:

```typescript
for await (const message of query({
  prompt: "Process data",
  options: {
    mcpServers: {
      "data-processor": dataServer
    }
  }
})) {
  if (message.type === "system" && message.subtype === "init") {
    const failedServers = message.mcp_servers.filter(
      s => s.status !== "connected"
    );
    if (failedServers.length > 0) {
      console.warn("Failed to connect:", failedServers);
    }
  }

  if (message.type === "result" && message.subtype === "error_during_execution") {
    console.error("Execution failed");
  }
}
```

**接続タイムアウト**: デフォルト60秒。
