# フック

フックを使用すると、エージェントの実行を主要なポイントでインターセプトし、バリデーション、ロギング、セキュリティ制御、またはカスタムロジックを追加できる。

## フックの構成要素

1. **コールバック関数**: フックが発火したときに実行されるロジック
2. **フック設定**: SDKにどのイベントにフックするか（`PreToolUse`など）、どのツールにマッチするかを指示する

## 利用可能なフック一覧

| フックイベント | Python SDK | TypeScript SDK | トリガー条件 | ユースケースの例 |
|--------------|-----------|---------------|------------|----------------|
| `PreToolUse` | はい | はい | ツール呼び出しリクエスト（ブロックまたは変更可能） | 危険なシェルコマンドをブロック |
| `PostToolUse` | はい | はい | ツール実行結果 | すべてのファイル変更を監査証跡に記録 |
| `PostToolUseFailure` | いいえ | はい | ツール実行失敗 | ツールエラーの処理またはログ |
| `UserPromptSubmit` | はい | はい | ユーザープロンプトの送信 | プロンプトに追加コンテキストを注入 |
| `Stop` | はい | はい | エージェント実行の停止 | 終了前にセッション状態を保存 |
| `SubagentStart` | いいえ | はい | サブエージェントの初期化 | 並列タスクの生成を追跡 |
| `SubagentStop` | はい | はい | サブエージェントの完了 | 並列タスクからの結果を集約 |
| `PreCompact` | はい | はい | 会話のコンパクション要求 | 要約前に完全なトランスクリプトをアーカイブ |
| `PermissionRequest` | いいえ | はい | 権限ダイアログが表示される場合 | カスタム権限処理 |
| `SessionStart` | いいえ | はい | セッションの初期化 | ロギングとテレメトリの初期化 |
| `SessionEnd` | いいえ | はい | セッションの終了 | 一時リソースのクリーンアップ |
| `Notification` | いいえ | はい | エージェントのステータスメッセージ | Slack/PagerDutyへの送信 |

## フックの設定方法

```python
async for message in query(
    prompt="Your prompt",
    options=ClaudeAgentOptions(
        hooks={
            'PreToolUse': [HookMatcher(matcher='Bash', hooks=[my_callback])]
        }
    )
):
    print(message)
```

`hooks`オプションの構造：
- **キー**: フックイベント名（例：`'PreToolUse'`、`'PostToolUse'`、`'Stop'`）
- **値**: マッチャーの配列。それぞれにオプションのフィルターパターンとコールバック関数が含まれる

## マッチャー設定

| オプション | 型 | デフォルト | 説明 |
|-----------|-----|---------|------|
| `matcher` | `string` | `undefined` | ツール名にマッチする正規表現パターン |
| `hooks` | `HookCallback[]` | - | 必須。パターンがマッチしたときに実行するコールバック関数の配列 |
| `timeout` | `number` | `60` | タイムアウト（秒）。外部API呼び出しを行うフックの場合は増やす |

組み込みツール名: `Bash`、`Read`、`Write`、`Edit`、`Glob`、`Grep`、`WebFetch`、`Task`

MCPツールの命名規則: `mcp__<server>__<action>`（例：`mcp__playwright__browser_screenshot`）

マッチャーはツールベースのフック（`PreToolUse`、`PostToolUse`、`PostToolUseFailure`、`PermissionRequest`）にのみ適用される。`Stop`、`SessionStart`、`Notification`などのライフサイクルフックでは、マッチャーは無視される。

## コールバック関数の入力

すべてのフックコールバックは3つの引数を受け取る：

1. **入力データ**（`dict` / `HookInput`）：イベントの詳細
2. **ツール使用ID**（`str | None` / `string | null`）：`PreToolUse`と`PostToolUse`イベントを関連付ける
3. **コンテキスト**（`HookContext`）：TypeScriptではキャンセル用の`signal`プロパティ（`AbortSignal`）を含む

### 共通フィールド（すべてのフックタイプに存在）

