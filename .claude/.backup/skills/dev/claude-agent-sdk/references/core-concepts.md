# Core Concepts - Claude Agent SDK

Claude Agent SDKの概要、クイックスタート、セッション管理、移行ガイドから抽出した設計判断に役立つリファレンス。

---

## 1. SDK概要

Claude Agent SDK（旧Claude Code SDK）は、Claude Codeを支えるツール、エージェントループ、コンテキスト管理を、PythonとTypeScriptでプログラム可能な形で提供する。ファイルの読み取り、コマンドの実行、ウェブ検索、コード編集などを自律的に行うAIエージェントを構築できる。

### パッケージ情報

| 項目 | 値 |
|---|---|
| TypeScript パッケージ | `@anthropic-ai/claude-agent-sdk` |
| Python パッケージ | `claude-agent-sdk` |
| Python import | `from claude_agent_sdk import query, ClaudeAgentOptions` |
| TypeScript import | `import { query, tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk"` |

### 認証方法

| プロバイダー | 環境変数 |
|---|---|
| Anthropic API | `ANTHROPIC_API_KEY=your-api-key` |
| Amazon Bedrock | `CLAUDE_CODE_USE_BEDROCK=1` + AWS認証情報 |
| Google Vertex AI | `CLAUDE_CODE_USE_VERTEX=1` + Google Cloud認証情報 |
| Microsoft Azure | `CLAUDE_CODE_USE_FOUNDRY=1` + Azure認証情報 |

> 事前に承認されていない限り、Anthropicはサードパーティの開発者がclaude.aiのログインやレート制限を自社製品に提供することを許可していない。APIキー認証方法を使用すること。

---

## 2. 基本アーキテクチャ

### query関数 - メインエントリポイント

`query`はエージェントループを作成するメインのエントリポイント。非同期イテレータを返すため、`async for`（Python）/ `for await`（TypeScript）でClaudeが作業する間メッセージをストリーミングする。

#### Python 基本パターン

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

async def main():
    async for message in query(
        prompt="Review utils.py for bugs that would cause crashes. Fix any issues you find.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Glob"],  # Claude が使用できるツール
            permission_mode="acceptEdits"            # ファイル編集を自動承認
        )
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)              # Claude の推論
                elif hasattr(block, "name"):
                    print(f"Tool: {block.name}")   # 呼び出されるツール
        elif isinstance(message, ResultMessage):
            print(f"Done: {message.subtype}")      # 最終結果

asyncio.run(main())
```

#### TypeScript 基本パターン

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk"

const response = query({
  prompt: "Help me build a web application",
  options: {
    model: "claude-opus-4-6"
  }
})

for await (const message of response) {
  if (message.type === 'system' && message.subtype === 'init') {
    console.log(`Session started with ID: ${message.session_id}`)
  }
  console.log(message)
}
```

### エージェントループの動作

`async for`ループは、Claudeが思考し、ツールを呼び出し、結果を観察し、次に何をするかを決定する間、実行し続ける。各イテレーションでメッセージが生成される：Claudeの推論、ツール呼び出し、ツール結果、または最終的な結果。SDKがオーケストレーション（ツール実行、コンテキスト管理、リトライ）を処理するため、ストリームを消費するだけで済む。ループはClaudeがタスクを完了するか、エラーが発生した時点で終了する。

ライブ出力が不要な場合（バックグラウンドジョブやCIパイプライン）、すべてのメッセージを一度に収集できる（ストリーミング vs シングルターンモード）。

---

## 3. ツール構成

### 組み込みツール一覧と推奨組み合わせ

| ツール組み合わせ | エージェントができること |
|---|---|
| `Read`, `Glob`, `Grep` | 読み取り専用の分析 |
| `Read`, `Edit`, `Glob` | コードの分析と修正 |
| `Read`, `Edit`, `Bash`, `Glob`, `Grep` | 完全な自動化 |

### ツール追加の例

Web検索機能を追加：

```python
options=ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob", "WebSearch"],
    permission_mode="acceptEdits"
)
```

