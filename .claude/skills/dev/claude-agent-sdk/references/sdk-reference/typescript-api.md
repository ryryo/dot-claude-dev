# TypeScript SDK

## TypeScript SDK V1

### `query()`

Claude Codeとやり取りするための主要な関数。メッセージをストリーミングする非同期ジェネレーターを返す。

```
function query({
  prompt,
  options
}: {
  prompt: string | AsyncIterable<SDKUserMessage>;
  options?: Options;
}): Query
```

**パラメータ:**

| パラメータ | 型 | 説明 |
|-----------|---|------|
| `prompt` | `string \| AsyncIterable<SDKUserMessage>` | 入力プロンプト、またはストリーミング用の非同期イテラブル |
| `options` | `Options` | 設定オブジェクト |

**戻り値:** `Query`（`AsyncGenerator<SDKMessage, void>` を拡張）

### `Query` インターフェース

```
interface Query extends AsyncGenerator<SDKMessage, void> {
  interrupt(): Promise<void>;
  rewindFiles(userMessageUuid: string): Promise<void>;
  setPermissionMode(mode: PermissionMode): Promise<void>;
  setModel(model?: string): Promise<void>;
  setMaxThinkingTokens(maxThinkingTokens: number | null): Promise<void>;
  supportedCommands(): Promise<SlashCommand[]>;
  supportedModels(): Promise<ModelInfo[]>;
  mcpServerStatus(): Promise<McpServerStatus[]>;
  accountInfo(): Promise<AccountInfo>;
}
```

| メソッド | 説明 |
|---------|------|
| `interrupt()` | クエリを中断する（ストリーミング入力モードでのみ） |
| `rewindFiles(userMessageUuid)` | ファイルを指定時点の状態に復元。`enableFileCheckpointing: true` が必要 |
| `setPermissionMode()` | パーミッションモードを変更（ストリーミング入力モードでのみ） |
| `setModel()` | モデルを変更（ストリーミング入力モードでのみ） |
| `setMaxThinkingTokens()` | 最大思考トークン数を変更（ストリーミング入力モードでのみ） |
| `supportedCommands()` | 利用可能なスラッシュコマンドを返す |
| `supportedModels()` | 利用可能なモデルを返す |
| `mcpServerStatus()` | 接続されたMCPサーバーのステータスを返す |
| `accountInfo()` | アカウント情報を返す |

---

## TypeScript SDK V2（プレビュー）

> V2 インターフェースは **不安定なプレビュー**。安定版になる前に API が変更される可能性がある。セッションフォークなどの一部の機能は V1 SDK でのみ利用可能。

V2はマルチターン会話をシンプルにする。APIサーフェスは3つのコンセプトに集約される：

- `createSession()` / `resumeSession()`：会話の開始または継続
- `session.send()`：メッセージの送信
- `session.stream()`：レスポンスの取得

### `unstable_v2_createSession()`

```
function unstable_v2_createSession(options: {
  model: string;
  // 追加オプションをサポート
}): Session
```

### `unstable_v2_resumeSession()`

```
function unstable_v2_resumeSession(
  sessionId: string,
  options: {
    model: string;
    // 追加オプションをサポート
  }
): Session
```

### `unstable_v2_prompt()`

シングルターンクエリ用のワンショット便利関数。

```
function unstable_v2_prompt(
  prompt: string,
  options: {
    model: string;
    // 追加オプションをサポート
  }
): Promise<Result>
```

### Session インターフェース

```
interface Session {
  send(message: string): Promise<void>;
  stream(): AsyncGenerator<SDKMessage>;
  close(): void;
}
```

### V2 コード例

**ワンショットプロンプト:**
```
import { unstable_v2_prompt } from '@anthropic-ai/claude-agent-sdk'

const result = await unstable_v2_prompt('What is 2 + 2?', {
  model: 'claude-opus-4-6'
})
console.log(result.result)
```

**基本的なセッション:**
```
import { unstable_v2_createSession } from '@anthropic-ai/claude-agent-sdk'

await using session = unstable_v2_createSession({
  model: 'claude-opus-4-6'
})

await session.send('Hello!')
for await (const msg of session.stream()) {
  if (msg.type === 'assistant') {
    const text = msg.message.content
      .filter(block => block.type === 'text')
      .map(block => block.text)
      .join('')
    console.log(text)
  }
}
```

**マルチターン会話:**
```
import { unstable_v2_createSession } from '@anthropic-ai/claude-agent-sdk'

await using session = unstable_v2_createSession({
  model: 'claude-opus-4-6'
})

// ターン 1
await session.send('What is 5 + 3?')
for await (const msg of session.stream()) {
  if (msg.type === 'assistant') {
    const text = msg.message.content
      .filter(block => block.type === 'text')
      .map(block => block.text)
      .join('')
    console.log(text)
  }
}

// ターン 2
await session.send('Multiply that by 2')
for await (const msg of session.stream()) {
  if (msg.type === 'assistant') {
    const text = msg.message.content
      .filter(block => block.type === 'text')
      .map(block => block.text)
      .join('')
    console.log(text)
  }
}
```

**セッションの再開:**
```
import {
  unstable_v2_createSession,
  unstable_v2_resumeSession,
  type SDKMessage
} from '@anthropic-ai/claude-agent-sdk'

function getAssistantText(msg: SDKMessage): string | null {
  if (msg.type !== 'assistant') return null
  return msg.message.content
    .filter(block => block.type === 'text')
    .map(block => block.text)
    .join('')
}

const session = unstable_v2_createSession({
  model: 'claude-opus-4-6'
})

await session.send('Remember this number: 42')

let sessionId: string | undefined
for await (const msg of session.stream()) {
  sessionId = msg.session_id
  const text = getAssistantText(msg)
  if (text) console.log('Initial response:', text)
}

console.log('Session ID:', sessionId)
session.close()

await using resumedSession = unstable_v2_resumeSession(sessionId!, {
  model: 'claude-opus-4-6'
})

await resumedSession.send('What number did I ask you to remember?')
for await (const msg of resumedSession.stream()) {
  const text = getAssistantText(msg)
  if (text) console.log('Resumed response:', text)
}
```

**クリーンアップ - 自動（TypeScript 5.2+）:**
```
import { unstable_v2_createSession } from '@anthropic-ai/claude-agent-sdk'

await using session = unstable_v2_createSession({
  model: 'claude-opus-4-6'
})
// ブロックを抜けるとセッションが自動的に閉じられる
```

**クリーンアップ - 手動:**
```
import { unstable_v2_createSession } from '@anthropic-ai/claude-agent-sdk'

const session = unstable_v2_createSession({
  model: 'claude-opus-4-6'
})
// ... セッションを使用 ...
session.close()
```
