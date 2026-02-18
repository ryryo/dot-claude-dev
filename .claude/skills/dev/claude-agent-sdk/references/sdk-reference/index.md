# SDK API Reference - Claude Agent SDK

Agent SDKのPython/TypeScript両言語の統合APIリファレンス。設計判断に必要な型定義、設定オプション、コード例を網羅する。

---

## ファイル構成

| トピック | ファイル | 概要 |
|---------|---------|------|
| Python SDK API | [python-api.md](./python-api.md) | `query()`、`ClaudeSDKClient`、会話継続、ストリーミング入力、中断、権限制御の例 |
| TypeScript SDK API | [typescript-api.md](./typescript-api.md) | TypeScript V1 `query()`/`Query`インターフェース、V2プレビュー（`createSession`/`resumeSession`/`prompt`） |
| 共通オプション・権限・設定 | [common-options.md](./common-options.md) | `ClaudeAgentOptions`/`Options`、`PermissionMode`、`SettingSource`、`SandboxSettings` |
| フックシステム | [hooks-api.md](./hooks-api.md) | `HookEvent`、`HookCallback`、`HookMatcher`、フック入出力型、使用例 |
| ツール・MCP・サブエージェント | [tools-api.md](./tools-api.md) | `McpServerConfig`、`tool()`デコレータ/関数、`createSdkMcpServer`、`AgentDefinition` |
| 型定義 | [types.md](./types.md) | メッセージ型、コンテンツブロック型、組み込みツール入出力型、エラー型、その他の型 |

---

## インストール

**Python:**
```
pip install claude-agent-sdk
```

**TypeScript:**
```
npm install @anthropic-ai/claude-agent-sdk
```

---

## Python vs TypeScript 比較表

### 主要API対応表

| 機能 | Python | TypeScript V1 | TypeScript V2 |
|------|--------|---------------|---------------|
| ワンショットクエリ | `query()` | `query()` | `unstable_v2_prompt()` |
| セッション維持 | `ClaudeSDKClient` | `query()` + streaming input | `createSession()` |
| セッション再開 | `ClaudeSDKClient` + `resume` | `query()` + `resume` option | `resumeSession()` |
| 中断 | `client.interrupt()` | `query.interrupt()` | - |
| ファイル巻き戻し | `client.rewind_files()` | `query.rewindFiles()` | - |
| ツール定義 | `@tool` デコレータ + dict/type schema | `tool()` + Zod schema | V1と共有 |
| MCPサーバー作成 | `create_sdk_mcp_server()` | `createSdkMcpServer()` | V1と共有 |
| パーミッション変更 | - | `query.setPermissionMode()` | - |
| モデル変更 | - | `query.setModel()` | - |

### オプション名の対応

| Python (`ClaudeAgentOptions`) | TypeScript (`Options`) |
|-------------------------------|------------------------|
| `system_prompt` | `systemPrompt` |
| `permission_mode` | `permissionMode` |
| `allowed_tools` | `allowedTools` |
| `disallowed_tools` | `disallowedTools` |
| `max_turns` | `maxTurns` |
| `max_budget_usd` | `maxBudgetUsd` |
| `max_thinking_tokens` | `maxThinkingTokens` |
| `mcp_servers` | `mcpServers` |
| `cli_path` | `pathToClaudeCodeExecutable` |
| `add_dirs` | `additionalDirectories` |
| `extra_args` | `extraArgs` |
| `can_use_tool` | `canUseTool` |
| `include_partial_messages` | `includePartialMessages` |
| `fork_session` | `forkSession` |
| `setting_sources` | `settingSources` |
| `output_format` | `outputFormat` |
| `fallback_model` | `fallbackModel` |
| `continue_conversation` | `continue` |
| `enable_file_checkpointing` | `enableFileCheckpointing` |
| `max_buffer_size` | - (TypeScriptにはなし) |
| `debug_stderr` (非推奨) | - |
| `stderr` | `stderr` |
| `user` | - (TypeScriptにはなし) |
| - | `abortController` (Pythonにはなし) |
| - | `executable` (Pythonにはなし) |
| - | `executableArgs` (Pythonにはなし) |
| - | `allowDangerouslySkipPermissions` (Pythonにはなし) |
| - | `strictMcpConfig` (Pythonにはなし) |
| - | `resumeSessionAt` (Pythonにはなし) |

