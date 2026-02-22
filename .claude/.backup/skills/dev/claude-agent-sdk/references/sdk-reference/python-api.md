# Python SDK

### `query()` と `ClaudeSDKClient` の選択

Python SDKは2つのインタラクション方法を提供する。

#### クイック比較

| 機能 | `query()` | `ClaudeSDKClient` |
|------|-----------|-------------------|
| セッション | 毎回新しいセッションを作成 | 同じセッションを再利用 |
| 会話 | 単一のやり取り | 同じコンテキストで複数のやり取り |
| 接続 | 自動的に管理 | 手動制御 |
| ストリーミング入力 | サポート | サポート |
| 中断 | 非サポート | サポート |
| フック | 非サポート | サポート |
| カスタムツール | 非サポート | サポート |
| チャット継続 | 毎回新しいセッション | 会話を維持 |
| ユースケース | 単発タスク | 継続的な会話 |

### `query()`

各インタラクションごとに新しいセッションを作成する。メッセージが到着するたびにそれを生成する非同期イテレータを返す。

```
async def query(
    *,
    prompt: str | AsyncIterable[dict[str, Any]],
    options: ClaudeAgentOptions | None = None
) -> AsyncIterator[Message]
```

**パラメータ:**

| パラメータ | 型 | 説明 |
|-----------|---|------|
| `prompt` | `str \| AsyncIterable[dict]` | 入力プロンプト、またはストリーミング用の非同期イテラブル |
| `options` | `ClaudeAgentOptions \| None` | 設定オブジェクト（Noneの場合はデフォルト） |

**戻り値:** `AsyncIterator[Message]`

**例:**
```
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        system_prompt="You are an expert Python developer",
        permission_mode='acceptEdits',
        cwd="/home/user/project"
    )

    async for message in query(
        prompt="Create a Python web server",
        options=options
    ):
        print(message)

asyncio.run(main())
```

### `ClaudeSDKClient`

複数のやり取りにわたって会話セッションを維持するクライアント。

```
class ClaudeSDKClient:
    def __init__(self, options: ClaudeAgentOptions | None = None)
    async def connect(self, prompt: str | AsyncIterable[dict] | None = None) -> None
    async def query(self, prompt: str | AsyncIterable[dict], session_id: str = "default") -> None
    async def receive_messages(self) -> AsyncIterator[Message]
    async def receive_response(self) -> AsyncIterator[Message]
    async def interrupt(self) -> None
    async def rewind_files(self, user_message_uuid: str) -> None
    async def disconnect(self) -> None
```

**メソッド:**

| メソッド | 説明 |
|---------|------|
| `__init__(options)` | オプションの設定でクライアントを初期化 |
| `connect(prompt)` | オプションの初期プロンプトでClaudeに接続 |
| `query(prompt, session_id)` | ストリーミングモードで新しいリクエストを送信 |
| `receive_messages()` | Claudeからのすべてのメッセージを非同期イテレータとして受信 |
| `receive_response()` | ResultMessageを含むまでメッセージを受信 |
| `interrupt()` | 中断シグナルを送信（ストリーミングモードでのみ動作） |
| `rewind_files(user_message_uuid)` | 指定されたユーザーメッセージの状態にファイルを復元。`enable_file_checkpointing=True` が必要 |
| `disconnect()` | Claudeから切断 |

**コンテキストマネージャーサポート:**
```
async with ClaudeSDKClient() as client:
    await client.query("Hello Claude")
    async for message in client.receive_response():
        print(message)
```

> **重要:** メッセージをイテレートする際、`break` を使用して早期に終了することは避けること。asyncioのクリーンアップの問題が発生する可能性がある。

**例 - 会話の継続:**
```
import asyncio
from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage

async def main():
    async with ClaudeSDKClient() as client:
        # 最初の質問
        await client.query("What's the capital of France?")

        # 応答を処理
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

        # フォローアップの質問 - Claudeは以前のコンテキストを記憶している
        await client.query("What's the population of that city?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

        # さらにフォローアップ - まだ同じ会話内
        await client.query("What are some famous landmarks there?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

asyncio.run(main())
```

**例 - ストリーミング入力:**
```
import asyncio
from claude_agent_sdk import ClaudeSDKClient

async def message_stream():
    """メッセージを動的に生成。"""
    yield {"type": "text", "text": "Analyze the following data:"}
    await asyncio.sleep(0.5)
    yield {"type": "text", "text": "Temperature: 25°C"}
    await asyncio.sleep(0.5)
    yield {"type": "text", "text": "Humidity: 60%"}
    await asyncio.sleep(0.5)
    yield {"type": "text", "text": "What patterns do you see?"}

async def main():
    async with ClaudeSDKClient() as client:
        # Claudeに入力をストリーミング
        await client.query(message_stream())

        # 応答を処理
        async for message in client.receive_response():
            print(message)

        # 同じセッションでフォローアップ
        await client.query("Should we be concerned about these readings?")

        async for message in client.receive_response():
            print(message)

asyncio.run(main())
```

**例 - 中断の使用:**
```
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def interruptible_task():
    options = ClaudeAgentOptions(
        allowed_tools=["Bash"],
        permission_mode="acceptEdits"
    )

    async with ClaudeSDKClient(options=options) as client:
        # 長時間実行タスクを開始
        await client.query("Count from 1 to 100 slowly")

        # しばらく実行させる
        await asyncio.sleep(2)

        # タスクを中断
        await client.interrupt()
        print("Task interrupted!")

        # 新しいコマンドを送信
        await client.query("Just say hello instead")

        async for message in client.receive_response():
            pass

asyncio.run(interruptible_task())
```

**例 - 高度な権限制御:**
```
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions
)
from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny

async def custom_permission_handler(
    tool_name: str,
    input_data: dict,
    context: dict
) -> PermissionResultAllow | PermissionResultDeny:
    """ツール権限のカスタムロジック。"""

    # システムディレクトリへの書き込みをブロック
    if tool_name == "Write" and input_data.get("file_path", "").startswith("/system/"):
        return PermissionResultDeny(
            message="System directory write not allowed",
            interrupt=True
        )

    # 機密ファイル操作をリダイレクト
    if tool_name in ["Write", "Edit"] and "config" in input_data.get("file_path", ""):
        safe_path = f"./sandbox/{input_data['file_path']}"
        return PermissionResultAllow(
            updated_input={**input_data, "file_path": safe_path}
        )

    # その他はすべて許可
    return PermissionResultAllow(updated_input=input_data)

async def main():
    options = ClaudeAgentOptions(
        can_use_tool=custom_permission_handler,
        allowed_tools=["Read", "Write", "Edit"]
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Update the system config file")

        async for message in client.receive_response():
            print(message)

asyncio.run(main())
```
