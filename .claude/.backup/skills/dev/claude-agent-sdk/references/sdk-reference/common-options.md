# 共通オプション・権限システム・設定ソース・サンドボックス設定

## 共通オプション

### Python: `ClaudeAgentOptions`

```
@dataclass
class ClaudeAgentOptions:
    tools: list[str] | ToolsPreset | None = None
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    max_budget_usd: float | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    fallback_model: str | None = None
    betas: list[SdkBeta] = field(default_factory=list)
    output_format: OutputFormat | None = None
    permission_prompt_tool_name: str | None = None
    cwd: str | Path | None = None
    cli_path: str | Path | None = None
    settings: str | None = None
    add_dirs: list[str | Path] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    extra_args: dict[str, str | None] = field(default_factory=dict)
    max_buffer_size: int | None = None
    debug_stderr: Any = sys.stderr  # Deprecated
    stderr: Callable[[str], None] | None = None
    can_use_tool: CanUseTool | None = None
    hooks: dict[HookEvent, list[HookMatcher]] | None = None
    user: str | None = None
    include_partial_messages: bool = False
    fork_session: bool = False
    agents: dict[str, AgentDefinition] | None = None
    setting_sources: list[SettingSource] | None = None
    max_thinking_tokens: int | None = None
```

### TypeScript: `Options`

| プロパティ | 型 | デフォルト | 説明 |
|-----------|---|----------|------|
| `abortController` | `AbortController` | `new AbortController()` | 操作をキャンセルするためのコントローラー |
| `additionalDirectories` | `string[]` | `[]` | Claudeがアクセスできる追加ディレクトリ |
| `agents` | `Record<string, AgentDefinition>` | `undefined` | プログラムでサブエージェントを定義 |
| `allowDangerouslySkipPermissions` | `boolean` | `false` | `permissionMode: 'bypassPermissions'` 使用時に必須 |
| `allowedTools` | `string[]` | 全ツール | 許可されたツール名のリスト |
| `betas` | `SdkBeta[]` | `[]` | ベータ機能を有効にする |
| `canUseTool` | `CanUseTool` | `undefined` | ツール使用のカスタムパーミッション関数 |
| `continue` | `boolean` | `false` | 最新の会話を続行 |
| `cwd` | `string` | `process.cwd()` | 現在の作業ディレクトリ |
| `disallowedTools` | `string[]` | `[]` | 禁止されたツール名のリスト |
| `enableFileCheckpointing` | `boolean` | `false` | 巻き戻し用のファイル変更追跡を有効にする |
| `env` | `Dict<string>` | `process.env` | 環境変数 |
| `executable` | `'bun' \| 'deno' \| 'node'` | 自動検出 | 使用するJavaScriptランタイム |
| `executableArgs` | `string[]` | `[]` | 実行ファイルに渡す引数 |
| `extraArgs` | `Record<string, string \| null>` | `{}` | 追加の引数 |
| `fallbackModel` | `string` | `undefined` | プライマリが失敗した場合に使用するモデル |
| `forkSession` | `boolean` | `false` | `resume` で再開する際にフォーク |
| `hooks` | `Partial<Record<HookEvent, HookCallbackMatcher[]>>` | `{}` | イベント用のフックコールバック |
| `includePartialMessages` | `boolean` | `false` | 部分メッセージイベントを含める |
| `maxBudgetUsd` | `number` | `undefined` | クエリの最大予算（USD） |
| `maxThinkingTokens` | `number` | `undefined` | 思考プロセスの最大トークン数 |
| `maxTurns` | `number` | `undefined` | 最大会話ターン数 |
| `mcpServers` | `Record<string, McpServerConfig>` | `{}` | MCPサーバーの設定 |
| `model` | `string` | CLIのデフォルト | 使用するClaudeモデル |
| `outputFormat` | `{ type: 'json_schema', schema: JSONSchema }` | `undefined` | エージェント結果の出力フォーマット（構造化出力） |
| `pathToClaudeCodeExecutable` | `string` | 組み込み実行ファイル | Claude Code実行ファイルへのパス |
| `permissionMode` | `PermissionMode` | `'default'` | セッションのパーミッションモード |
| `permissionPromptToolName` | `string` | `undefined` | パーミッションプロンプト用のMCPツール名 |
| `plugins` | `SdkPluginConfig[]` | `[]` | ローカルパスからカスタムプラグインを読み込む |
| `resume` | `string` | `undefined` | 再開するセッションID |
| `resumeSessionAt` | `string` | `undefined` | 特定のメッセージUUIDでセッションを再開 |
| `sandbox` | `SandboxSettings` | `undefined` | サンドボックスの動作をプログラムで設定 |
| `settingSources` | `SettingSource[]` | `[]`（設定なし） | 読み込むファイルシステム設定を制御 |
| `stderr` | `(data: string) => void` | `undefined` | stderr出力のコールバック |
| `strictMcpConfig` | `boolean` | `false` | 厳密なMCPバリデーションを強制 |
| `systemPrompt` | `string \| { type: 'preset'; preset: 'claude_code'; append?: string }` | `undefined` | システムプロンプトの設定 |
| `tools` | `string[] \| { type: 'preset'; preset: 'claude_code' }` | `undefined` | ツールの設定 |

