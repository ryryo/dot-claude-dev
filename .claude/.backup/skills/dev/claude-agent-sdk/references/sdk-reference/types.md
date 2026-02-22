# 型定義

## メッセージ型

### Python

```
Message = UserMessage | AssistantMessage | SystemMessage | ResultMessage | StreamEvent
```

#### `UserMessage`
```
@dataclass
class UserMessage:
    content: str | list[ContentBlock]
```

#### `AssistantMessage`
```
@dataclass
class AssistantMessage:
    content: list[ContentBlock]
    model: str
```

#### `SystemMessage`
```
@dataclass
class SystemMessage:
    subtype: str
    data: dict[str, Any]
```

#### `ResultMessage`
```
@dataclass
class ResultMessage:
    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None
    structured_output: Any = None
```

#### `StreamEvent`

`ClaudeAgentOptions` で `include_partial_messages=True` の場合にのみ受信される。

```
@dataclass
class StreamEvent:
    uuid: str
    session_id: str
    event: dict[str, Any]
    parent_tool_use_id: str | None = None
```

### TypeScript

```
type SDKMessage =
  | SDKAssistantMessage
  | SDKUserMessage
  | SDKUserMessageReplay
  | SDKResultMessage
  | SDKSystemMessage
  | SDKPartialAssistantMessage
  | SDKCompactBoundaryMessage;
```

#### `SDKAssistantMessage`
```
type SDKAssistantMessage = {
  type: 'assistant';
  uuid: UUID;
  session_id: string;
  message: APIAssistantMessage;
  parent_tool_use_id: string | null;
}
```

#### `SDKUserMessage`
```
type SDKUserMessage = {
  type: 'user';
  uuid?: UUID;
  session_id: string;
  message: APIUserMessage;
  parent_tool_use_id: string | null;
}
```

#### `SDKResultMessage`
```
type SDKResultMessage =
  | {
      type: 'result';
      subtype: 'success';
      uuid: UUID;
      session_id: string;
      duration_ms: number;
      duration_api_ms: number;
      is_error: boolean;
      num_turns: number;
      result: string;
      total_cost_usd: number;
      usage: NonNullableUsage;
      modelUsage: { [modelName: string]: ModelUsage };
      permission_denials: SDKPermissionDenial[];
      structured_output?: unknown;
    }
  | {
      type: 'result';
      subtype:
        | 'error_max_turns'
        | 'error_during_execution'
        | 'error_max_budget_usd'
        | 'error_max_structured_output_retries';
      uuid: UUID;
      session_id: string;
      duration_ms: number;
      duration_api_ms: number;
      is_error: boolean;
      num_turns: number;
      total_cost_usd: number;
      usage: NonNullableUsage;
      modelUsage: { [modelName: string]: ModelUsage };
      permission_denials: SDKPermissionDenial[];
      errors: string[];
    }
```

#### `SDKSystemMessage`
```
type SDKSystemMessage = {
  type: 'system';
  subtype: 'init';
  uuid: UUID;
  session_id: string;
  apiKeySource: ApiKeySource;
  cwd: string;
  tools: string[];
  mcp_servers: {
    name: string;
    status: string;
  }[];
  model: string;
  permissionMode: PermissionMode;
  slash_commands: string[];
  output_style: string;
}
```

#### `SDKPartialAssistantMessage`

`includePartialMessages` がtrueの場合のみ。

```
type SDKPartialAssistantMessage = {
  type: 'stream_event';
  event: RawMessageStreamEvent;
  parent_tool_use_id: string | null;
  uuid: UUID;
  session_id: string;
}
```

#### `SDKCompactBoundaryMessage`
```
type SDKCompactBoundaryMessage = {
  type: 'system';
  subtype: 'compact_boundary';
  uuid: UUID;
  session_id: string;
  compact_metadata: {
    trigger: 'manual' | 'auto';
    pre_tokens: number;
  };
}
```

#### `SDKPermissionDenial`
```
type SDKPermissionDenial = {
  tool_name: string;
  tool_use_id: string;
  tool_input: ToolInput;
}
```

---

## コンテンツブロック型

### Python

```
ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock
```

#### `TextBlock`
```
@dataclass
class TextBlock:
    text: str
```

#### `ThinkingBlock`
```
@dataclass
class ThinkingBlock:
    thinking: str
    signature: str
```

#### `ToolUseBlock`
```
@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]
```

#### `ToolResultBlock`
```
@dataclass
class ToolResultBlock:
    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None
```

---