ターミナルコマンド実行を追加：

```python
options=ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob", "Bash"],
    permission_mode="acceptEdits"
)
```

---

## 4. パーミッションモード

| モード | 動作 | ユースケース |
|---|---|---|
| `acceptEdits` | ファイル編集を自動承認し、その他のアクションは確認を求める | 信頼された開発ワークフロー |
| `bypassPermissions` | プロンプトなしで実行 | CI/CDパイプライン、自動化 |
| `default` | 承認を処理する`canUseTool`コールバックが必要 | カスタム承認フロー |

ユーザーに承認を求めたい場合は、`default`モードを使用し、ユーザー入力を収集する`canUseTool`コールバックを提供する。

---

## 5. ClaudeAgentOptions

### カスタムシステムプロンプト

```python
options=ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob"],
    permission_mode="acceptEdits",
    system_prompt="You are a senior Python developer. Always follow PEP 8 style guidelines."
)
```

### システムプロンプトのプリセット（TypeScript）

```typescript
// デフォルト: 最小限のシステムプロンプト
const result = query({ prompt: "Hello" });

// Claude Codeのプリセットを明示的に使用:
const result = query({
  prompt: "Hello",
  options: {
    systemPrompt: { type: "preset", preset: "claude_code" }
  }
});

// カスタムシステムプロンプト:
const result = query({
  prompt: "Hello",
  options: {
    systemPrompt: "You are a helpful coding assistant"
  }
});
```

### 設定ソース (settingSources)

v0.1.0以降、SDKはデフォルトでファイルシステムの設定を読み込まない。必要に応じて明示的に指定する。

```typescript
// すべての設定ソースを読み込む（旧動作互換）:
const result = query({
  prompt: "Hello",
  options: {
    settingSources: ["user", "project", "local"]
  }
});

// プロジェクト設定のみ:
const result = query({
  prompt: "Hello",
  options: {
    settingSources: ["project"]  // Only project settings
  }
});
```

Python版:
```python
options=ClaudeAgentOptions(
    setting_sources=["project"]
)
```

### Claude Code機能（settingSourcesで有効化）

| 機能 | 説明 | 場所 |
|---|---|---|
| スキル | Markdownで定義された専門的な機能 | `.claude/skills/SKILL.md` |
| スラッシュコマンド | 一般的なタスク用のカスタムコマンド | `.claude/commands/*.md` |
| メモリ | プロジェクトのコンテキストと指示 | `CLAUDE.md` または `.claude/CLAUDE.md` |
| プラグイン | カスタムコマンド、エージェント、MCPサーバーで拡張 | `plugins` オプションによるプログラム的設定 |

---

## 6. セッション管理

### セッションの基本フロー

1. `query`を呼び出すと、SDKが自動的にセッションを作成
2. 最初のシステムメッセージ（`type === 'system'`, `subtype === 'init'`）でセッションIDが返される
3. セッションIDを保存し、後で`resume`オプションに指定してセッションを再開

### セッションIDの取得

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk"

let sessionId: string | undefined

const response = query({
  prompt: "Help me build a web application",
  options: {
    model: "claude-opus-4-6"
  }
})

for await (const message of response) {
  if (message.type === 'system' && message.subtype === 'init') {
    sessionId = message.session_id
    console.log(`Session started with ID: ${sessionId}`)
  }
  console.log(message)
}
```

### セッションの再開

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk"

const response = query({
  prompt: "Continue implementing the authentication system from where we left off",
  options: {
    resume: "session-xyz", // Session ID from previous conversation
    model: "claude-opus-4-6",
    allowedTools: ["Read", "Edit", "Write", "Glob", "Grep", "Bash"]
  }
})

for await (const message of response) {
  console.log(message)
}
```

SDKはセッションを再開する際に会話履歴とコンテキストの読み込みを自動的に処理し、Claudeが中断したところから正確に継続できるようにする。

### セッションのフォーク