| フィールド | 型 | 説明 |
|----------|-----|------|
| `hook_event_name` | `string` | フックタイプ（`PreToolUse`、`PostToolUse`など） |
| `session_id` | `string` | 現在のセッション識別子 |
| `transcript_path` | `string` | 会話トランスクリプトへのパス |
| `cwd` | `string` | 現在の作業ディレクトリ |

### フック固有のフィールド

| フィールド | 型 | 説明 | 対象フック |
|----------|-----|------|----------|
| `tool_name` | `string` | 呼び出されるツールの名前 | PreToolUse、PostToolUse、PostToolUseFailure(TS)、PermissionRequest(TS) |
| `tool_input` | `object` | ツールに渡される引数 | PreToolUse、PostToolUse、PostToolUseFailure(TS)、PermissionRequest(TS) |
| `tool_response` | `any` | ツール実行から返された結果 | PostToolUse |
| `error` | `string` | ツール実行失敗のエラーメッセージ | PostToolUseFailure(TS) |
| `is_interrupt` | `boolean` | 失敗が割り込みによって引き起こされたか | PostToolUseFailure(TS) |
| `prompt` | `string` | ユーザーのプロンプトテキスト | UserPromptSubmit |
| `stop_hook_active` | `boolean` | ストップフックが処理中か | Stop、SubagentStop |
| `agent_id` | `string` | サブエージェントの一意識別子 | SubagentStart(TS)、SubagentStop(TS) |
| `agent_type` | `string` | サブエージェントのタイプ/ロール | SubagentStart(TS) |
| `agent_transcript_path` | `string` | サブエージェントの会話トランスクリプトへのパス | SubagentStop(TS) |
| `trigger` | `string` | コンパクションのトリガー：`manual`または`auto` | PreCompact |
| `custom_instructions` | `string` | コンパクション用カスタム指示 | PreCompact |
| `permission_suggestions` | `array` | ツールに対する推奨権限更新 | PermissionRequest(TS) |
| `source` | `string` | セッション開始方法：`startup`、`resume`、`clear`、`compact` | SessionStart(TS) |
| `reason` | `string` | セッション終了理由 | SessionEnd(TS) |
| `message` | `string` | エージェントからのステータスメッセージ | Notification(TS) |
| `notification_type` | `string` | 通知タイプ：`permission_prompt`、`idle_prompt`、`auth_success`、`elicitation_dialog` | Notification(TS) |
| `title` | `string` | エージェントによるオプションのタイトル | Notification(TS) |

## コールバックの出力

### トップレベルフィールド（`hookSpecificOutput`の外側）

| フィールド | 型 | 説明 |
|----------|-----|------|
| `continue` | `boolean` | このフックの後にエージェントが続行するか（デフォルト：`true`） |
| `stopReason` | `string` | `continue`が`false`の場合に表示されるメッセージ |
| `suppressOutput` | `boolean` | トランスクリプトからstdoutを非表示にする（デフォルト：`false`） |
| `systemMessage` | `string` | Claudeが参照できるように会話に注入されるメッセージ |

### `hookSpecificOutput`内のフィールド

| フィールド | 型 | 対象フック | 説明 |
|----------|-----|----------|------|
| `hookEventName` | `string` | すべて | 必須。`input.hook_event_name`を使用 |
| `permissionDecision` | `'allow'` \| `'deny'` \| `'ask'` | PreToolUse | ツールが実行されるかどうかを制御 |
| `permissionDecisionReason` | `string` | PreToolUse | 決定に対してClaudeに表示される説明 |
| `updatedInput` | `object` | PreToolUse | 変更されたツール入力（`permissionDecision: 'allow'`が必要） |
| `additionalContext` | `string` | PreToolUse、PostToolUse、UserPromptSubmit、SessionStart(TS)、SubagentStart(TS) | 会話に追加されるコンテキスト |

## 権限決定フロー

複数のフックまたは権限ルールが適用される場合の評価順序：

1. **Deny**ルールが最初にチェック（いずれかがマッチ = 即座に拒否）
2. **Ask**ルールが2番目にチェック
3. **Allow**ルールが3番目にチェック
4. 何もマッチしない場合は**デフォルトでAsk**

