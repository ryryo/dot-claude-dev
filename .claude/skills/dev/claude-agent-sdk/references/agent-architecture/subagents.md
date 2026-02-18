# サブエージェント

サブエージェントは、メインエージェントが集中的なサブタスクを処理するために生成できる個別のエージェントインスタンス。コンテキストの分離、タスクの並列実行、専門的な指示の適用を行う。

## 作成方法

| 方式 | 説明 |
|:-----|:-----|
| **プログラム的**（推奨） | `query()` オプションの `agents` パラメータで定義 |
| **ファイルシステムベース** | `.claude/agents/` ディレクトリにマークダウンファイルとして定義 |
| **組み込み汎用** | `Task` ツールを許可すれば、定義なしで `general-purpose` サブエージェントを呼び出し可能 |

プログラム的に定義されたエージェントは、同じ名前のファイルシステムベースのエージェントよりも優先される。

## サブエージェントの利点

- **コンテキスト管理**: メインエージェントとは別のコンテキストを維持し、情報過多を防止
- **並列化**: 複数のサブエージェントを同時実行し、ワークフローを高速化
- **専門的な指示と知識**: カスタマイズされたシステムプロンプトで特定の専門知識を付与
- **ツール制限**: 特定のツールに制限し、意図しないアクションのリスクを軽減

## AgentDefinition設定

| フィールド | 型 | 必須 | 説明 |
|:------|:-----|:---------|:------------|
| `description` | `string` | はい | このエージェントをいつ使用するかの自然言語による説明 |
| `prompt` | `string` | はい | エージェントの役割と動作を定義するシステムプロンプト |
| `tools` | `string[]` | いいえ | 許可されたツール名の配列。省略した場合、すべてのツールを継承 |
| `model` | `'sonnet' \| 'opus' \| 'haiku' \| 'inherit'` | いいえ | モデルオーバーライド。省略した場合はメインモデルがデフォルト |

**制約**: サブエージェントは独自のサブエージェントを生成できない。`tools` 配列に `Task` を含めないこと。

## コード例: プログラム的定義

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