### `OutputFormat`

**Python:**
```
class OutputFormat(TypedDict):
    type: Literal["json_schema"]
    schema: dict[str, Any]
```

**TypeScript:**
```
{ type: 'json_schema', schema: JSONSchema }
```

### `SystemPromptPreset`

**Python:**
```
class SystemPromptPreset(TypedDict):
    type: Literal["preset"]
    preset: Literal["claude_code"]
    append: NotRequired[str]
```

**TypeScript:**
```
{ type: 'preset'; preset: 'claude_code'; append?: string }
```

### `PermissionMode`

**Python:**
```
PermissionMode = Literal[
    "default",           # 標準の権限動作
    "acceptEdits",       # ファイル編集を自動承認
    "plan",              # 計画モード - 実行なし
    "bypassPermissions"  # すべての権限チェックをバイパス（注意して使用）
]
```

**TypeScript:**
```
type PermissionMode =
  | 'default'
  | 'acceptEdits'
  | 'bypassPermissions'
  | 'plan'
```

### `SdkBeta`

```
SdkBeta = Literal["context-1m-2025-08-07"]
```

| 値 | 説明 | 互換モデル |
|---|------|-----------|
| `'context-1m-2025-08-07'` | 100万トークンのコンテキストウィンドウを有効にする | Claude Opus 4.6、Claude Sonnet 4.5、Claude Sonnet 4 |

---

## 権限システム

### `CanUseTool`

**Python:**
```
CanUseTool = Callable[
    [str, dict[str, Any], ToolPermissionContext],
    Awaitable[PermissionResult]
]
```

コールバックは以下を受け取る：
- `tool_name`: 呼び出されるツールの名前
- `input_data`: ツールの入力パラメータ
- `context`: `ToolPermissionContext`

**TypeScript:**
```
type CanUseTool = (
  toolName: string,
  input: ToolInput,
  options: {
    signal: AbortSignal;
    suggestions?: PermissionUpdate[];
  }
) => Promise<PermissionResult>;
```

### `ToolPermissionContext`（Python）

```
@dataclass
class ToolPermissionContext:
    signal: Any | None = None
    suggestions: list[PermissionUpdate] = field(default_factory=list)
```

### `PermissionResult`

**Python:**
```
PermissionResult = PermissionResultAllow | PermissionResultDeny
```

```
@dataclass
class PermissionResultAllow:
    behavior: Literal["allow"] = "allow"
    updated_input: dict[str, Any] | None = None
    updated_permissions: list[PermissionUpdate] | None = None
```

```
@dataclass
class PermissionResultDeny:
    behavior: Literal["deny"] = "deny"
    message: str = ""
    interrupt: bool = False
```

**TypeScript:**
```
type PermissionResult =
  | {
      behavior: 'allow';
      updatedInput: ToolInput;
      updatedPermissions?: PermissionUpdate[];
    }
  | {
      behavior: 'deny';
      message: string;
      interrupt?: boolean;
    }
```

### `PermissionUpdate`

**Python:**
```
@dataclass
class PermissionUpdate:
    type: Literal[
        "addRules",
        "replaceRules",
        "removeRules",
        "setMode",
        "addDirectories",
        "removeDirectories",
    ]
    rules: list[PermissionRuleValue] | None = None
    behavior: Literal["allow", "deny", "ask"] | None = None
    mode: PermissionMode | None = None
    directories: list[str] | None = None
    destination: Literal["userSettings", "projectSettings", "localSettings", "session"] | None = None
```

