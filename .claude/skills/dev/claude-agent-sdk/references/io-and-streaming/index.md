# I/O & Streaming - Claude Agent SDK

| サブファイル | 内容 |
|---|---|
| [streaming-output.md](./streaming-output.md) | ストリーミング出力: StreamEvent、イベントタイプ、テキスト/ツールのストリーミング、UI統合パターン、制限事項 |
| [structured-output.md](./structured-output.md) | 構造化出力: JSON Schema設定、Zod/Pydantic型安全スキーマ、マルチステップ例、エラーハンドリング |
| [approval-and-input.md](./approval-and-input.md) | 承認とユーザー入力: canUseToolコールバック、ツール承認、確認質問 (AskUserQuestion)、制限事項 |

---

## 1. 入力モード: ストリーミング vs シングルメッセージ

Agent SDKは2つの入力モードをサポートする。

### ストリーミング入力モード（デフォルト・推奨）

永続的でインタラクティブなセッション。エージェントは長期的なプロセスとして動作し、ユーザー入力の受け取り、割り込み処理、権限リクエスト表示、セッション管理を行う。

| 機能 | サポート |
|---|---|
| 画像アップロード | あり |
| キューに入れたメッセージ | あり |
| ツール統合（全ツール・カスタムMCPサーバー） | あり |
| フック対応 | あり |
| リアルタイムフィードバック | あり |
| コンテキスト永続性（マルチターン） | あり |

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";
import { readFileSync } from "fs";

async function* generateMessages() {
  // First message
  yield {
    type: "user" as const,
    message: {
      role: "user" as const,
      content: "Analyze this codebase for security issues"
    }
  };

  // Wait for conditions or user input
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Follow-up with image
  yield {
    type: "user" as const,
    message: {
      role: "user" as const,
      content: [
        {
          type: "text",
          text: "Review this architecture diagram"
        },
        {
          type: "image",
          source: {
            type: "base64",
            media_type: "image/png",
            data: readFileSync("diagram.png", "base64")
          }
        }
      ]
    }
  };
}

// Process streaming responses
for await (const message of query({
  prompt: generateMessages(),
  options: {
    maxTurns: 10,
    allowedTools: ["Read", "Grep"]
  }
})) {
  if (message.type === "result") {
    console.log(message.result);
  }
}
```

### シングルメッセージ入力

1回限りのクエリ。セッション状態を使用して再開可能。

**使用する場合:**
- 1回限りのレスポンスが必要
- 画像添付、フックなどが不要
- ラムダ関数などのステートレス環境

**サポートしない機能:**
- メッセージ内の直接的な画像添付
- 動的なメッセージキューイング
- リアルタイム割り込み
- フック統合
- 自然なマルチターン会話

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Simple one-shot query
for await (const message of query({
  prompt: "Explain the authentication flow",
  options: {
    maxTurns: 1,
    allowedTools: ["Read", "Grep"]
  }
})) {
  if (message.type === "result") {
    console.log(message.result);
  }
}

// Continue conversation with session management
for await (const message of query({
  prompt: "Now explain the authorization process",
  options: {
    continue: true,
    maxTurns: 1
  }
})) {
  if (message.type === "result") {
    console.log(message.result);
  }
}
```

---

## 5. 停止理由 (stop_reason)

`ResultMessage`の`stop_reason`フィールドで、モデルが生成を停止した理由を検出する。ストリーミングの有効/無効に関係なく利用可能。

### 利用可能な停止理由

| 停止理由 | 意味 |
|---|---|
| `end_turn` | 正常にレスポンスの生成を完了 |
| `max_tokens` | 最大出力トークン制限に到達 |
| `stop_sequence` | 設定されたストップシーケンスを生成 |
| `refusal` | リクエストの実行を拒否 |
| `tool_use` | 最終出力がツール呼び出し（SDKの結果では一般的ではない） |
| `null` | APIレスポンスが受信されなかった（エラーやキャッシュ再生） |

### stop_reasonの読み取り

```python
from claude_agent_sdk import query, ResultMessage
import asyncio

async def check_stop_reason():
    async for message in query(prompt="Write a poem about the ocean"):
        if isinstance(message, ResultMessage):
            print(f"Stop reason: {message.stop_reason}")
            if message.stop_reason == "refusal":
                print("The model declined this request.")

asyncio.run(check_stop_reason())
```

### エラー結果の停止理由

