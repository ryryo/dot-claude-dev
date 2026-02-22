---
name: claude-agent-sdk
description: |
  Claude Agent SDK（Python / TypeScript）を使った機能実装の設計をサポートするスキル。
  ヒアリング型ワークフローでユーザーの要件を明確化し、
  公式ドキュメントに基づいた最適なアーキテクチャと実装パターンを提案する。

  Trigger:
  Agent SDK, claude_agent_sdk, claude-agent-sdk, ClaudeAgentOptions, ClaudeSDKClient,
  Agent SDKで, エージェントSDK, エージェントを作りたい, agent-sdkを使って,
  query(), createSdkMcpServer, サブエージェント構成, agent architecture
allowed-tools:
  - Read
  - Glob
  - Grep
  - AskUserQuestion
  - Task
---

# Claude Agent SDK 設計サポート

## 概要

Claude Agent SDK（Python / TypeScript）を使った機能実装の設計をサポートするスキル。
**ヒアリング型ワークフロー**でユーザーの要件を明確化し、公式ドキュメントに基づいた最適なアーキテクチャと実装パターンを提案する。

## 設計原則

| 原則 | 説明 |
|------|------|
| **Hearing First** | まずヒアリングで要件を明確化してから設計提案 |
| **Use Case Driven** | 公式デモの実装パターンを基にした具体的なユースケース提案 |
| **Progressive Disclosure** | 必要なリファレンスのみを読み込み |
| **Both Languages** | Python / TypeScript 両方の実装パターンを提示 |
| **Design-Oriented** | コード生成ではなく設計判断を支援 |

---

## ワークフロー

```
Phase 1: 要件ヒアリング
  → agents/interview-requirements.md を読み込み
  → AskUserQuestion で要件を明確化
  → references/use-cases-index.md を読み込み、近いユースケース番号を特定
      ↓
Phase 2: ユースケース詳細 & リファレンス参照
  → Phase 1 で特定したユースケース番号の examples/0X-*.md を読み込み
  → 組合せ設計時は examples/common-patterns.md も読み込み
  → ヒアリング結果に基づき必要な references/ を追加読み込み
      ↓
Phase 3: 設計提案
  → examples/ のアーキテクチャ図・コード例を土台に設計提案
```

### Phase 1: 要件ヒアリング

1. **agents/interview-requirements.md** を読み込み、ヒアリング項目を把握する
2. **references/use-cases-index.md** を読み込み、ユースケースカタログを把握する
3. **AskUserQuestion** で以下を確認する:
   - **目的**: 何を作りたいか（エージェントの用途）
   - **機能**: 必要な機能（ツール、MCP、サブエージェント等）
   - **言語**: Python or TypeScript
   - **I/O**: ストリーミング / シングル / 構造化出力
   - **セッション**: ワンショット / 継続 / フォーク
   - **デプロイ**: ローカル / コンテナ / クラウド
   - **セキュリティ**: 権限モード、サンドボックス
   - **コスト**: トークン制限、最適化要件
4. ヒアリング結果を **use-cases-index.md の選定ガイド**と照合し、**該当ユースケース番号（#1〜#7）を特定**してユーザーに提示する

### Phase 2: ユースケース詳細 & リファレンス参照

Phase 1 で特定したユースケース番号に基づき、以下の順で読み込む:

#### Step 1: ユースケース詳細を読み込む（必須）

Phase 1 で特定した番号に対応するファイルを読み込む:

| ユースケース | ファイル |
|------------|---------|
| #1 CLIツール（ワンショット） | [references/examples/01-cli-oneshot.md](references/examples/01-cli-oneshot.md) |
| #2 セッション型マルチターン | [references/examples/02-v2-session.md](references/examples/02-v2-session.md) |
| #3 WebSocket チャットアプリ | [references/examples/03-websocket-chat.md](references/examples/03-websocket-chat.md) |
| #4 マルチエージェントシステム | [references/examples/04-multi-agent.md](references/examples/04-multi-agent.md) |
| #5 MCPツール統合アプリ | [references/examples/05-mcp-tools.md](references/examples/05-mcp-tools.md) |
| #6 デスクトップアプリ（Electron） | [references/examples/06-electron-desktop.md](references/examples/06-electron-desktop.md) |
| #7 ドキュメント自動生成 | [references/examples/07-doc-generation.md](references/examples/07-doc-generation.md) |

> 複数ユースケースを組み合わせる場合は、該当する複数ファイル + [references/examples/common-patterns.md](references/examples/common-patterns.md) を読み込む。

#### Step 2: 基礎リファレンスを読み込む（必須）