セッションを再開する際、元のセッションを継続するか、新しいブランチにフォークするかを選択できる。

| 動作 | `forkSession: false`（デフォルト） | `forkSession: true` |
|---|---|---|
| セッションID | 元と同じ | 新しいセッションIDが生成される |
| 履歴 | 元のセッションに追加 | 再開ポイントから新しいブランチを作成 |
| 元のセッション | 変更される | 変更されずに保持 |
| ユースケース | 線形的な会話を継続 | 代替案を探索するためにブランチ |

#### フォークの利用シーン

- 同じ開始点から異なるアプローチを探索する
- 元のセッションを変更せずに複数の会話ブランチを作成する
- 元のセッション履歴に影響を与えずに変更をテストする
- 異なる実験のために別々の会話パスを維持する

#### フォークの例

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk"

let sessionId: string | undefined

const response = query({
  prompt: "Help me design a REST API",
  options: { model: "claude-opus-4-6" }
})

for await (const message of response) {
  if (message.type === 'system' && message.subtype === 'init') {
    sessionId = message.session_id
    console.log(`Original session: ${sessionId}`)
  }
}

// Fork the session to try a different approach
const forkedResponse = query({
  prompt: "Now let's redesign this as a GraphQL API instead",
  options: {
    resume: sessionId,
    forkSession: true,  // Creates a new session ID
    model: "claude-opus-4-6"
  }
})

for await (const message of forkedResponse) {
  if (message.type === 'system' && message.subtype === 'init') {
    console.log(`Forked session: ${message.session_id}`)
  }
}

// The original session remains unchanged and can still be resumed
const originalContinued = query({
  prompt: "Add authentication to the REST API",
  options: {
    resume: sessionId,
    forkSession: false,  // Continue original session (default)
    model: "claude-opus-4-6"
  }
})
```

---

## 7. 移行ガイド（Claude Code SDK → Claude Agent SDK）

### パッケージ名の変更

| 項目 | 旧 | 新 |
|---|---|---|
| パッケージ名 (TS/JS) | `@anthropic-ai/claude-code` | `@anthropic-ai/claude-agent-sdk` |
| Python パッケージ | `claude-code-sdk` | `claude-agent-sdk` |

### TypeScript移行手順

```bash
npm uninstall @anthropic-ai/claude-code
npm install @anthropic-ai/claude-agent-sdk
```

```typescript
// Before
import { query, tool, createSdkMcpServer } from "@anthropic-ai/claude-code";

// After
import {
  query,
  tool,
  createSdkMcpServer,
} from "@anthropic-ai/claude-agent-sdk";
```

```json
// Before
{
  "dependencies": {
    "@anthropic-ai/claude-code": "^1.0.0"
  }
}

// After
{
  "dependencies": {
    "@anthropic-ai/claude-agent-sdk": "^0.1.0"
  }
}
```

### Python移行手順

```bash
pip uninstall claude-code-sdk
pip install claude-agent-sdk
```

```python
# Before
from claude_code_sdk import query, ClaudeCodeOptions

