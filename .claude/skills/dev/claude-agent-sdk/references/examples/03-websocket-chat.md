# #3 WebSocket チャットアプリ

**何を作れるか**: ブラウザとリアルタイム通信するチャットアプリ。WebSocket経由でユーザーメッセージを受け取り、SDKのストリーミング出力をクライアントに転送。

**デモソース**: [simple-chatapp](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/simple-chatapp)

## アーキテクチャ

```
ブラウザ ←WebSocket→ サーバー ←MessageQueue→ query() SDK
                         ↑
                     Session管理（マルチユーザー対応）
```

**SDK主要機能**: `query()` + ストリーミング入力（AsyncIterable）、セッション管理

## コード例: MessageQueue パターン（TypeScript）

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

// AsyncIterable を実装したメッセージキュー
// SDK の prompt に渡すことでストリーミング入力を実現
class MessageQueue {
  private messages: UserMessage[] = [];
  private waiting: ((msg: UserMessage) => void) | null = null;
  private closed = false;

  push(content: string) {
    const msg: UserMessage = {
      type: 'user',
      message: { role: 'user', content },
    };
    if (this.waiting) {
      this.waiting(msg);
      this.waiting = null;
    } else {
      this.messages.push(msg);
    }
  }

  async *[Symbol.asyncIterator](): AsyncIterableIterator<UserMessage> {
    while (!this.closed) {
      if (this.messages.length > 0) {
        yield this.messages.shift()!;
      } else {
        yield await new Promise<UserMessage>((resolve) => {
          this.waiting = resolve;
        });
      }
    }
  }

  close() { this.closed = true; }
}
```

## コード例: セッション管理クラス（TypeScript）

```typescript
// SDK の query() にキューを渡して長時間実行セッションを作成
class AgentSession {
  private queue = new MessageQueue();
  private outputIterator: AsyncIterator<any> | null = null;

  constructor() {
    this.outputIterator = query({
      prompt: this.queue as any, // AsyncIterable をストリーミング入力として渡す
      options: {
        maxTurns: 100,
        model: 'opus',
        allowedTools: ['Bash', 'Read', 'Write', 'Edit', 'WebSearch', 'WebFetch'],
        systemPrompt: 'You are a helpful AI assistant.',
      },
    })[Symbol.asyncIterator]();
  }

  sendMessage(content: string) {
    this.queue.push(content);
  }

  async *getOutputStream() {
    if (!this.outputIterator) throw new Error('Session not initialized');
    while (true) {
      const { value, done } = await this.outputIterator.next();
      if (done) break;
      yield value;
    }
  }

  close() { this.queue.close(); }
}
```

## コード例: WebSocket → SDK ブリッジ（TypeScript）

```typescript
// WebSocket セッション管理: SDKメッセージをクライアントに転送
class Session {
  private agentSession: AgentSession;
  private subscribers: Set<WSClient> = new Set();

  sendMessage(content: string) {
    this.agentSession.sendMessage(content);
    if (!this.isListening) this.startListening();
  }

  private async startListening() {
    this.isListening = true;
    for await (const message of this.agentSession.getOutputStream()) {
      this.handleSDKMessage(message);
    }
  }

  private handleSDKMessage(message: any) {
    if (message.type === 'assistant') {
      const content = message.message.content;
      if (Array.isArray(content)) {
        for (const block of content) {
          if (block.type === 'text') {
            this.broadcast({ type: 'assistant_message', content: block.text });
          } else if (block.type === 'tool_use') {
            this.broadcast({
              type: 'tool_use',
              toolName: block.name,
              toolId: block.id,
              toolInput: block.input,
            });
          }
        }
      }
    } else if (message.type === 'result') {
      this.broadcast({
        type: 'result',
        success: message.subtype === 'success',
        cost: message.total_cost_usd,
        duration: message.duration_ms,
      });
    }
  }
}
```

## ポイント

- `query()` の `prompt` に AsyncIterable を渡すとストリーミング入力になる
- MessageQueue パターンで「SDKが待機中にユーザーメッセージを後から注入」を実現
- SDKメッセージの `type` で分岐: `assistant`（テキスト/ツール使用）、`result`（完了）、`system`（初期化）
- 複数クライアントへの broadcast で WebSocket マルチユーザー対応