いずれかのフックが`deny`を返した場合、操作はブロックされる。他のフックが`allow`を返しても、オーバーライドできない。

## フックパターン集

### .envファイルの保護

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher

async def protect_env_files(input_data, tool_use_id, context):
    file_path = input_data['tool_input'].get('file_path', '')
    file_name = file_path.split('/')[-1]

    if file_name == '.env':
        return {
            'hookSpecificOutput': {
                'hookEventName': input_data['hook_event_name'],
                'permissionDecision': 'deny',
                'permissionDecisionReason': 'Cannot modify .env files'
            }
        }
    return {}

async def main():
    async for message in query(
        prompt="Update the database configuration",
        options=ClaudeAgentOptions(
            hooks={
                'PreToolUse': [HookMatcher(matcher='Write|Edit', hooks=[protect_env_files])]
            }
        )
    ):
        print(message)

asyncio.run(main())
```

### 危険なコマンドのブロック

```python
async def block_dangerous_commands(input_data, tool_use_id, context):
    if input_data['hook_event_name'] != 'PreToolUse':
        return {}

    command = input_data['tool_input'].get('command', '')

    if 'rm -rf /' in command:
        return {
            'hookSpecificOutput': {
                'hookEventName': input_data['hook_event_name'],
                'permissionDecision': 'deny',
                'permissionDecisionReason': 'Dangerous command blocked: rm -rf /'
            }
        }
    return {}
```

### /etcへの書き込みブロック + システムメッセージ注入

```python
async def block_etc_writes(input_data, tool_use_id, context):
    file_path = input_data['tool_input'].get('file_path', '')

    if file_path.startswith('/etc'):
        return {
            'systemMessage': 'Remember: system directories like /etc are protected.',
            'hookSpecificOutput': {
                'hookEventName': input_data['hook_event_name'],
                'permissionDecision': 'deny',
                'permissionDecisionReason': 'Writing to /etc is not allowed'
            }
        }
    return {}
```

### ツール入力の変更（サンドボックスへのリダイレクト）

```python
async def redirect_to_sandbox(input_data, tool_use_id, context):
    if input_data['hook_event_name'] != 'PreToolUse':
        return {}

    if input_data['tool_name'] == 'Write':
        original_path = input_data['tool_input'].get('file_path', '')
        return {
            'hookSpecificOutput': {
                'hookEventName': input_data['hook_event_name'],
                'permissionDecision': 'allow',
                'updatedInput': {
                    **input_data['tool_input'],
                    'file_path': f'/sandbox{original_path}'
                }
            }
        }
    return {}
```

`updatedInput`を使用する場合、`permissionDecision`も含める必要がある。元の`tool_input`を変更するのではなく、常に新しいオブジェクトを返す。

### 読み取り専用ツールの自動承認

```python
async def auto_approve_read_only(input_data, tool_use_id, context):
    if input_data['hook_event_name'] != 'PreToolUse':
        return {}

    read_only_tools = ['Read', 'Glob', 'Grep', 'LS']
    if input_data['tool_name'] in read_only_tools:
        return {
            'hookSpecificOutput': {
                'hookEventName': input_data['hook_event_name'],
                'permissionDecision': 'allow',
                'permissionDecisionReason': 'Read-only tool auto-approved'
            }
        }
    return {}
```

### ツール呼び出しのロギング

```python
async def log_tool_calls(input_data, tool_use_id, context):
    if input_data['hook_event_name'] == 'PreToolUse':
        print(f"Tool: {input_data['tool_name']}")
        print(f"Input: {input_data['tool_input']}")
    return {}
