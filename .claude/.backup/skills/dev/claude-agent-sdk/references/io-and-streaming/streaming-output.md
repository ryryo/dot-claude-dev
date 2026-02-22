# ストリーミング出力

デフォルトではSDKは完全な`AssistantMessage`を返す。リアルタイムでトークンを受信するには、部分メッセージストリーミングを有効にする。

## 有効化オプション

| 言語 | オプション名 |
|---|---|
| Python | `include_partial_messages=True` |
| TypeScript | `includePartialMessages: true` |

有効にすると、通常の`AssistantMessage`や`ResultMessage`に加えて、生のAPIイベントを含む`StreamEvent`メッセージが返される。

## StreamEvent リファレンス

| 言語 | 型名 | インポート元 |
|---|---|---|
| Python | `StreamEvent` | `claude_agent_sdk.types` |
| TypeScript | `SDKPartialAssistantMessage` | `type: 'stream_event'` |

```python
@dataclass
class StreamEvent:
    uuid: str                      # このイベントの一意識別子
    session_id: str                # セッション識別子
    event: dict[str, Any]          # 生のClaude APIストリームイベント
    parent_tool_use_id: str | None # サブエージェントからの場合の親ツールID
```

## イベントタイプ一覧

| イベントタイプ | 説明 |
|---|---|
| `message_start` | 新しいメッセージの開始 |
| `content_block_start` | 新しいコンテンツブロック（テキストまたはツール使用）の開始 |
| `content_block_delta` | コンテンツのインクリメンタルな更新 |
| `content_block_stop` | コンテンツブロックの終了 |
| `message_delta` | メッセージレベルの更新（停止理由、使用量） |
| `message_stop` | メッセージの終了 |

## メッセージフロー

部分メッセージ有効時:

```
StreamEvent (message_start)
StreamEvent (content_block_start) - テキストブロック
StreamEvent (content_block_delta) - テキストチャンク...
StreamEvent (content_block_stop)
StreamEvent (content_block_start) - tool_useブロック
StreamEvent (content_block_delta) - ツール入力チャンク...
StreamEvent (content_block_stop)
StreamEvent (message_delta)
StreamEvent (message_stop)
AssistantMessage - すべてのコンテンツを含む完全なメッセージ
... ツールが実行される ...
... 次のターンのストリーミングイベントが続く ...
ResultMessage - 最終結果
```

部分メッセージ無効時に受信するメッセージタイプ: `SystemMessage`（セッション初期化）、`AssistantMessage`（完全なレスポンス）、`ResultMessage`（最終結果）、`CompactBoundaryMessage`（会話履歴が圧縮されたことを示す）。

## テキストレスポンスのストリーミング

`delta.type`が`text_delta`である`content_block_delta`イベントを探す。

```python
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import StreamEvent
import asyncio

async def stream_text():
    options = ClaudeAgentOptions(include_partial_messages=True)

    async for message in query(prompt="Explain how databases work", options=options):
        if isinstance(message, StreamEvent):
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    # 各テキストチャンクが到着するたびに出力
                    print(delta.get("text", ""), end="", flush=True)

    print()  # 最後の改行

asyncio.run(stream_text())
```

## ツール呼び出しのストリーミング

3つのイベントタイプを使用:
- `content_block_start`: ツールの開始
- `content_block_delta`（`input_json_delta`付き）: 入力チャンクの到着
- `content_block_stop`: ツール呼び出しの完了

```python
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import StreamEvent
import asyncio

async def stream_tool_calls():
    options = ClaudeAgentOptions(
        include_partial_messages=True,
        allowed_tools=["Read", "Bash"],
    )

    # 現在のツールを追跡し、入力JSONを蓄積する
    current_tool = None
    tool_input = ""

    async for message in query(prompt="Read the README.md file", options=options):
        if isinstance(message, StreamEvent):
            event = message.event
            event_type = event.get("type")

            if event_type == "content_block_start":
                # 新しいツール呼び出しが開始
                content_block = event.get("content_block", {})
                if content_block.get("type") == "tool_use":
                    current_tool = content_block.get("name")
                    tool_input = ""
                    print(f"Starting tool: {current_tool}")

            elif event_type == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "input_json_delta":
                    # ストリーミングされるJSON入力を蓄積
                    chunk = delta.get("partial_json", "")
                    tool_input += chunk
                    print(f"  Input chunk: {chunk}")

            elif event_type == "content_block_stop":
                # ツール呼び出し完了 - 最終入力を表示
                if current_tool:
                    print(f"Tool {current_tool} called with: {tool_input}")
                    current_tool = None

asyncio.run(stream_tool_calls())
```

## ストリーミングUI統合パターン

テキストとツールのストリーミングを統合し、`in_tool`フラグでツール実行中のステータスインジケーターを表示するパターン。

```python
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
from claude_agent_sdk.types import StreamEvent
import asyncio
import sys

async def streaming_ui():
    options = ClaudeAgentOptions(
        include_partial_messages=True,
        allowed_tools=["Read", "Bash", "Grep"],
    )

    # 現在ツール呼び出し中かどうかを追跡
    in_tool = False

    async for message in query(
        prompt="Find all TODO comments in the codebase",
        options=options
    ):
        if isinstance(message, StreamEvent):
            event = message.event
            event_type = event.get("type")

            if event_type == "content_block_start":
                content_block = event.get("content_block", {})
                if content_block.get("type") == "tool_use":
                    # ツール呼び出しが開始 - ステータスインジケーターを表示
                    tool_name = content_block.get("name")
                    print(f"\n[Using {tool_name}...]", end="", flush=True)
                    in_tool = True

            elif event_type == "content_block_delta":
                delta = event.get("delta", {})
                # ツール実行中でない場合のみテキストをストリーミング
                if delta.get("type") == "text_delta" and not in_tool:
                    sys.stdout.write(delta.get("text", ""))
                    sys.stdout.flush()

            elif event_type == "content_block_stop":
                if in_tool:
                    # ツール呼び出し完了
                    print(" done", flush=True)
                    in_tool = False

        elif isinstance(message, ResultMessage):
            # エージェントがすべての作業を完了
            print(f"\n\n--- Complete ---")

asyncio.run(streaming_ui())
```

## ストリーミング出力の既知の制限事項

| 機能 | 制限 |
|---|---|
| 拡張思考 | `max_thinking_tokens` / `maxThinkingTokens` を明示的に設定した場合、`StreamEvent`は発行されない。SDKではデフォルトで思考は無効。 |
| 構造化出力 | JSON結果は最終的な`ResultMessage.structured_output`にのみ表示され、ストリーミングデルタとしては表示されない。 |
