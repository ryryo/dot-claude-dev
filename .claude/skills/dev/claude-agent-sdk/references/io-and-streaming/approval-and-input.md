# 承認とユーザー入力

Claudeがユーザー入力をリクエストする2つの状況:
1. **ツールの使用許可**が必要な場合（ファイル削除やコマンド実行など）
2. **確認質問**がある場合（`AskUserQuestion`ツール経由）

どちらも`canUseTool`コールバックをトリガーし、レスポンスを返すまで実行が一時停止する。

## canUseToolコールバックの設定

```python
async def handle_tool_request(tool_name, input_data, context):
    # ユーザーにプロンプトを表示し、許可または拒否を返す
    ...

options = ClaudeAgentOptions(can_use_tool=handle_tool_request)
```

## ツール承認リクエスト

コールバック引数:

| 引数 | 説明 |
|---|---|
| `toolName` | 使用しようとしているツール名（例: `"Bash"`, `"Write"`, `"Edit"`） |
| `input` | ツールに渡すパラメータ |

主要ツールの入力フィールド:

| ツール | 入力フィールド |
|---|---|
| `Bash` | `command`, `description`, `timeout` |
| `Write` | `file_path`, `content` |
| `Edit` | `file_path`, `old_string`, `new_string` |
| `Read` | `file_path`, `offset`, `limit` |

## レスポンスタイプ

| レスポンス | Python | TypeScript |
|---|---|---|
| 許可 | `PermissionResultAllow(updated_input=...)` | `{ behavior: "allow", updatedInput }` |
| 拒否 | `PermissionResultDeny(message=...)` | `{ behavior: "deny", message }` |

応答パターン:
- **承認**: リクエスト通りに実行
- **変更付き承認**: 実行前に入力を変更（パスのサニタイズ、制約の追加）
- **拒否**: ブロックして理由を伝える
- **代替案の提案**: ブロックするが方向を導く
- **完全なリダイレクト**: ストリーミング入力で新しい指示を送る

## ツール承認の完全な例

```python
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, query
from claude_agent_sdk.types import (
    HookMatcher,
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
)

async def can_use_tool(
    tool_name: str, input_data: dict, context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    # ツールリクエストを表示
    print(f"\nTool: {tool_name}")
    if tool_name == "Bash":
        print(f"Command: {input_data.get('command')}")
        if input_data.get("description"):
            print(f"Description: {input_data.get('description')}")
    else:
        print(f"Input: {input_data}")

    # ユーザーの承認を取得
    response = input("Allow this action? (y/n): ")

    # ユーザーの応答に基づいて許可または拒否を返す
    if response.lower() == "y":
        # 許可：ツールは元の（または変更された）入力で実行される
        return PermissionResultAllow(updated_input=input_data)
    else:
        # 拒否：ツールは実行されず、Claudeにメッセージが表示される
        return PermissionResultDeny(message="User denied this action")

# 必要な回避策：ダミーフックがcan_use_toolのためにストリームを開いたままにする
async def dummy_hook(input_data, tool_use_id, context):
    return {"continue_": True}

async def prompt_stream():
    yield {
        "type": "user",
        "message": {
            "role": "user",
            "content": "Create a test file in /tmp and then delete it",
        },
    }

async def main():
    async for message in query(
        prompt=prompt_stream(),
        options=ClaudeAgentOptions(
            can_use_tool=can_use_tool,
            hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[dummy_hook])]},
        ),
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

**重要:** Pythonでは`can_use_tool`はストリーミングモードと、ストリームを開いたままにする`PreToolUse`フック（`{"continue_": True}`を返す）が必要。

## 確認質問 (AskUserQuestion)

Claudeが複数の有効なアプローチがあるタスクでユーザー入力が必要な場合に呼び出す。`plan`モードで特に一般的。

**質問フォーマット:**

| フィールド | 説明 |
|---|---|
| `question` | 表示する完全な質問テキスト |
| `header` | 質問の短いラベル（最大12文字） |
| `options` | 2〜4個の選択肢の配列、各選択肢に`label`と`description` |
| `multiSelect` | `true`の場合、複数のオプションを選択可能 |

質問入力の例:

```json
{
  "questions": [
    {
      "question": "How should I format the output?",
      "header": "Format",
      "options": [
        { "label": "Summary", "description": "Brief overview of key points" },
        { "label": "Detailed", "description": "Full explanation with examples" }
      ],
      "multiSelect": false
    }
  ]
}
```

**レスポンスフォーマット:**

| フィールド | 説明 |
|---|---|
| `questions` | 元の質問配列をそのまま渡す（ツール処理に必要） |
| `answers` | キーが質問テキスト、値が選択されたラベルであるオブジェクト |

複数選択の場合、ラベルを`", "`で結合。自由テキストの場合、カスタムテキストを値として直接使用。

```python
return PermissionResultAllow(
    updated_input={
        "questions": input_data.get("questions", []),
        "answers": {
            "How should I format the output?": "Summary",
            "Which sections should I include?": "Introduction, Conclusion"
        }
    }
)
```

## 確認質問の完全な例

```python
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, query
from claude_agent_sdk.types import HookMatcher, PermissionResultAllow