# After
from claude_agent_sdk import query, ClaudeAgentOptions
```

### 破壊的変更一覧

| 変更 | v0.0.x（旧） | v0.1.0（新） | 影響 |
|---|---|---|---|
| Python型名 | `ClaudeCodeOptions` | `ClaudeAgentOptions` | import文と型宣言の更新が必要 |
| システムプロンプト | Claude Codeのシステムプロンプトがデフォルト | 最小限のシステムプロンプトがデフォルト | 旧動作が必要なら `systemPrompt: { type: "preset", preset: "claude_code" }` を指定 |
| 設定ソース | 全設定ファイルを自動読み込み | デフォルトで設定を読み込まない | 旧動作が必要なら `settingSources: ["user", "project", "local"]` を指定 |

#### 設定ソース無効化の理由

デフォルトで設定を読み込まなくなった理由：
- **CI/CD環境** - ローカルカスタマイズなしで一貫した動作
- **デプロイされたアプリケーション** - ファイルシステム設定への依存なし
- **テスト** - 分離されたテスト環境
- **マルチテナントシステム** - ユーザー間の設定漏洩を防止

---

## 8. SDKの位置づけ

Claude Agent SDKは、コーディングタスクだけでなく、あらゆる種類のAIエージェントを構築するためのフレームワーク：

- ビジネスエージェント（法律アシスタント、ファイナンスアドバイザー、カスタマーサポート）
- 特化型コーディングエージェント（SREボット、セキュリティレビュアー、コードレビューエージェント）
- ツール使用、MCP統合などを活用した、あらゆるドメイン向けカスタムエージェント

---

## 9. 設計判断ポイント

以下は、Agent SDKを使用してエージェントを設計する際に検討すべき主要な判断ポイントである。

### 言語選択: Python vs TypeScript

- 両言語ともに同じ`query`関数ベースのAPIを提供
- Pythonでは`ClaudeAgentOptions`、TypeScriptではオブジェクトリテラルでオプション指定
- Pythonでは`async for`、TypeScriptでは`for await`でストリーミング
- プロジェクトの既存技術スタックに合わせて選択

### 認証プロバイダー選択

- **Anthropic API直接**: 最もシンプル。`ANTHROPIC_API_KEY`のみで開始可能
- **Bedrock / Vertex AI / Azure**: 既存クラウドインフラとの統合、企業ガバナンス要件、データローカリティが必要な場合

### パーミッションモードの選択

- **`acceptEdits`**: 開発ワークフローでファイル編集を自動承認したい場合。ほとんどの開発エージェントに適する
- **`bypassPermissions`**: CI/CDパイプラインや完全自動化。人間の介入が不要な場合
- **`default` + `canUseTool`**: ユーザー承認フローが必要な場合。プロダクション環境でユーザー操作を確認する場合

### ツール構成の判断

- **読み取り専用分析**（`Read`, `Glob`, `Grep`）: コードレビュー、監査など破壊的操作が不要な場合
- **コード修正**（`Read`, `Edit`, `Glob`）: バグ修正、リファクタリングなどファイル変更が必要な場合
- **完全自動化**（`Read`, `Edit`, `Bash`, `Glob`, `Grep`）: テスト実行、ビルド、デプロイを含む場合
- `WebSearch`追加: 外部情報の検索が必要な場合

### システムプロンプトの設計

- **デフォルト（最小限）**: SDKアプリケーション独自の動作を定義したい場合。v0.1.0以降のデフォルト
- **`claude_code`プリセット**: Claude Code CLIと同等の動作が必要な場合。旧SDKからの移行互換
- **カスタムプロンプト**: 特定ドメイン（法律、金融など）やコーディング規約（PEP 8など）を遵守させたい場合

### 設定ソースの判断

- **指定なし（デフォルト）**: CI/CD、デプロイ環境、マルチテナントシステム。予測可能な動作を保証
- **`["project"]`のみ**: プロジェクト固有のスキルやCLAUDE.mdを活用したい場合
- **`["user", "project", "local"]`**: Claude Code CLIと同等のフル設定。開発者のローカル環境向け

### セッション管理の設計

- **セッションなし（シングルターン）**: 1回のタスク完了で終了する場合。CIパイプラインなど
- **セッション再開（`resume`）**: マルチターン会話。長期的な開発ワークフローでコンテキストを維持
- **セッションフォーク（`forkSession: true`）**: 同一コンテキストから複数のアプローチを試す場合。A/Bテスト的な設計探索

### ストリーミング vs シングルターン

- **ストリーミング（`async for`）**: リアルタイムで進捗表示が必要な対話型エージェント
- **シングルターン**: ライブ出力が不要なバックグラウンドジョブやCIパイプライン

### 出力処理の判断

- **フィルタリングあり**: `AssistantMessage`と`ResultMessage`を選別して人間が読みやすい出力を表示
- **フィルタリングなし**: デバッグ用。システム初期化や内部状態を含む生のメッセージオブジェクトを確認