```

### 複数フックのチェーン

```python
options = ClaudeAgentOptions(
    hooks={
        'PreToolUse': [
            HookMatcher(hooks=[rate_limiter]),        # 最初：レート制限をチェック
            HookMatcher(hooks=[authorization_check]), # 2番目：権限を検証
            HookMatcher(hooks=[input_sanitizer]),     # 3番目：入力をサニタイズ
            HookMatcher(hooks=[audit_logger])         # 最後：アクションをログ
        ]
    }
)
```

フックは配列に表示される順序で実行される。各フックを単一の責任に集中させ、複雑なロジックには複数のフックをチェーンする。

### 正規表現によるツール固有のマッチャー

```python
options = ClaudeAgentOptions(
    hooks={
        'PreToolUse': [
            # ファイル変更ツールにマッチ
            HookMatcher(matcher='Write|Edit|Delete', hooks=[file_security_hook]),

            # すべてのMCPツールにマッチ
            HookMatcher(matcher='^mcp__', hooks=[mcp_audit_hook]),

            # すべてにマッチ（マッチャーなし）
            HookMatcher(hooks=[global_logger])
        ]
    }
)
```

### サブエージェントの追跡

```python
async def subagent_tracker(input_data, tool_use_id, context):
    if input_data['hook_event_name'] == 'SubagentStop':
        print(f"[SUBAGENT] Completed")
        print(f"  Tool use ID: {tool_use_id}")
        print(f"  Stop hook active: {input_data.get('stop_hook_active')}")
    return {}

options = ClaudeAgentOptions(
    hooks={
        'SubagentStop': [HookMatcher(hooks=[subagent_tracker])]
    }
)
```

### フックでの非同期操作

```python
import aiohttp
from datetime import datetime

async def webhook_notifier(input_data, tool_use_id, context):
    if input_data['hook_event_name'] != 'PostToolUse':
        return {}

    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                'https://api.example.com/webhook',
                json={
                    'tool': input_data['tool_name'],
                    'timestamp': datetime.now().isoformat()
                }
            )
    except Exception as e:
        print(f'Webhook request failed: {e}')

    return {}
```

### 通知の送信（TypeScriptのみ）

```typescript
import { query, HookCallback, NotificationHookInput } from "@anthropic-ai/claude-agent-sdk";

const notificationHandler: HookCallback = async (input, toolUseID, { signal }) => {
  const notification = input as NotificationHookInput;

  await fetch('https://hooks.slack.com/services/YOUR/WEBHOOK/URL', {
    method: 'POST',
    body: JSON.stringify({
      text: `Agent status: ${notification.message}`
    }),
    signal
  });

  return {};
};

for await (const message of query({
  prompt: "Analyze this codebase",
  options: {
    hooks: {
      Notification: [{ hooks: [notificationHandler] }]
    }
  }
})) {
  console.log(message);
}
```

## フックのトラブルシューティング

| 問題 | 原因・確認事項 |
|------|-------------|
| フックが発火しない | イベント名の大文字小文字を確認（`PreToolUse` not `preToolUse`）。マッチャーパターンの一致確認。`max_turns`制限でセッションが終了していないか確認 |
| マッチャーが期待通りにフィルタリングしない | マッチャーはツール名のみにマッチ。ファイルパスでフィルタリングするにはコールバック内で`tool_input.file_path`をチェック |
| フックのタイムアウト | `HookMatcher`の`timeout`値を増やす。TypeScriptでは`AbortSignal`を使用 |
| ツールが予期せずブロックされる | すべての`PreToolUse`フックの`permissionDecision`を確認。空のマッチャーはすべてのツールにマッチする |
| 変更された入力が適用されない | `updatedInput`が`hookSpecificOutput`内にあること、`permissionDecision: 'allow'`も返していること、`hookEventName`を含めていることを確認 |
| セッションフックが利用できない | `SessionStart`、`SessionEnd`、`Notification`はTypeScript SDKのみ |
| サブエージェントの権限プロンプトが増殖する | サブエージェントは親の権限を自動継承しない。`PreToolUse`フックで自動承認するか権限ルールを設定 |
| サブエージェントによる再帰的なフックループ | `parent_tool_use_id`で検出、トップレベルのみにスコープ設定 |
| `systemMessage`が出力に表示されない | すべてのSDK出力モードで表示されるとは限らない。別途ログに記録するか専用の出力チャネルを使用 |