## 組み込みツール入出力型

### Task

**ツール名:** `Task`

**入力:**
```
{
    "description": str,      # タスクの短い（3-5語の）説明
    "prompt": str,           # エージェントが実行するタスク
    "subagent_type": str     # 使用する特殊エージェントのタイプ
}
```

**出力:**
```
{
    "result": str,
    "usage": dict | None,
    "total_cost_usd": float | None,
    "duration_ms": int | None
}
```

### AskUserQuestion

**ツール名:** `AskUserQuestion`

**入力:**
```
{
    "questions": [
        {
            "question": str,
            "header": str,            # 最大12文字
            "options": [
                {
                    "label": str,     # 1-5語
                    "description": str
                }
            ],
            "multiSelect": bool
        }
    ],
    "answers": dict | None
}
```

**出力:**
```
{
    "questions": [...],
    "answers": dict[str, str]  # 質問テキスト -> 回答文字列
}
```

### Bash

**ツール名:** `Bash`

**入力:**
```
{
    "command": str,
    "timeout": int | None,           # 最大600000ms
    "description": str | None,       # 5-10語
    "run_in_background": bool | None
}
```

**出力:**
```
{
    "output": str,
    "exitCode": int,
    "killed": bool | None,
    "shellId": str | None
}
```

### Edit

**ツール名:** `Edit`

**入力:**
```
{
    "file_path": str,
    "old_string": str,
    "new_string": str,
    "replace_all": bool | None  # デフォルト False
}
```

**出力:**
```
{
    "message": str,
    "replacements": int,
    "file_path": str
}
```

### Read

**ツール名:** `Read`

**入力:**
```
{
    "file_path": str,
    "offset": int | None,
    "limit": int | None
}
```

**出力（テキストファイル）:**
```
{
    "content": str,
    "total_lines": int,
    "lines_returned": int
}
```

**出力（画像）:**
```
{
    "image": str,       # Base64
    "mime_type": str,
    "file_size": int
}
```

### Write

**ツール名:** `Write`

**入力:**
```
{
    "file_path": str,
    "content": str
}
```

**出力:**
```
{
    "message": str,
    "bytes_written": int,
    "file_path": str
}
```

### Glob

**ツール名:** `Glob`

**入力:**
```
{
    "pattern": str,
    "path": str | None
}
```

**出力:**
```
{
    "matches": list[str],
    "count": int,
    "search_path": str
}
```

### Grep

**ツール名:** `Grep`

**入力:**
```
{
    "pattern": str,
    "path": str | None,
    "glob": str | None,
    "type": str | None,
    "output_mode": str | None,  # "content", "files_with_matches", "count"
    "-i": bool | None,
    "-n": bool | None,
    "-B": int | None,
    "-A": int | None,
    "-C": int | None,
    "head_limit": int | None,
    "multiline": bool | None
}
```

**出力（contentモード）:**
```
{
    "matches": [
        {
            "file": str,
            "line_number": int | None,
            "line": str,
            "before_context": list[str] | None,
            "after_context": list[str] | None
        }
    ],
    "total_matches": int
}
```

**出力（files_with_matchesモード）:**
```
{
    "files": list[str],
    "count": int
}
```

### NotebookEdit

**ツール名:** `NotebookEdit`

**入力:**
```
{
    "notebook_path": str,
    "cell_id": str | None,
    "new_source": str,
    "cell_type": "code" | "markdown" | None,
    "edit_mode": "replace" | "insert" | "delete" | None
}
```

**出力:**
```
{
    "message": str,
    "edit_type": "replaced" | "inserted" | "deleted",
    "cell_id": str | None,
    "total_cells": int
}
```

### WebFetch

**ツール名:** `WebFetch`

**入力:**
```
{
    "url": str,
    "prompt": str
}
```

**出力:**
```
{
    "response": str,
    "url": str,
    "final_url": str | None,
    "status_code": int | None
}
```

### WebSearch

**ツール名:** `WebSearch`

**入力:**
```
{
    "query": str,
    "allowed_domains": list[str] | None,
    "blocked_domains": list[str] | None
}
```

**出力:**
```
{
    "results": [
        {
            "title": str,
            "url": str,
            "snippet": str,
            "metadata": dict | None
        }
    ],
    "total_results": int,
    "query": str
}
```

### TodoWrite

**ツール名:** `TodoWrite`

**入力:**
```
{
    "todos": [
        {
            "content": str,
            "status": "pending" | "in_progress" | "completed",
            "activeForm": str
        }
    ]
}
```

