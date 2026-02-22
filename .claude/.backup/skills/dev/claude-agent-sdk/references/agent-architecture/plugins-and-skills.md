# プラグインとAgent Skills

## プラグイン

プラグインは、プロジェクト全体で共有できるカスタム機能のパッケージ。Agent SDKを通じて、ローカルディレクトリからプログラムで読み込む。

### プラグインに含まれるもの

| コンポーネント | 説明 |
|:------------|:-----|
| **コマンド** | カスタムスラッシュコマンド |
| **エージェント** | 特定のタスク用の特殊なサブエージェント |
| **スキル** | Claude が自律的に使用するモデル呼び出し機能 |
| **フック** | ツール使用およびその他のイベントに応答するイベントハンドラー |
| **MCP サーバー** | Model Context Protocol 経由の外部ツール統合 |

### プラグインの読み込み

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Hello",
  options: {
    plugins: [
      { type: "local", path: "./my-plugin" },
      { type: "local", path: "/absolute/path/to/another-plugin" }
    ]
  }
})) {
  // Plugin commands, agents, and other features are now available
}
```

### パス指定

- **相対パス**: 現在の作業ディレクトリを基準に解決
- **絶対パス**: ファイルシステムの完全なパス

パスはプラグインのルートディレクトリ（`.claude-plugin/plugin.json` を含むディレクトリ）を指す必要がある。

### プラグインインストールの確認

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Hello",
  options: {
    plugins: [{ type: "local", path: "./my-plugin" }]
  }
})) {
  if (message.type === "system" && message.subtype === "init") {
    console.log("Plugins:", message.plugins);
    console.log("Commands:", message.slash_commands);
  }
}
```

### プラグインコマンドの使用

コマンドは `plugin-name:command-name` 形式で名前空間化される:

```typescript
for await (const message of query({
  prompt: "/my-plugin:greet",
  options: {
    plugins: [{ type: "local", path: "./my-plugin" }]
  }
})) {
  if (message.type === "assistant") {
    console.log(message.content);
  }
}
```

### プラグイン構造

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Required: plugin manifest
├── commands/                 # Custom slash commands
│   └── custom-cmd.md
├── agents/                   # Custom agents
│   └── specialist.md
├── skills/                   # Agent Skills
│   └── my-skill/
│       └── SKILL.md
├── hooks/                    # Event handlers
│   └── hooks.json
└── .mcp.json                # MCP server definitions
```

### 一般的なユースケース

```typescript
// 開発とテスト
plugins: [
  { type: "local", path: "./dev-plugins/my-plugin" }
]

// プロジェクト固有の拡張機能
plugins: [
  { type: "local", path: "./project-plugins/team-workflows" }
]

// 複数のプラグインソース
plugins: [
  { type: "local", path: "./local-plugin" },
  { type: "local", path: "~/.claude/custom-plugins/shared-plugin" }
]
```

---

## Agent Skills

Agent SkillsはClaudeに専門的な機能を拡張し、Claudeが関連する場面で自律的に呼び出す。`SKILL.md` ファイルとしてパッケージ化される。

### SkillsがSDKでどのように機能するか

1. **ファイルシステムアーティファクトとして定義**: `.claude/skills/` ディレクトリに `SKILL.md` ファイルとして作成
2. **ファイルシステムから読み込み**: `settingSources`（TS）/ `setting_sources`（Python）の指定が必要
3. **自動的に検出**: 起動時にメタデータが検出され、トリガー時にフルコンテンツがロード
4. **モデルによる呼び出し**: Claudeがコンテキストに基づいて自律的に選択
5. **allowed_toolsで有効化**: `"Skill"` を追加

**デフォルトの動作**: SDKはデフォルトではファイルシステム設定を読み込まない。明示的に `settingSources` / `setting_sources` を設定する必要がある。

サブエージェント（プログラムで定義可能）とは異なり、SkillsはファイルシステムアーティファクトとしてのみSKILL.mdとして作成する必要がある。SDKはSkillsを登録するためのプログラムAPIを提供していない。

### SDKでの使用

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        cwd="/path/to/project",  # .claude/skills/を含むプロジェクト
        setting_sources=["user", "project"],  # ファイルシステムからSkillsを読み込み
        allowed_tools=["Skill", "Read", "Write", "Bash"]  # Skillツールを有効化
    )

    async for message in query(
        prompt="Help me process this PDF document",
        options=options
    ):
        print(message)

asyncio.run(main())
```

### Skillの場所

| 場所 | パス | 条件 |
|:-----|:-----|:-----|
| プロジェクトSkills | `.claude/skills/` | `setting_sources` に `"project"` が含まれる |
| ユーザーSkills | `~/.claude/skills/` | `setting_sources` に `"user"` が含まれる |
| プラグインSkills | プラグインにバンドル | プラグインがインストール済み |

### Skillsの作成

`SKILL.md` ファイルを含むディレクトリとして定義。`description` フィールドがClaudeがSkillを呼び出すタイミングを決定する。

```
.claude/skills/processing-pdfs/
└── SKILL.md
```

### ツールの制限に関する注意

SKILL.mdの `allowed-tools` フロントマターフィールドは、Claude Code CLIを直接使用する場合にのみサポートされる。**SDKを通じてSkillsを使用する場合には適用されない**。

SDKでは `allowedTools` オプションでツールアクセスを制御:

```python
options = ClaudeAgentOptions(
    setting_sources=["user", "project"],
    allowed_tools=["Skill", "Read", "Grep", "Glob"]  # 制限されたツールセット
)
```

### トラブルシューティング: Skillsが見つからない

```python
# 間違い - Skillsは読み込まれません
options = ClaudeAgentOptions(
    allowed_tools=["Skill"]
)

# 正しい - Skillsが読み込まれます
options = ClaudeAgentOptions(
    setting_sources=["user", "project"],  # Skillsの読み込みに必要
    allowed_tools=["Skill"]
)
```

作業ディレクトリ (`cwd`) が `.claude/skills/` を含むディレクトリを指していることを確認すること。