**TypeScript:**
```
type PermissionUpdate =
  | {
      type: 'addRules';
      rules: PermissionRuleValue[];
      behavior: PermissionBehavior;
      destination: PermissionUpdateDestination;
    }
  | {
      type: 'replaceRules';
      rules: PermissionRuleValue[];
      behavior: PermissionBehavior;
      destination: PermissionUpdateDestination;
    }
  | {
      type: 'removeRules';
      rules: PermissionRuleValue[];
      behavior: PermissionBehavior;
      destination: PermissionUpdateDestination;
    }
  | {
      type: 'setMode';
      mode: PermissionMode;
      destination: PermissionUpdateDestination;
    }
  | {
      type: 'addDirectories';
      directories: string[];
      destination: PermissionUpdateDestination;
    }
  | {
      type: 'removeDirectories';
      directories: string[];
      destination: PermissionUpdateDestination;
    }
```

**TypeScript 追加型:**
```
type PermissionBehavior = 'allow' | 'deny' | 'ask';

type PermissionUpdateDestination =
  | 'userSettings'
  | 'projectSettings'
  | 'localSettings'
  | 'session'

type PermissionRuleValue = {
  toolName: string;
  ruleContent?: string;
}
```

---

## 設定ソース

### `SettingSource`

**Python:**
```
SettingSource = Literal["user", "project", "local"]
```

**TypeScript:**
```
type SettingSource = 'user' | 'project' | 'local';
```

| 値 | 説明 | 場所 |
|---|------|------|
| `"user"` | グローバルユーザー設定 | `~/.claude/settings.json` |
| `"project"` | 共有プロジェクト設定（バージョン管理対象） | `.claude/settings.json` |
| `"local"` | ローカルプロジェクト設定（gitignore対象） | `.claude/settings.local.json` |

#### デフォルトの動作

`setting_sources` / `settingSources` が省略または `None`/`undefined` の場合、SDKはファイルシステム設定を読み込まない。SDKアプリケーションの分離が提供される。

#### 設定の優先順位

複数のソースが読み込まれる場合（高い順）：
1. ローカル設定（`.claude/settings.local.json`）
2. プロジェクト設定（`.claude/settings.json`）
3. ユーザー設定（`~/.claude/settings.json`）

プログラムオプション（`agents`、`allowed_tools` など）は常にファイルシステム設定を上書きする。

#### 使用例

**すべてのファイルシステム設定を読み込む（レガシー動作）:**

Python:
```
async for message in query(
    prompt="Analyze this code",
    options=ClaudeAgentOptions(
        setting_sources=["user", "project", "local"]
    )
):
    print(message)
```

TypeScript:
```
const result = query({
  prompt: "Analyze this code",
  options: {
    settingSources: ['user', 'project', 'local']
  }
});
```

**CLAUDE.mdプロジェクト指示の読み込み:**

Python:
```
async for message in query(
    prompt="Add a new feature following project conventions",
    options=ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code"
        },
        setting_sources=["project"],
        allowed_tools=["Read", "Write", "Edit"]
    )
):
    print(message)
```

TypeScript:
```
const result = query({
  prompt: "Add a new feature following project conventions",
  options: {
    systemPrompt: {
      type: 'preset',
      preset: 'claude_code'
    },
    settingSources: ['project'],
    allowedTools: ['Read', 'Write', 'Edit']
  }
});
```

---

## サンドボックス設定

### `SandboxSettings`

**Python:**
```
class SandboxSettings(TypedDict, total=False):
    enabled: bool
    autoAllowBashIfSandboxed: bool
    excludedCommands: list[str]
    allowUnsandboxedCommands: bool
    network: SandboxNetworkConfig
    ignoreViolations: SandboxIgnoreViolations
    enableWeakerNestedSandbox: bool
```

**TypeScript:**
```
type SandboxSettings = {
  enabled?: boolean;
  autoAllowBashIfSandboxed?: boolean;
  excludedCommands?: string[];
  allowUnsandboxedCommands?: boolean;
  network?: NetworkSandboxSettings;
  ignoreViolations?: SandboxIgnoreViolations;
  enableWeakerNestedSandbox?: boolean;
}
```