| 結果バリアント | stop_reasonの値 |
|---|---|
| `success` | 最終アシスタントメッセージの停止理由 |
| `error_max_turns` | ターン制限に達する前の最後のアシスタントメッセージの停止理由 |
| `error_max_budget_usd` | 予算を超過する前の最後のアシスタントメッセージの停止理由 |
| `error_max_structured_output_retries` | リトライ制限に達する前の最後のアシスタントメッセージの停止理由 |
| `error_during_execution` | 最後に確認された停止理由、またはAPIレスポンスの前にエラーが発生した場合は`null` |

```python
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
import asyncio

async def handle_max_turns():
    options = ClaudeAgentOptions(max_turns=3)

    async for message in query(prompt="Refactor this module", options=options):
        if isinstance(message, ResultMessage):
            if message.subtype == "error_max_turns":
                print(f"Hit turn limit. Last stop reason: {message.stop_reason}")
                # stop_reason might be "end_turn" or "tool_use"
                # depending on what the model was doing when the limit hit

asyncio.run(handle_max_turns())
```

### 拒否の検出

```python
from claude_agent_sdk import query, ResultMessage
import asyncio

async def safe_query(prompt: str):
    async for message in query(prompt=prompt):
        if isinstance(message, ResultMessage):
            if message.stop_reason == "refusal":
                print("Request was declined. Please revise your prompt.")
                return None
            return message.result
    return None

asyncio.run(safe_query("Summarize this article"))
```

---

## 設計判断ポイント

### 入力モードの選択

| 判断基準 | ストリーミング入力（推奨） | シングルメッセージ入力 |
|---|---|---|
| インタラクティブ性 | マルチターン、割り込み、リダイレクトが可能 | 1回限りのリクエスト・レスポンス |
| 画像サポート | あり | なし |
| フック・カスタマイズ | フルサポート | なし |
| 実行環境 | 長時間実行プロセス | ラムダ関数等のステートレス環境 |
| `canUseTool`利用 | ストリーミングモード + `PreToolUse`ダミーフックが**必須**（Python） | 利用不可 |
| ユースケース | チャットUI、IDEプラグイン、対話型ワークフロー | CI/CDパイプライン、バッチ処理、単発タスク |

### 出力ストリーミングの判断

| 判断基準 | 部分メッセージ有効 | 部分メッセージ無効（デフォルト） |
|---|---|---|
| ユーザー体験 | テキスト・ツール呼び出しのリアルタイム表示 | 完了まで待機 |
| 実装の複雑さ | StreamEventの型チェック・蓄積処理が必要 | AssistantMessage/ResultMessageのみで単純 |
| 拡張思考との互換性 | 非互換（`max_thinking_tokens`設定時はStreamEvent未発行） | 制約なし |
| 構造化出力 | ストリーミングデルタなし（最終ResultMessageのみ） | 同じ |

### 構造化出力の判断

| 判断基準 | 構造化出力あり | 構造化出力なし |
|---|---|---|
| 適用場面 | データベース投入、API連携、UIコンポーネントへの渡し | チャット応答、自由形式レポート |
| 型安全性 | Zod/Pydanticで完全な型推論・バリデーション | なし |
| エラーリスク | 複雑すぎるスキーマや曖昧なプロンプトで`error_max_structured_output_retries`になる可能性 | なし |
| ストリーミングとの関係 | ストリーミングデルタ非対応、最終`ResultMessage.structured_output`のみ | ストリーミング可能 |
| スキーマ設計のコツ | シンプルに始める、情報不足の可能性があるフィールドはオプションに、プロンプトを明確に | - |

### ユーザー入力パターンの選択

| 方法 | 適用場面 | 制約 |
|---|---|---|
| `canUseTool`コールバック | ツール承認・確認質問の標準パターン | Pythonではストリーミング入力+ダミーフックが必須 |
| `AskUserQuestion`ツール | planモードでの要件収集、多肢選択式の確認 | 1〜4問、各2〜4選択肢。サブエージェントでは利用不可 |
| ストリーミング入力 | タスク中の中断・追加コンテキスト・チャットUI | ステートフル環境が必要 |
| カスタムツール | フォーム・ウィザード・外部承認連携 | 実装コストが高い |

### stop_reasonに基づくエラーハンドリング戦略

| stop_reason | 推奨対応 |
|---|---|
| `end_turn` | 正常完了、結果を使用 |
| `refusal` | プロンプトの見直し、ユーザーへの通知 |
| `max_tokens` | 出力制限の引き上げ、またはタスクの分割 |
| `null` | 接続エラーのリトライ処理 |