async def main():
    async for message in query(
        prompt="Review the authentication module for security issues",
        options=ClaudeAgentOptions(
            # Task tool is required for subagent invocation
            allowed_tools=["Read", "Grep", "Glob", "Task"],
            agents={
                "code-reviewer": AgentDefinition(
                    description="Expert code review specialist. Use for quality, security, and maintainability reviews.",
                    prompt="""You are a code review specialist with expertise in security, performance, and best practices.

When reviewing code:
- Identify security vulnerabilities
- Check for performance issues
- Verify adherence to coding standards
- Suggest specific improvements

Be thorough but concise in your feedback.""",
                    tools=["Read", "Grep", "Glob"],
                    model="sonnet"
                ),
                "test-runner": AgentDefinition(
                    description="Runs and analyzes test suites. Use for test execution and coverage analysis.",
                    prompt="""You are a test execution specialist. Run tests and provide clear analysis of results.

Focus on:
- Running test commands
- Analyzing test output
- Identifying failing tests
- Suggesting fixes for failures""",
                    tools=["Bash", "Read", "Grep"]
                )
            }
        )
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

for await (const message of query({
  prompt: "Review the authentication module for security issues",
  options: {
    allowedTools: ['Read', 'Grep', 'Glob', 'Task'],
    agents: {
      'code-reviewer': {
        description: 'Expert code review specialist. Use for quality, security, and maintainability reviews.',
        prompt: `You are a code review specialist with expertise in security, performance, and best practices.

When reviewing code:
- Identify security vulnerabilities
- Check for performance issues
- Verify adherence to coding standards
- Suggest specific improvements

Be thorough but concise in your feedback.`,
        tools: ['Read', 'Grep', 'Glob'],
        model: 'sonnet'
      },
      'test-runner': {
        description: 'Runs and analyzes test suites. Use for test execution and coverage analysis.',
        prompt: `You are a test execution specialist. Run tests and provide clear analysis of results.

Focus on:
- Running test commands
- Analyzing test output
- Identifying failing tests
- Suggesting fixes for failures`,
        tools: ['Bash', 'Read', 'Grep'],
      }
    }
  }
})) {
  if ('result' in message) console.log(message.result);
}
```

## 動的エージェント設定

実行時の条件に基づいてエージェント定義を動的に作成できる。

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

def create_security_agent(security_level: str) -> AgentDefinition:
    is_strict = security_level == "strict"
    return AgentDefinition(
        description="Security code reviewer",
        prompt=f"You are a {'strict' if is_strict else 'balanced'} security reviewer...",
        tools=["Read", "Grep", "Glob"],
        model="opus" if is_strict else "sonnet"
    )

async def main():
    async for message in query(
        prompt="Review this PR for security issues",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Grep", "Glob", "Task"],
            agents={
                "security-reviewer": create_security_agent("strict")
            }
        )
    ):
        if hasattr(message, "result"):
            print(message.result)
```

```typescript
import { query, type AgentDefinition } from '@anthropic-ai/claude-agent-sdk';

function createSecurityAgent(securityLevel: 'basic' | 'strict'): AgentDefinition {
  const isStrict = securityLevel === 'strict';
  return {
    description: 'Security code reviewer',
    prompt: `You are a ${isStrict ? 'strict' : 'balanced'} security reviewer...`,
    tools: ['Read', 'Grep', 'Glob'],
    model: isStrict ? 'opus' : 'sonnet'
  };
}

for await (const message of query({
  prompt: "Review this PR for security issues",
  options: {
    allowedTools: ['Read', 'Grep', 'Glob', 'Task'],
    agents: {
      'security-reviewer': createSecurityAgent('strict')
    }
  }
})) {
  if ('result' in message) console.log(message.result);
}
```

## 一般的なツールの組み合わせ

| ユースケース | ツール | 説明 |
|:---------|:------|:------------|
| 読み取り専用分析 | `Read`, `Grep`, `Glob` | コードを調査できるが、変更や実行はできない |
| テスト実行 | `Bash`, `Read`, `Grep` | コマンドを実行して出力を分析できる |
| コード変更 | `Read`, `Edit`, `Write`, `Grep`, `Glob` | コマンド実行なしの完全な読み書きアクセス |
| フルアクセス | すべてのツール | 親からすべてのツールを継承（`tools` フィールドを省略） |

## 呼び出し方式

- **自動呼び出し**: Claudeがタスクと各サブエージェントの `description` に基づいて自動判断
- **明示的呼び出し**: プロンプトで名前を指定（例: `"Use the code-reviewer agent to check the authentication module"`）

## サブエージェント呼び出しの検出

サブエージェントはTaskツールを介して呼び出される。`name: "Task"` を持つ `tool_use` ブロックを確認する。サブエージェントのコンテキスト内からのメッセージには `parent_tool_use_id` フィールドが含まれる。

```python
async for message in query(
    prompt="Use the code-reviewer agent to review this codebase",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep", "Task"],
        agents={
            "code-reviewer": AgentDefinition(
                description="Expert code reviewer.",
                prompt="Analyze code quality and suggest improvements.",
                tools=["Read", "Glob", "Grep"]
            )
        }
    )
):
    if hasattr(message, 'content') and message.content:
        for block in message.content:
            if getattr(block, 'type', None) == 'tool_use' and block.name == 'Task':
                print(f"Subagent invoked: {block.input.get('subagent_type')}")

    if hasattr(message, 'parent_tool_use_id') and message.parent_tool_use_id:
        print("  (running inside subagent)")
```

## サブエージェントの再開

サブエージェントは中断したところから続行するために再開できる。完全な会話履歴を保持する。

1. **セッションIDのキャプチャ**: メッセージから `session_id` を抽出
2. **エージェントIDの抽出**: メッセージコンテンツから `agentId` を解析
3. **セッションの再開**: `resume: sessionId` を渡し、プロンプトにエージェントIDを含める

```typescript
import { query, type SDKMessage } from '@anthropic-ai/claude-agent-sdk';

function extractAgentId(message: SDKMessage): string | undefined {
  if (!('message' in message)) return undefined;
  const content = JSON.stringify(message.message.content);
  const match = content.match(/agentId:\s*([a-f0-9-]+)/);
  return match?.[1];
}

let agentId: string | undefined;
let sessionId: string | undefined;

// First invocation
for await (const message of query({
  prompt: "Use the Explore agent to find all API endpoints in this codebase",
  options: { allowedTools: ['Read', 'Grep', 'Glob', 'Task'] }
})) {
  if ('session_id' in message) sessionId = message.session_id;
  const extractedId = extractAgentId(message);
  if (extractedId) agentId = extractedId;
  if ('result' in message) console.log(message.result);
}

// Second invocation - resume and ask follow-up
if (agentId && sessionId) {
  for await (const message of query({
    prompt: `Resume agent ${agentId} and list the top 3 most complex endpoints`,
    options: { allowedTools: ['Read', 'Grep', 'Glob', 'Task'], resume: sessionId }
  })) {
    if ('result' in message) console.log(message.result);
  }
}
```

**永続性に関する注意**:
- メイン会話がコンパクションされても、サブエージェントのトランスクリプトは影響を受けない
- トランスクリプトはセッション内で永続化される
- 自動クリーンアップは `cleanupPeriodDays` 設定（デフォルト: 30日）に基づく
