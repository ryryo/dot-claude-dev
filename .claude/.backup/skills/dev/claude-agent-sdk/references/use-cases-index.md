# ユースケースカタログ（インデックス）

Claude Agent SDK で実現できるアプリケーションパターンの一覧。
[公式デモリポジトリ](https://github.com/anthropics/claude-agent-sdk-demos)の実装を基にまとめている。

**Phase 1（ヒアリング）でこのファイルを読み込み、ユーザーに近いパターンを提示する。**
**Phase 2 で該当ユースケースの詳細ファイルを読み込む。**

---

## ユースケース一覧

| # | ユースケース | パターン | SDK主要機能 | 言語 | 複雑度 | 詳細 |
|---|------------|---------|------------|------|--------|------|
| 1 | CLIツール（ワンショット） | query() → ストリーム消費 | query, allowedTools, hooks | TS | ★☆☆ | [examples/01-cli-oneshot.md](examples/01-cli-oneshot.md) |
| 2 | セッション型マルチターン | V2 Session API | createSession, resumeSession, prompt | TS | ★★☆ | [examples/02-v2-session.md](examples/02-v2-session.md) |
| 3 | WebSocket チャットアプリ | query() + MessageQueue | ストリーミング入力, セッション管理 | TS | ★★☆ | [examples/03-websocket-chat.md](examples/03-websocket-chat.md) |
| 4 | マルチエージェントシステム | ClaudeSDKClient + AgentDefinition | サブエージェント, HookMatcher, Task | Python | ★★★ | [examples/04-multi-agent.md](examples/04-multi-agent.md) |
| 5 | MCPツール統合アプリ | createSdkMcpServer + WebSocket | MCPツール定義, フック, resume | TS | ★★★ | [examples/05-mcp-tools.md](examples/05-mcp-tools.md) |
| 6 | デスクトップアプリ（Electron） | Electron IPC + query() | query, settingSources, Skill | TS | ★★☆ | [examples/06-electron-desktop.md](examples/06-electron-desktop.md) |
| 7 | ドキュメント自動生成 | query() + Skill + WebSearch | ワンショット, スキル連携 | TS | ★☆☆ | [examples/07-doc-generation.md](examples/07-doc-generation.md) |

**横断パターン**: [examples/common-patterns.md](examples/common-patterns.md)（ストリーミング消費、Hooks、Resume、Skill連携）

---

## ユースケース選定ガイド

### 「何を作りたいか」→ 推奨パターン

| 作りたいもの | 推奨ユースケース | 読み込むファイル |
|------------|----------------|----------------|
| シンプルなCLIツール | #1 CLIツール | 01-cli-oneshot.md |
| 対話型アシスタント | #2 V2 Session or #3 WebSocket | 02 or 03 |
| Webアプリのチャット機能 | #3 WebSocket チャット | 03-websocket-chat.md |
| 複数タスクの並列処理 | #4 マルチエージェント | 04-multi-agent.md |
| 外部API連携（DB、メール等） | #5 MCPツール統合 | 05-mcp-tools.md |
| デスクトップアプリ | #6 Electron | 06-electron-desktop.md |
| ドキュメント自動生成 | #7 ドキュメント生成 | 07-doc-generation.md |
| 上記の組み合わせ | 複数参照 | 該当ファイル + common-patterns.md |

### 利用環境 → 推奨パターン

| 利用環境 | 推奨 |
|---------|------|
| CLI ツール | #1, #7 |
| Webアプリのバックエンド | #3, #5 |
| CI/CD パイプライン | #1 |
| インタラクティブな対話ツール | #2, #3 |
| デスクトップアプリ | #6 |
| マルチエージェント並列処理 | #4 |

### 技術的判断基準

| 判断ポイント | 選択肢 |
|------------|--------|
| **セッション不要**（1回で完了） | #1, #7 |
| **セッション必要**（マルチターン） | #2（V2 API）or #3（MessageQueue） |
| **サブエージェント必要** | #4（Python） |
| **独自ツール必要**（DB、API等） | #5（MCP） |
| **GUI 必要** | #3（Web）or #6（Electron） |
