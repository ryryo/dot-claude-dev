# #2 セッション型マルチターン対話（V2 API）

**何を作れるか**: セッションベースの対話型アプリ。send/receive パターンで自然なマルチターン会話を実現。セッションの永続化・再開も可能。

**デモソース**: [hello-world-v2](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/hello-world-v2)

## アーキテクチャ

```
createSession → send() → stream() → send() → stream() → ...
                                     ↑ セッションIDで resumeSession も可能
```

**SDK主要機能**: `unstable_v2_createSession`, `unstable_v2_resumeSession`, `unstable_v2_prompt`

## コード例: マルチターン対話（TypeScript）

```typescript
import {
  unstable_v2_createSession,
  unstable_v2_resumeSession,
  unstable_v2_prompt,
} from '@anthropic-ai/claude-agent-sdk';

// --- パターンA: マルチターン会話 ---
async function multiTurn() {
  await using session = unstable_v2_createSession({ model: 'sonnet' });

  // ターン1
  await session.send('What is 5 + 3? Just the number.');
  for await (const msg of session.stream()) {
    if (msg.type === 'assistant') {
      const text = msg.message.content.find(
        (c): c is { type: 'text'; text: string } => c.type === 'text'
      );
      console.log(`Turn 1: ${text?.text}`);
    }
  }

  // ターン2 - Claudeはコンテキストを記憶している
  await session.send('Multiply that by 2. Just the number.');
  for await (const msg of session.stream()) {
    if (msg.type === 'assistant') {
      const text = msg.message.content.find(
        (c): c is { type: 'text'; text: string } => c.type === 'text'
      );
      console.log(`Turn 2: ${text?.text}`);
    }
  }
}

// --- パターンB: ワンショット便利関数 ---
async function oneShot() {
  const result = await unstable_v2_prompt(
    'What is the capital of France? One word.',
    { model: 'sonnet' }
  );
  if (result.subtype === 'success') {
    console.log(`Answer: ${result.result}`);
    console.log(`Cost: $${result.total_cost_usd.toFixed(4)}`);
  }
}

// --- パターンC: セッション再開 ---
async function sessionResume() {
  let sessionId: string | undefined;

  // セッション1: 情報を記憶させる
  {
    await using session = unstable_v2_createSession({ model: 'sonnet' });
    await session.send('My favorite color is blue. Remember this!');
    for await (const msg of session.stream()) {
      if (msg.type === 'system' && msg.subtype === 'init') {
        sessionId = msg.session_id; // セッションIDを保存
      }
    }
  }

  // セッション2: 再開して記憶を確認
  {
    await using session = unstable_v2_resumeSession(sessionId!, { model: 'sonnet' });
    await session.send('What is my favorite color?');
    for await (const msg of session.stream()) {
      if (msg.type === 'assistant') {
        const text = msg.message.content.find(
          (c): c is { type: 'text'; text: string } => c.type === 'text'
        );
        console.log(`Resumed: ${text?.text}`);
      }
    }
  }
}
```

## ポイント

- `await using` で自動クリーンアップ（TypeScript 5.2+ Disposable）
- `send()` → `stream()` の繰り返しで自然なマルチターン
- `session_id` を保存すれば後からセッション再開可能
- `unstable_v2_prompt()` はワンショット用の便利関数
