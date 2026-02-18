# #7 ドキュメント自動生成ツール

**何を作れるか**: Web検索で人物・テーマの情報を収集し、テンプレートに基づいてドキュメント（.docx, PDF等）を自動生成するCLIツール。

**デモソース**: [resume-generator](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/resume-generator)

## アーキテクチャ

```
CLI引数（人名等） → query()
    → WebSearch でリサーチ
    → Skill でドキュメントテンプレート読み込み
    → Bash/Write で.docx/.pdf生成
    → 完成ファイルパスを出力
```

**SDK主要機能**: `query()`, `settingSources`, `Skill`, `WebSearch`, `systemPrompt`

## コード例: リサーチ＋ドキュメント生成（TypeScript）

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

const SYSTEM_PROMPT = `You are a professional resume writer.
Research a person and create a 1-page .docx resume.

WORKFLOW:
1. WebSearch for the person's background
2. Create a .docx file using the docx library

OUTPUT: agent/custom_scripts/resume.docx`;

async function generateResume(personName: string) {
  const q = query({
    prompt: `Research "${personName}" and create a professional resume.`,
    options: {
      maxTurns: 30,
      cwd: process.cwd(),
      model: 'sonnet',
      allowedTools: ['Skill', 'WebSearch', 'WebFetch', 'Bash', 'Write', 'Read', 'Glob'],
      settingSources: ['project'],  // .claude/skills/ からドキュメント生成スキルを読み込み
      systemPrompt: SYSTEM_PROMPT,
    },
  });

  for await (const msg of q) {
    if (msg.type === 'assistant' && msg.message) {
      for (const block of msg.message.content) {
        if (block.type === 'text') console.log(block.text);
        if (block.type === 'tool_use') {
          console.log(`Using tool: ${block.name}`);
          if (block.name === 'WebSearch' && block.input?.query) {
            console.log(`  Searching: "${block.input.query}"`);
          }
        }
      }
    }
    // result メッセージでコストと所要時間を取得
    if (msg.type === 'result' && msg.subtype === 'tool_result') {
      const result = JSON.stringify(msg.content).slice(0, 200);
      console.log(`  Result: ${result}`);
    }
  }
}
```

## ポイント

- `systemPrompt` でエージェントの役割とワークフローを明確に定義
- `settingSources: ['project']` で `.claude/skills/` のドキュメント生成スキルを活用
- `WebSearch` → `Bash`（ライブラリでファイル生成）→ `Write` の自然なワークフロー
- ツール使用状況をリアルタイムにコンソール出力して進捗を可視化
