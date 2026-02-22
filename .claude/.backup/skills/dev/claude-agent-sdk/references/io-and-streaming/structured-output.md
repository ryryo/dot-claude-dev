# 構造化出力

エージェントから型安全なJSON出力を取得する。JSON Schemaで形状を定義し、`outputFormat` / `output_format`オプションで渡す。

## 設定

| 言語 | オプション名 | 設定値 |
|---|---|---|
| TypeScript | `outputFormat` | `{ type: 'json_schema', schema: <JSONSchemaオブジェクト> }` |
| Python | `output_format` | `{ type: 'json_schema', schema: <JSONSchemaオブジェクト> }` |

サポートされるJSON Schema機能: object, array, string, number, boolean, null, `enum`, `const`, `required`, ネストされたオブジェクト, `$ref`定義。

## 基本例 (JSON Schema)

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk'

// 返してほしいデータの形状を定義
const schema = {
  type: 'object',
  properties: {
    company_name: { type: 'string' },
    founded_year: { type: 'number' },
    headquarters: { type: 'string' }
  },
  required: ['company_name']
}

for await (const message of query({
  prompt: 'Research Anthropic and provide key company information',
  options: {
    outputFormat: {
      type: 'json_schema',
      schema: schema
    }
  }
})) {
  // 結果メッセージにはバリデーション済みデータを含むstructured_outputが含まれる
  if (message.type === 'result' && message.structured_output) {
    console.log(message.structured_output)
    // { company_name: "Anthropic", founded_year: 2021, headquarters: "San Francisco, CA" }
  }
}
```

## 型安全なスキーマ: Zod (TypeScript) / Pydantic (Python)

JSON Schemaを手書きする代わりに、Zod/Pydanticでスキーマを定義し、完全な型推論・ランタイムバリデーション・より良いエラーメッセージ・組み合わせ可能で再利用可能なスキーマを得られる。

```typescript
import { z } from 'zod'
import { query } from '@anthropic-ai/claude-agent-sdk'

// Zodでスキーマを定義
const FeaturePlan = z.object({
  feature_name: z.string(),
  summary: z.string(),
  steps: z.array(z.object({
    step_number: z.number(),
    description: z.string(),
    estimated_complexity: z.enum(['low', 'medium', 'high'])
  })),
  risks: z.array(z.string())
})

type FeaturePlan = z.infer<typeof FeaturePlan>

// JSON Schemaに変換
const schema = z.toJSONSchema(FeaturePlan)

// クエリで使用
for await (const message of query({
  prompt: 'Plan how to add dark mode support to a React app. Break it into implementation steps.',
  options: {
    outputFormat: {
      type: 'json_schema',
      schema: schema
    }
  }
})) {
  if (message.type === 'result' && message.structured_output) {
    // バリデーションして完全に型付けされた結果を取得
    const parsed = FeaturePlan.safeParse(message.structured_output)
    if (parsed.success) {
      const plan: FeaturePlan = parsed.data
      console.log(`Feature: ${plan.feature_name}`)
      console.log(`Summary: ${plan.summary}`)
      plan.steps.forEach(step => {
        console.log(`${step.step_number}. [${step.estimated_complexity}] ${step.description}`)
      })
    }
  }
}
```

## マルチステップ例: TODOトラッキングエージェント

エージェントがツール（Grep, Bash）を自律的に使用しながら、結果を構造化出力にまとめる例。

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk'

// TODO抽出用の構造を定義
const todoSchema = {
  type: 'object',
  properties: {
    todos: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          text: { type: 'string' },
          file: { type: 'string' },
          line: { type: 'number' },
          author: { type: 'string' },
          date: { type: 'string' }
        },
        required: ['text', 'file', 'line']
      }
    },
    total_count: { type: 'number' }
  },
  required: ['todos', 'total_count']
}

// エージェントはGrepでTODOを検索し、Bashでgit blame情報を取得
for await (const message of query({
  prompt: 'Find all TODO comments in this codebase and identify who added them',
  options: {
    outputFormat: {
      type: 'json_schema',
      schema: todoSchema
    }
  }
})) {
  if (message.type === 'result' && message.structured_output) {
    const data = message.structured_output
    console.log(`Found ${data.total_count} TODOs`)
    data.todos.forEach(todo => {
      console.log(`${todo.file}:${todo.line} - ${todo.text}`)
      if (todo.author) {
        console.log(`  Added by ${todo.author} on ${todo.date}`)
      }
    })
  }
}
```

## 構造化出力のエラーハンドリング

| subtype | 意味 |
|---|---|
| `success` | 出力が正常に生成され、バリデーションされた |
| `error_max_structured_output_retries` | エージェントが複数回の試行後も有効な出力を生成できなかった |

```typescript
for await (const msg of query({
  prompt: 'Extract contact info from the document',
  options: {
    outputFormat: {
      type: 'json_schema',
      schema: contactSchema
    }
  }
})) {
  if (msg.type === 'result') {
    if (msg.subtype === 'success' && msg.structured_output) {
      // バリデーション済みの出力を使用
      console.log(msg.structured_output)
    } else if (msg.subtype === 'error_max_structured_output_retries') {
      // 失敗を処理 - よりシンプルなプロンプトでリトライ、非構造化にフォールバックなど
      console.error('Could not produce valid output')
    }
  }
}
```

**エラーを避けるためのヒント:**
- スキーマを焦点を絞ったものにする。シンプルに始めて、必要に応じて複雑さを追加する。
- スキーマをタスクに合わせる。情報が得られない可能性があるフィールドはオプションにする。
- 明確なプロンプトを使用する。
