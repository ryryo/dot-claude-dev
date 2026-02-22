# ファイルチェックポイント

ファイルチェックポイントは、エージェントセッション中にWrite、Edit、NotebookEditツールを通じて行われたファイル変更を追跡し、任意の以前の状態にファイルを巻き戻すことができる。

## 対象ツール

| ツール | 説明 |
|--------|------|
| Write | 新しいファイルを作成するか、既存のファイルを新しい内容で上書き |
| Edit | 既存のファイルの特定の部分に対して的を絞った編集 |
| NotebookEdit | Jupyterノートブック（`.ipynb`ファイル）のセルを変更 |

Bashコマンド（`echo > file.txt`や`sed -i`など）を通じて行われた変更は追跡されない。

## チェックポイントの仕組み

- SDKはWrite、Edit、またはNotebookEditツールを通じてファイルを変更する前にバックアップを作成
- レスポンスストリーム内のユーザーメッセージにはチェックポイントUUIDが含まれる
- ファイルの巻き戻しはディスク上のファイルを復元するが、会話自体は巻き戻さない

追跡対象：
- セッション中に作成されたファイル
- セッション中に変更されたファイル
- 変更されたファイルの元の内容

## 基本的な実装フロー

```python
import asyncio
import os
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, UserMessage, ResultMessage

async def main():
    # ステップ1: チェックポイントを有効にする
    options = ClaudeAgentOptions(
        enable_file_checkpointing=True,
        permission_mode="acceptEdits",  # プロンプトなしでファイル編集を自動承認
        extra_args={"replay-user-messages": None},  # チェックポイントUUID受信に必要
        env={**os.environ, "CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING": "1"}
    )

    checkpoint_id = None
    session_id = None

    # ステップ2: クエリを実行し、チェックポイントUUIDとセッションIDをキャプチャ
    async with ClaudeSDKClient(options) as client:
        await client.query("Refactor the authentication module")

        async for message in client.receive_response():
            if isinstance(message, UserMessage) and message.uuid and not checkpoint_id:
                checkpoint_id = message.uuid
            if isinstance(message, ResultMessage) and not session_id:
                session_id = message.session_id

    # ステップ3: 後で、空のプロンプトでセッションを再開して巻き戻す
    if checkpoint_id and session_id:
        async with ClaudeSDKClient(ClaudeAgentOptions(
            enable_file_checkpointing=True,
            resume=session_id
        )) as client:
            await client.query("")  # 接続を開くための空のプロンプト
            async for message in client.receive_response():
                await client.rewind_files(checkpoint_id)
                break
        print(f"Rewound to checkpoint: {checkpoint_id}")

asyncio.run(main())
```

## 必要な設定

| オプション | Python | TypeScript | 説明 |
|-----------|--------|-----------|------|
| チェックポイントを有効にする | `enable_file_checkpointing=True` | `enableFileCheckpointing: true` | 巻き戻し用にファイル変更を追跡 |
| チェックポイントUUIDを受信 | `extra_args={"replay-user-messages": None}` | `extraArgs: { 'replay-user-messages': null }` | ストリームでユーザーメッセージUUIDを取得するために必要 |
| 環境変数 | `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1` | 同左 | ファイルチェックポイント機能の有効化に必要 |

環境変数の設定方法：

**コマンドラインで設定**:
```bash
export CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1
```

**SDKオプションで設定**:
```python
import os

options = ClaudeAgentOptions(
       enable_file_checkpointing=True,
       env={**os.environ, "CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING": "1"}
)
```

## リスクのある操作前のチェックポイント

最新のチェックポイントUUIDのみを保持し、問題が発生した場合に即座に巻き戻すパターン：

```python
import asyncio
import os
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, UserMessage

async def main():
    options = ClaudeAgentOptions(
        enable_file_checkpointing=True,
        permission_mode="acceptEdits",
        extra_args={"replay-user-messages": None},
        env={**os.environ, "CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING": "1"}
    )

    safe_checkpoint = None

    async with ClaudeSDKClient(options) as client:
        await client.query("Refactor the authentication module")

        async for message in client.receive_response():
            if isinstance(message, UserMessage) and message.uuid:
                safe_checkpoint = message.uuid

            if your_revert_condition and safe_checkpoint:
                await client.rewind_files(safe_checkpoint)
                break

asyncio.run(main())
```

## 複数の復元ポイント

すべてのチェックポイントUUIDをメタデータとともに保存し、任意の以前のチェックポイントに巻き戻すパターン：

```python
import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, UserMessage, ResultMessage

@dataclass
class Checkpoint:
    id: str
    description: str
    timestamp: datetime

async def main():
    options = ClaudeAgentOptions(
        enable_file_checkpointing=True,
        permission_mode="acceptEdits",
        extra_args={"replay-user-messages": None},
        env={**os.environ, "CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING": "1"}
    )

    checkpoints = []
    session_id = None

    async with ClaudeSDKClient(options) as client:
        await client.query("Refactor the authentication module")

        async for message in client.receive_response():
            if isinstance(message, UserMessage) and message.uuid:
                checkpoints.append(Checkpoint(
                    id=message.uuid,
                    description=f"After turn {len(checkpoints) + 1}",
                    timestamp=datetime.now()
                ))
            if isinstance(message, ResultMessage) and not session_id:
                session_id = message.session_id

    # 後で：セッションを再開して任意のチェックポイントに巻き戻す
    if checkpoints and session_id:
        target = checkpoints[0]  # 任意のチェックポイントを選択
        async with ClaudeSDKClient(ClaudeAgentOptions(
            enable_file_checkpointing=True,
            resume=session_id
        )) as client:
            await client.query("")
            async for message in client.receive_response():
                await client.rewind_files(target.id)
                break
        print(f"Rewound to: {target.description}")

asyncio.run(main())
```

## CLIからの巻き戻し

```bash
claude --resume <session-id> --rewind-files <checkpoint-uuid>
```

## 制限事項

| 制限事項 | 説明 |
|---------|------|
| Write/Edit/NotebookEditツールのみ | Bashコマンドを通じて行われた変更は追跡されない |
| 同一セッション | チェックポイントはそれを作成したセッションに紐づく |
| ファイル内容のみ | ディレクトリの作成、移動、削除は巻き戻しで元に戻されない |
| ローカルファイル | リモートまたはネットワークファイルは追跡されない |

## トラブルシューティング

| 問題 | 原因・解決策 |
|------|-------------|
| チェックポイントオプションが認識されない | 最新のSDKバージョンに更新（`pip install --upgrade claude-agent-sdk` / `npm install @anthropic-ai/claude-agent-sdk@latest`） |
| ユーザーメッセージにUUIDがない | `extra_args={"replay-user-messages": None}`（Python）または`extraArgs: { 'replay-user-messages': null }`（TypeScript）を追加 |
| 「No file checkpoint found for message」エラー | `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING`環境変数を設定。セッションを適切に完了してから巻き戻す |
| 「ProcessTransport is not ready for writing」エラー | レスポンス反復完了後にrewindを呼んでいる。空のプロンプトでセッションを再開してから巻き戻す |
