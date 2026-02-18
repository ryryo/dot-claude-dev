# #1 CLIツール（ワンショット実行）

**何を作れるか**: コマンドラインから1回のプロンプトを投げて結果を得るツール。ファイル操作、コード生成、分析タスクなどに最適。

**デモソース**: [hello-world](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/hello-world)

## アーキテクチャ

```
ユーザー → CLI引数/プロンプト → query() → for await → 結果表示
```

**SDK主要機能**: `query()`, `allowedTools`, `maxTurns`, `cwd`, `hooks`

## コード例: 基本的なワンショット実行（TypeScript）

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';
import type { HookJSONOutput } from '@anthropic-ai/claude-agent-sdk';

const q = query({
  prompt: 'Hello, Claude! Please introduce yourself in one sentence.',
  options: {
    maxTurns: 100,
    cwd: path.join(process.cwd(), 'agent'),
    model: 'opus',
    allowedTools: [
      'Task', 'Bash', 'Glob', 'Grep', 'Read', 'Edit', 'Write',
      'WebFetch', 'TodoWrite', 'WebSearch',
    ],
    // PreToolUse フックでファイル書き込み先を制限する例
    hooks: {
      PreToolUse: [
        {
          matcher: 'Write|Edit|MultiEdit',
          hooks: [
            async (input: any): Promise<HookJSONOutput> => {
              const filePath = input.tool_input.file_path || '';
              const ext = path.extname(filePath).toLowerCase();

              if (ext === '.js' || ext === '.ts') {
                const allowedPath = path.join(process.cwd(), 'agent', 'custom_scripts');
                if (!filePath.startsWith(allowedPath)) {
                  return {
                    decision: 'block',
                    stopReason: `Scripts must be in: ${allowedPath}`,
                    continue: false,
                  };
                }
              }
              return { continue: true };
            },
          ],
        },
      ],
    },
  },
});

// ストリーミング出力を消費
for await (const message of q) {
  if (message.type === 'assistant' && message.message) {
    const text = message.message.content.find((c: any) => c.type === 'text');
    if (text && 'text' in text) {
      console.log('Claude:', text.text);
    }
  }
}
```

## ポイント

- `query()` は AsyncIterable を返す。`for await` でストリーミング消費する
- `hooks.PreToolUse` でファイル書き込み先やコマンド実行を制限できる
- `cwd` でエージェントの作業ディレクトリを指定
- `allowedTools` で利用可能なツールを明示的にリスト化