**出力:**
```
{
    "message": str,
    "stats": {
        "total": int,
        "pending": int,
        "in_progress": int,
        "completed": int
    }
}
```

### BashOutput

**ツール名:** `BashOutput`

**入力:**
```
{
    "bash_id": str,
    "filter": str | None
}
```

**出力:**
```
{
    "output": str,
    "status": "running" | "completed" | "failed",
    "exitCode": int | None
}
```

### KillBash

**ツール名:** `KillBash`

**入力:**
```
{
    "shell_id": str
}
```

**出力:**
```
{
    "message": str,
    "shell_id": str
}
```

### ExitPlanMode

**ツール名:** `ExitPlanMode`

**入力:**
```
{
    "plan": str
}
```

**出力:**
```
{
    "message": str,
    "approved": bool | None
}
```

### ListMcpResources

**ツール名:** `ListMcpResources`

**入力:**
```
{
    "server": str | None
}
```

**出力:**
```
{
    "resources": [
        {
            "uri": str,
            "name": str,
            "description": str | None,
            "mimeType": str | None,
            "server": str
        }
    ],
    "total": int
}
```

### ReadMcpResource

**ツール名:** `ReadMcpResource`

**入力:**
```
{
    "server": str,
    "uri": str
}
```

**出力:**
```
{
    "contents": [
        {
            "uri": str,
            "mimeType": str | None,
            "text": str | None,
            "blob": str | None
        }
    ],
    "server": str
}
```

---

## エラー型

### Python エラー型

#### `ClaudeSDKError`
```
class ClaudeSDKError(Exception):
    """Base error for Claude SDK."""
```

#### `CLINotFoundError`
```
class CLINotFoundError(CLIConnectionError):
    def __init__(self, message: str = "Claude Code not found", cli_path: str | None = None):
```

#### `CLIConnectionError`
```
class CLIConnectionError(ClaudeSDKError):
    """Failed to connect to Claude Code."""
```

#### `ProcessError`
```
class ProcessError(ClaudeSDKError):
    def __init__(self, message: str, exit_code: int | None = None, stderr: str | None = None):
        self.exit_code = exit_code
        self.stderr = stderr
```

#### `CLIJSONDecodeError`
```
class CLIJSONDecodeError(ClaudeSDKError):
    def __init__(self, line: str, original_error: Exception):
        self.line = line
        self.original_error = original_error
```

### エラーハンドリング例（Python）
```
from claude_agent_sdk import (
    query,
    CLINotFoundError,
    ProcessError,
    CLIJSONDecodeError
)

try:
    async for message in query(prompt="Hello"):
        print(message)
except CLINotFoundError:
    print("Please install Claude Code: npm install -g @anthropic-ai/claude-code")
except ProcessError as e:
    print(f"Process failed with exit code: {e.exit_code}")
except CLIJSONDecodeError as e:
    print(f"Failed to parse response: {e}")
```

### TypeScript エラー型

#### `AbortError`
```
class AbortError extends Error {}
```

---

## その他の型

### TypeScript 固有の型

#### `SlashCommand`
```
type SlashCommand = {
  name: string;
  description: string;
  argumentHint: string;
}
```

#### `ModelInfo`
```
type ModelInfo = {
  value: string;
  displayName: string;
  description: string;
}
```

#### `McpServerStatus`
```
type McpServerStatus = {
  name: string;
  status: 'connected' | 'failed' | 'needs-auth' | 'pending';
  serverInfo?: {
    name: string;
    version: string;
  };
}
```

#### `AccountInfo`
```
type AccountInfo = {
  email?: string;
  organization?: string;
  subscriptionType?: string;
  tokenSource?: string;
  apiKeySource?: string;
}
```

#### `ModelUsage`
```
type ModelUsage = {
  inputTokens: number;
  outputTokens: number;
  cacheReadInputTokens: number;
  cacheCreationInputTokens: number;
  webSearchRequests: number;
  costUSD: number;
  contextWindow: number;
}
```

#### `ApiKeySource`
```
type ApiKeySource = 'user' | 'project' | 'org' | 'temporary';
```

#### `Usage`
```
type Usage = {
  input_tokens: number | null;
  output_tokens: number | null;
  cache_creation_input_tokens?: number | null;
  cache_read_input_tokens?: number | null;
}
```

#### `CallToolResult`
```
type CallToolResult = {
  content: Array<{
    type: 'text' | 'image' | 'resource';
  }>;
  isError?: boolean;
}
```