### フックイベントの対応

| イベント | Python | TypeScript |
|---------|--------|------------|
| `PreToolUse` | サポート | サポート |
| `PostToolUse` | サポート | サポート |
| `PostToolUseFailure` | 非サポート | サポート |
| `Notification` | 非サポート | サポート |
| `UserPromptSubmit` | サポート | サポート |
| `SessionStart` | 非サポート | サポート |
| `SessionEnd` | 非サポート | サポート |
| `Stop` | サポート | サポート |
| `SubagentStart` | 非サポート | サポート |
| `SubagentStop` | サポート | サポート |
| `PreCompact` | サポート | サポート |
| `PermissionRequest` | 非サポート | サポート |

---

## 設計判断ポイント

### Python vs TypeScript の選択基準

**Pythonを選ぶ場合:**
- データサイエンス/ML系のワークフローに統合する場合
- asyncioベースの非同期処理に慣れている場合
- `ClaudeSDKClient` による明示的なセッションライフサイクル管理が必要な場合
- コンテキストマネージャー（`async with`）によるリソース管理を活用したい場合

**TypeScriptを選ぶ場合:**
- Node.js/Web系のアプリケーションに統合する場合
- Zodスキーマによる型安全なツール定義を活用したい場合
- より多くのフックイベント（SessionStart/End、Notification、PermissionRequest等）が必要な場合
- `Query` オブジェクトの追加メソッド（`setPermissionMode`、`setModel`、`supportedModels`等）が必要な場合
- `AbortController` によるキャンセル機構を使いたい場合

### TypeScript V1 vs V2 の選択基準

**V1を選ぶ場合:**
- 安定したAPIが必要な場合（V2はプレビュー段階）
- セッションフォーク（`forkSession`）が必要な場合
- 高度なストリーミング入力パターンが必要な場合
- 単一の非同期ジェネレーターで入出力を処理したい場合

**V2を選ぶ場合:**
- マルチターン会話を簡潔に実装したい場合
- `send()` / `stream()` の明確な分離が望ましい場合
- セッションの作成・再開を直感的に行いたい場合
- TypeScript 5.2+の `await using` による自動リソース管理を活用したい場合
- APIの変更を許容できるプロジェクトの場合

### query() vs ClaudeSDKClient（Python）の選択基準

**`query()` を選ぶ場合:**
- 会話履歴が不要な単発の質問
- 独立したタスク
- シンプルな自動化スクリプト

**`ClaudeSDKClient` を選ぶ場合:**
- 会話の継続が必要（Claudeにコンテキストを記憶させる）
- フォローアップの質問
- 中断サポートが必要
- カスタムツール・フックが必要
- セッションのライフサイクルを明示的に管理したい

### 権限モードの選択指針

| モード | ユースケース | リスク |
|--------|-----------|--------|
| `default` | インタラクティブな使用、ユーザーが承認を確認可能 | なし |
| `acceptEdits` | CI/CD、ファイル変更を自動承認したい場合 | ファイル変更が自動承認される |
| `plan` | コードレビュー、変更プランの確認のみ | 実行不可 |
| `bypassPermissions` | 完全自動化、信頼された環境のみ | すべての権限チェックがバイパスされる |

### setting_sources の設計指針

- **デフォルト（省略/None）:** ファイルシステム設定を読み込まない。SDK専用アプリケーションの分離に最適。
- **`["project"]`:** プロジェクトの `.claude/settings.json` とCLAUDE.mdのみ読み込む。CI環境やチーム共有設定に最適。
- **`["user", "project", "local"]`:** すべて読み込む。レガシー動作の再現に使用。
- **CLAUDE.mdを読み込むには:** `setting_sources` に `"project"` を含め、かつ `system_prompt` にプリセットを使用する必要がある。

### サンドボックス設計の指針

- コマンド実行の分離にはサンドボックス設定を使用する
- ファイルシステム/ネットワークのアクセス制御にはパーミッションルールを使用する
- `bypassPermissions` + `allowUnsandboxedCommands` の組み合わせはモデルがサンドボックス分離を暗黙的に回避できるため、極めて慎重に使用すること
- `excludedCommands` は静的、`allowUnsandboxedCommands` は動的（モデルがリクエスト時に決定）