def parse_response(response: str, options: list) -> str:
    """ユーザー入力をオプション番号またはフリーテキストとして解析する。"""
    try:
        indices = [int(s.strip()) - 1 for s in response.split(",")]
        labels = [options[i]["label"] for i in indices if 0 <= i < len(options)]
        return ", ".join(labels) if labels else response
    except ValueError:
        return response

async def handle_ask_user_question(input_data: dict) -> PermissionResultAllow:
    """Claudeの質問を表示し、ユーザーの回答を収集する。"""
    answers = {}

    for q in input_data.get("questions", []):
        print(f"\n{q['header']}: {q['question']}")

        options = q["options"]
        for i, opt in enumerate(options):
            print(f"  {i + 1}. {opt['label']} - {opt['description']}")
        if q.get("multiSelect"):
            print("  (Enter numbers separated by commas, or type your own answer)")
        else:
            print("  (Enter a number, or type your own answer)")

        response = input("Your choice: ").strip()
        answers[q["question"]] = parse_response(response, options)

    return PermissionResultAllow(
        updated_input={
            "questions": input_data.get("questions", []),
            "answers": answers,
        }
    )

async def can_use_tool(tool_name: str, input_data: dict, context) -> PermissionResultAllow:
    # AskUserQuestionを質問ハンドラーにルーティング
    if tool_name == "AskUserQuestion":
        return await handle_ask_user_question(input_data)
    # この例では他のツールを自動承認
    return PermissionResultAllow(updated_input=input_data)

async def prompt_stream():
    yield {
        "type": "user",
        "message": {"role": "user", "content": "Help me decide on the tech stack for a new mobile app"},
    }

# 必要な回避策：ダミーフックがcan_use_toolのためにストリームを開いたままにする
async def dummy_hook(input_data, tool_use_id, context):
    return {"continue_": True}

async def main():
    async for message in query(
        prompt=prompt_stream(),
        options=ClaudeAgentOptions(
            can_use_tool=can_use_tool,
            hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[dummy_hook])]},
        ),
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

## ユーザー入力の制限事項

- `AskUserQuestion`はTaskツール経由で生成されたサブエージェントでは利用不可
- 各`AskUserQuestion`呼び出しは、それぞれ2〜4個のオプションを持つ1〜4個の質問をサポート

## ユーザー入力を取得するその他の方法

| 方法 | 適用場面 |
|---|---|
| ストリーミング入力 | タスク中の中断、追加コンテキスト提供、チャットインターフェース構築 |
| カスタムツール | 構造化された入力収集（フォーム、ウィザード）、外部承認システム統合、ドメイン固有のインタラクション |
