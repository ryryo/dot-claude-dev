# #5 カスタムMCPツール統合アプリ

**何を作れるか**: SDKに独自のドメイン固有ツール（メール検索、DB操作、外部API呼び出し等）をMCPサーバーとして統合し、エージェントから直接呼び出せるフルスタックアプリ。

**デモソース**: [email-agent](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/email-agent)

## アーキテクチャ

```
ブラウザ ←WS→ サーバー → AIClient → query()
                                      ├── 標準ツール (Bash, Read, Write...)
                                      └── MCPツール (mcp__email__search_inbox, ...)
                                              ↑
                                        createSdkMcpServer で定義
```

**SDK主要機能**: `createSdkMcpServer`, `tool()`, `query()` + `mcpServers`, `resume`

## コード例: MCPツール定義（TypeScript）

```typescript
import { tool, createSdkMcpServer } from '@anthropic-ai/claude-agent-sdk';
import { z } from 'zod';

// カスタムMCPサーバーの作成
export const customServer = createSdkMcpServer({
  name: 'email',       // ツール名プレフィックス: mcp__email__*
  version: '1.0.0',
  tools: [
    tool(
      'search_inbox',  // → エージェントからは mcp__email__search_inbox で呼び出し
      'Search emails in the inbox using Gmail query syntax',
      {
        // Zod スキーマでツール入力を型安全に定義
        gmailQuery: z.string().describe(
          "Gmail query string (e.g., 'from:example@gmail.com subject:invoice')"
        ),
      },
      async (args) => {
        // ツール実装: 検索実行 → 結果返却
        const results = await emailApi.searchEmails({
          gmailQuery: args.gmailQuery,
          limit: 30,
        });

        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              totalResults: results.length,
              emails: results.map(formatEmail),
            }, null, 2),
          }],
        };
      }
    ),

    tool(
      'read_emails',   // → mcp__email__read_emails
      'Read multiple emails by their IDs',
      {
        ids: z.array(z.string()).describe('Array of email message IDs'),
      },
      async (args) => {
        const emails = await emailApi.getEmailsByIds(args.ids);
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({ emails: emails.map(formatEmail) }, null, 2),
          }],
        };
      }
    ),
  ],
});
```

## コード例: MCPサーバーを query() に統合（TypeScript）

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';
import { customServer } from './custom-tools';

class AIClient {
  async *queryStream(prompt: string, options?: Partial<AIQueryOptions>) {
    for await (const message of query({
      prompt,
      options: {
        maxTurns: 100,
        cwd: path.join(process.cwd(), 'agent'),
        model: 'opus',
        allowedTools: [
          // 標準ツール
          'Task', 'Bash', 'Read', 'Edit', 'Write', 'WebSearch', 'Skill',
          // MCPツール（mcp__{server名}__{tool名} の形式で指定）
          'mcp__email__search_inbox',
          'mcp__email__read_emails',
        ],
        appendSystemPrompt: EMAIL_AGENT_PROMPT,
        settingSources: ['local', 'project'],
        mcpServers: {
          email: customServer, // MCPサーバーを登録
        },
        hooks: { /* ... */ },
        ...options,
      },
    })) {
      yield message;
    }
  }
}
```

## コード例: セッション Resume で継続的対話（TypeScript）

```typescript
class Session {
  private sdkSessionId: string | null = null;

  async addUserMessage(content: string): Promise<void> {
    // 2回目以降は resume でセッションを継続
    const options = this.sdkSessionId
      ? { resume: this.sdkSessionId }
      : {};

    for await (const message of this.aiClient.queryStream(content, options)) {
      this.broadcastToSubscribers(message);

      // SDK セッションIDをキャプチャ
      if (message.type === 'system' && message.subtype === 'init') {
        this.sdkSessionId = message.session_id;
      }
    }
  }
}
```

## ポイント

- `createSdkMcpServer()` で独自ドメインのツールを宣言的に定義
- `tool()` は Zod スキーマによる型安全な入力定義をサポート
- MCPツールは `mcp__{サーバー名}__{ツール名}` の形式でエージェントに公開される
- `allowedTools` にMCPツール名を明示的にリスト化して利用許可
- `resume` オプションで同じセッションIDを渡してマルチターン会話を実現
- `settingSources: ['local', 'project']` でスキル・設定を読み込み