| トピック | リファレンス |
|----------|-------------|
| SDK基礎・セッション | [references/core-concepts.md](references/core-concepts.md) |

#### Step 3: 追加リファレンスを読み込む（該当時のみ）

ヒアリング結果に基づき、**必要なリファレンスのみ**を追加で読み込む:

| トピック | リファレンス | 読み込み条件 |
|----------|-------------|-------------|
| サブエージェント・ツール・MCP | [references/agent-architecture/index.md](references/agent-architecture/index.md) | カスタムツール・MCP使用時（→詳細: subagents, mcp, custom-tools, plugins-and-skills） |
| ストリーミング・構造化出力 | [references/io-and-streaming/index.md](references/io-and-streaming/index.md) | I/Oモード選択時（→詳細: streaming-output, structured-output, approval-and-input） |
| 権限・フック・設定 | [references/system-configuration/index.md](references/system-configuration/index.md) | 権限・フック設計時（→詳細: hooks, commands-and-todo, checkpoints） |
| デプロイ・セキュリティ | [references/deployment-and-operations.md](references/deployment-and-operations.md) | 本番デプロイ・セキュリティ設計時 |
| API詳細 | [references/sdk-reference/index.md](references/sdk-reference/index.md) | API仕様確認時（→詳細: python-api, typescript-api, common-options, hooks-api, tools-api） |

### Phase 3: 設計提案

Phase 2 で読み込んだ **examples/ のアーキテクチャ図・コード例を土台**に、以下の形式で提案する:

```
## 設計提案

### 参考ユースケース
- ベースパターン: #X（examples/0X-*.md のタイトル）
- 追加パターン: #Y（該当する場合）
- 参照元: examples/0X-*.md のアーキテクチャ図・実装ポイント

### アーキテクチャ概要
[examples/0X-*.md のアーキテクチャ図をベースに、ユーザー要件に合わせてカスタマイズした構成図・説明]

### 推奨構成
- 言語: Python / TypeScript
- 入力モード: ストリーミング / シングル
- 権限モード: default / acceptEdits / bypassPermissions
- セッション: ワンショット / 継続 / フォーク
- デプロイ: パターン名

### 実装ステップ
1. [examples/0X-*.md の実装ポイントを参考に具体的なステップを記述]
2. ...

### コード例（Python / TypeScript）
[examples/0X-*.md のコード例をベースに、ユーザー要件に合わせて調整したコードを提示]
[複数パターン組合せ時は common-patterns.md のコード例も活用]
```

---

## クイックリファレンス

### Agent SDK 比較表

| 特徴 | Python | TypeScript |
|------|--------|------------|
| パッケージ | claude-agent-sdk | @anthropic-ai/claude-agent-sdk |
| メイン関数 | query() | query() |
| オプション型 | ClaudeAgentOptions | ClaudeAgentOptions |
| 永続セッション | ClaudeSDKClient | - |
| スキーマ検証 | Pydantic | Zod |
| V2 API | - | unstable_v2_prompt() |

### 権限モード早見表

| モード | ファイル操作 | Bash | 全ツール |
|--------|------------|------|---------|
| default | 承認要求 | 承認要求 | 承認要求 |
| acceptEdits | 自動承認 | 承認要求 | 承認要求 |
| bypassPermissions | 自動承認 | 自動承認 | 自動承認 |
| plan | 実行不可 | 実行不可 | 実行不可 |

### 入力モード比較

| 機能 | ストリーミング | シングル |
|------|--------------|---------|
| 画像アップロード | 可 | 不可 |
| メッセージキュー | 可 | 不可 |
| フック | 可 | 不可 |
| リアルタイムフィードバック | 可 | 不可 |
| シンプルさ | - | 可 |

### デプロイパターン

| パターン | 説明 | 適用場面 |
|----------|------|----------|
| エフェメラル | リクエスト毎にコンテナ | API/Webhook |
| 長時間実行 | 永続プロセス | 常駐サービス |
| ハイブリッド | 用途に応じて切替 | 大規模システム |
| シングルコンテナ | 1コンテナ内で実行 | 開発・テスト |

---

## ベストプラクティス

| すべきこと | 避けるべきこと |
|-----------|---------------|
| ストリーミング入力を使う（本番） | シングルモードを本番で使う |
| 最小権限の原則で権限モード選択 | bypassPermissionsを無条件で使う |
| フックで危険なコマンドを制御 | 権限チェックなしでBash実行 |
| セッションIDを保存して再開可能に | 毎回新規セッションを作成 |
| maxTurnsでコスト制限 | トークン使用量を監視しない |
| カスタムツールにZod/Pydanticスキーマ | 型なしのツール定義 |