| プロパティ | 型 | デフォルト | 説明 |
|-----------|---|----------|------|
| `enabled` | `bool` | `False` | コマンド実行のサンドボックスモードを有効にする |
| `autoAllowBashIfSandboxed` | `bool` | `False` | サンドボックスが有効な場合にbashコマンドを自動承認する |
| `excludedCommands` | `list[str]` | `[]` | サンドボックス制限を常にバイパスするコマンド |
| `allowUnsandboxedCommands` | `bool` | `False` | モデルがサンドボックス外でのコマンド実行をリクエストすることを許可 |
| `network` | `SandboxNetworkConfig` | `None` | ネットワーク固有のサンドボックス設定 |
| `ignoreViolations` | `SandboxIgnoreViolations` | `None` | 無視するサンドボックス違反の設定 |
| `enableWeakerNestedSandbox` | `bool` | `False` | 互換性のためにより弱いネストされたサンドボックスを有効にする |

**ファイルシステムとネットワークのアクセス制限** はサンドボックス設定では設定しない。代わりにパーミッションルールから導出される：
- ファイルシステム読み取り制限：読み取り拒否ルール
- ファイルシステム書き込み制限：編集許可/拒否ルール
- ネットワーク制限：WebFetch許可/拒否ルール

### `SandboxNetworkConfig` / `NetworkSandboxSettings`

**Python:**
```
class SandboxNetworkConfig(TypedDict, total=False):
    allowLocalBinding: bool
    allowUnixSockets: list[str]
    allowAllUnixSockets: bool
    httpProxyPort: int
    socksProxyPort: int
```

**TypeScript:**
```
type NetworkSandboxSettings = {
  allowLocalBinding?: boolean;
  allowUnixSockets?: string[];
  allowAllUnixSockets?: boolean;
  httpProxyPort?: number;
  socksProxyPort?: number;
}
```

| プロパティ | 型 | デフォルト | 説明 |
|-----------|---|----------|------|
| `allowLocalBinding` | `bool` | `False` | プロセスがローカルポートにバインドすることを許可 |
| `allowUnixSockets` | `list[str]` | `[]` | アクセスできるUnixソケットパス |
| `allowAllUnixSockets` | `bool` | `False` | すべてのUnixソケットへのアクセスを許可 |
| `httpProxyPort` | `int` | `None` | ネットワークリクエスト用のHTTPプロキシポート |
| `socksProxyPort` | `int` | `None` | ネットワークリクエスト用のSOCKSプロキシポート |

> **Unixソケットのセキュリティ:** `allowUnixSockets` は強力なシステムサービスへのアクセスを許可する可能性がある。例えば `/var/run/docker.sock` を許可するとDocker APIを通じてホストシステムへの完全なアクセスが許可され、サンドボックスの分離がバイパスされる。

### `SandboxIgnoreViolations`

```
file: list[str]     # 違反を無視するファイルパスパターン
network: list[str]  # 違反を無視するネットワークパターン
```

### `excludedCommands` vs `allowUnsandboxedCommands`

- `excludedCommands`: 常にサンドボックスを自動的にバイパスするコマンドの静的リスト。モデルはこれを制御できない。
- `allowUnsandboxedCommands`: モデルがツール入力で `dangerouslyDisableSandbox: True` を設定することで、実行時にサンドボックス外での実行をリクエストできる。

### サンドボックス使用例

**Python:**
```
from claude_agent_sdk import query, ClaudeAgentOptions, SandboxSettings

sandbox_settings: SandboxSettings = {
    "enabled": True,
    "autoAllowBashIfSandboxed": True,
    "network": {
        "allowLocalBinding": True
    }
}

async for message in query(
    prompt="Build and test my project",
    options=ClaudeAgentOptions(sandbox=sandbox_settings)
):
    print(message)
```

**TypeScript:**
```
import { query } from "@anthropic-ai/claude-agent-sdk";

const result = await query({
  prompt: "Build and test my project",
  options: {
    sandbox: {
      enabled: true,
      autoAllowBashIfSandboxed: true,
      network: {
        allowLocalBinding: true
      }
    }
  }
});
```
