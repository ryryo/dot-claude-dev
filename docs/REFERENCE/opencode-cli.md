# OpenCode CLI リファレンス

> Source: https://opencode.ai/docs/cli/

## 概要

OpenCode はターミナルベースのAIコーディングアシスタント。TUI（対話UI）とCLI（非対話）の2モードで動作する。

```bash
opencode              # TUI起動（デフォルト）
opencode run "prompt"  # 非対話モードで実行
```

---

## CLIコマンド一覧

### run（非対話実行）

```bash
opencode run [message..]
```

| オプション | 説明 |
|-----------|------|
| `-m, --model` | モデル指定（`provider/model`形式） |
| `-c, --continue` | 前回セッション継続 |
| `-s, --session` | セッションID指定 |
| `-f, --file` | 添付ファイル |
| `--format` | 出力形式: `default`（整形）/ `json`（イベントJSON） |
| `--agent` | 使用エージェント指定 |
| `--share` | セッション共有 |
| `--attach` | 起動中サーバーに接続（例: `http://localhost:4096`） |
| `--variant` | モデルバリアント（reasoning effort: high, max, minimal） |
| `--thinking` | thinkingブロック表示 |
| `--title` | セッションタイトル |

```bash
# 基本
opencode run "このコードをリファクタして"

# モデル指定
opencode run -m anthropic/claude-sonnet-4-20250514 "バグを修正して"

# JSON出力（パース用）
opencode run --format json "現在の日時を教えて"

# ファイル添付
opencode run -f screenshot.png "このUIの問題を指摘して"

# 前回セッション継続
opencode run -c "続きをお願い"
```

### agent（エージェント管理）

```bash
opencode agent create   # カスタムエージェント作成ウィザード
opencode agent list     # エージェント一覧
```

### auth（認証）

```bash
opencode auth login     # APIキー設定（~/.local/share/opencode/auth.json に保存）
opencode auth list      # 認証済みプロバイダ一覧
opencode auth logout    # 認証情報削除
```

### models（モデル一覧）

```bash
opencode models              # 全モデル一覧
opencode models anthropic    # プロバイダ指定
opencode models --refresh    # キャッシュ更新
opencode models --verbose    # メタデータ表示
```

### session（セッション管理）

```bash
opencode session list         # セッション一覧
opencode session list -n 10   # 件数制限
opencode export [sessionID]   # JSON エクスポート
opencode import <file>        # JSON インポート（URLも可）
```

### serve / web / attach（サーバー）

```bash
opencode serve                # ヘッドレスHTTP APIサーバー起動
opencode web                  # Webブラウザ UI起動
opencode attach <url>         # リモートサーバーにTUI接続
```

### mcp（MCP サーバー管理）

```bash
opencode mcp add              # MCPサーバー追加
opencode mcp list             # MCP一覧
opencode mcp auth <name>      # OAuth認証
opencode mcp debug <name>     # 接続デバッグ
```

### github（GitHub連携）

```bash
opencode github install       # GitHub Actions ワークフロー設定
opencode github run           # エージェント実行（--event, --token対応）
opencode pr <number>          # PRブランチ取得 → opencode起動
```

### その他

```bash
opencode stats                # トークン使用量・コスト表示（--days, --project）
opencode upgrade [version]    # アップデート
opencode uninstall            # アンインストール
opencode acp                  # Agent Client Protocol サーバー起動
opencode completion           # シェル補完スクリプト生成
opencode debug                # デバッグツール
```

### グローバルフラグ

| フラグ | 説明 |
|--------|------|
| `-h, --help` | ヘルプ表示 |
| `-v, --version` | バージョン表示 |
| `--print-logs` | stderrにログ出力 |
| `--log-level` | ログレベル（DEBUG/INFO/WARN/ERROR） |
| `--port` | リッスンポート |
| `--hostname` | リッスンホスト |

---

## 設定ファイル

### 形式と配置

JSON / JSONC（コメント付きJSON）。スキーマ参照推奨:

```jsonc
{
  "$schema": "https://opencode.ai/config.json"
}
```

### 読み込み順（後が優先）

1. リモート設定（`.well-known/opencode`）
2. グローバル: `~/.config/opencode/opencode.json`
3. `OPENCODE_CONFIG` 環境変数パス
4. プロジェクト: `./opencode.json`（git rootまで探索）
5. `.opencode/` ディレクトリ（agents, commands, tools等）
6. `OPENCODE_CONFIG_CONTENT` 環境変数（インライン）

### 主要設定項目

```jsonc
{
  "$schema": "https://opencode.ai/config.json",

  // モデル
  "model": "anthropic/claude-sonnet-4-20250514",
  "small_model": "anthropic/claude-haiku-4-5-20251001",

  // エージェント
  "default_agent": "build",
  "agent": { /* エージェント定義 */ },

  // ツール
  "tools": {
    "write": true,
    "bash": true
  },

  // パーミッション
  "permission": {
    "*": "ask",
    "bash": { "*": "ask", "git *": "allow" },
    "edit": { "*": "allow", "*.env": "deny" }
  },

  // MCPサーバー
  "mcp": { /* MCP定義 */ },

  // カスタムコマンド
  "command": { /* コマンド定義 */ },

  // その他
  "theme": "default",
  "share": "manual",
  "autoupdate": true
}
```

### 変数展開

```jsonc
{
  "provider": {
    "anthropic": {
      "options": {
        "apiKey": "{env:ANTHROPIC_API_KEY}"  // 環境変数
      }
    }
  },
  "instructions": ["{file:./AGENTS.md}"]     // ファイル内容
}
```

### 環境変数

| 変数 | 説明 |
|------|------|
| `OPENCODE_CONFIG` | 設定ファイルパス |
| `OPENCODE_SERVER_PASSWORD` | HTTP Basic認証有効化 |
| `OPENCODE_DISABLE_AUTOUPDATE` | 自動更新無効化 |
| `OPENCODE_EXPERIMENTAL` | 実験機能有効化 |

---

## エージェント

### 概要

エージェントはカスタムプロンプト・モデル・ツールを持つ特化AIアシスタント。`@`メンションまたはTabキーで切替。

### タイプ

| タイプ | 説明 | 組込み例 |
|--------|------|---------|
| `primary` | メインアシスタント | Build（全ツール）、Plan（制限付き） |
| `subagent` | 特化サブエージェント | General（全アクセス）、Explore（読取専用） |

### JSON定義

```jsonc
{
  "agent": {
    "my-agent": {
      "description": "カスタムエージェントの説明",
      "mode": "subagent",
      "model": "anthropic/claude-sonnet-4-20250514",
      "temperature": 0.3,
      "steps": 50,
      "tools": {
        "write": false,
        "bash": true
      },
      "permission": {
        "bash": { "*": "ask", "git *": "allow" }
      }
    }
  }
}
```

### Markdown定義

ファイル: `~/.config/opencode/agents/my-agent.md` または `.opencode/agents/my-agent.md`

```markdown
---
description: カスタムエージェントの説明
mode: subagent
model: anthropic/claude-sonnet-4-20250514
tools:
  write: false
---

あなたはコードレビュー専門のアシスタントです。
セキュリティとパフォーマンスの問題を重点的にチェックしてください。
```

### 設定オプション

| オプション | 説明 |
|-----------|------|
| `description` | エージェント説明（必須） |
| `mode` | `primary` / `subagent` / `all` |
| `model` | モデル指定 |
| `temperature` | 0.0-1.0 |
| `steps` | 最大反復数 |
| `prompt` | システムプロンプトファイルパス |
| `tools` | ツール有効/無効 |
| `permission` | ツール権限設定 |
| `color` | 表示色（hex） |

---

## ツール

### 組込みツール

| ツール | 説明 |
|--------|------|
| `read` | ファイル読取（行範囲指定可） |
| `write` | ファイル作成/上書き |
| `edit` | 文字列置換による編集 |
| `patch` | パッチ適用 |
| `grep` | 正規表現で内容検索 |
| `glob` | パターンでファイル検索 |
| `list` | ディレクトリ一覧 |
| `bash` | シェルコマンド実行 |
| `lsp` | Language Server（実験的） |
| `skill` | SKILL.md読込 |
| `question` | ユーザーへの質問 |
| `todowrite/todoread` | タスクリスト管理 |
| `webfetch` | Webページ取得 |

### カスタムツール

配置: `.opencode/tools/` または `~/.config/opencode/tools/`

```typescript
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "データベースクエリ実行",
  args: {
    query: tool.schema.string().describe("実行するSQL"),
  },
  async execute(args) {
    return `結果: ${args.query}`
  },
})
```

ファイル名がツール名になる。

---

## パーミッション

### 3段階

| 値 | 動作 |
|------|------|
| `allow` | 自動実行 |
| `ask` | ユーザー確認 |
| `deny` | ブロック |

### 粒度制御

```jsonc
{
  "permission": {
    "*": "ask",                              // デフォルト
    "bash": {
      "*": "ask",
      "git *": "allow",                     // git系は自動許可
      "rm *": "deny"                        // rm系は拒否
    },
    "edit": {
      "*": "allow",
      "*.env": "deny"                       // .envファイル編集禁止
    },
    "external_directory": {
      "~/other-project/**": "allow"         // 外部ディレクトリ許可
    }
  }
}
```

ルールは**後勝ち**（最後にマッチしたルールが適用）。

### 全パーミッション一覧

`read`, `edit`, `glob`, `grep`, `list`, `bash`, `task`, `skill`, `lsp`, `todoread`, `todowrite`, `webfetch`, `websearch`, `codesearch`, `external_directory`, `doom_loop`

---

## ルール（AGENTS.md）

### 配置と読込順

1. プロジェクトルート: `AGENTS.md`（ディレクトリ上方探索）
2. グローバル: `~/.config/opencode/AGENTS.md`
3. フォールバック: `CLAUDE.md`（互換性）

### 設定からの追加指示

```jsonc
{
  "instructions": [
    "./docs/CODING_STANDARDS.md",
    "packages/*/AGENTS.md",
    "https://example.com/rules.md"
  ]
}
```

---

## スキル（SKILL.md）

### 配置

```
.opencode/skills/<name>/SKILL.md    # プロジェクト
~/.config/opencode/skills/<name>/SKILL.md  # グローバル
.claude/skills/<name>/SKILL.md      # Claude互換パス
```

### フォーマット

```markdown
---
name: my-skill
description: スキルの説明（1-1024文字）
---

スキルの内容...
```

名前: `^[a-z0-9]+(-[a-z0-9]+)*$`（小文字英数+ハイフン）

---

## カスタムコマンド

### Markdown定義

ファイル: `.opencode/commands/test.md`

```markdown
---
description: テスト実行
agent: build
model: anthropic/claude-sonnet-4-20250514
---

以下のテストを実行して結果を報告してください。
対象: $ARGUMENTS
```

### JSON定義

```jsonc
{
  "command": {
    "test": {
      "template": "テスト実行: $ARGUMENTS",
      "description": "テスト実行",
      "agent": "build",
      "subtask": false
    }
  }
}
```

### プロンプト機能

| 構文 | 説明 | 例 |
|------|------|-----|
| `$ARGUMENTS` | 全引数 | `/test Button` → `Button` |
| `$1`, `$2` | 位置引数 | `/test a b` → `$1=a, $2=b` |
| `` !`cmd` `` | コマンド出力埋込 | `` !`npm test` `` |
| `@file` | ファイル内容埋込 | `@src/index.ts` |

TUIで `/command-name` で実行。

---

## MCPサーバー

### ローカルMCP

```jsonc
{
  "mcp": {
    "my-server": {
      "type": "local",
      "enabled": true,
      "command": ["npx", "-y", "@modelcontextprotocol/server-everything"],
      "environment": { "API_KEY": "{env:MY_API_KEY}" },
      "timeout": 5000
    }
  }
}
```

### リモートMCP

```jsonc
{
  "mcp": {
    "remote-server": {
      "type": "remote",
      "url": "https://mcp.example.com",
      "headers": { "Authorization": "Bearer {env:TOKEN}" },
      "timeout": 5000
    }
  }
}
```

---

## TUIショートカット

| コマンド | キー | 説明 |
|---------|------|------|
| `/compact` | `ctrl+x c` | セッション要約 |
| `/details` | `ctrl+x d` | ツール実行詳細トグル |
| `/editor` | `ctrl+x e` | 外部エディタ起動 |
| `/exit` | `ctrl+x q` | 終了 |
| `/export` | `ctrl+x x` | Markdownエクスポート |
| `/help` | `ctrl+x h` | ヘルプ |
| `/init` | `ctrl+x i` | AGENTS.md生成 |
| `/models` | `ctrl+x m` | モデル一覧 |
| `/new` | `ctrl+x n` | 新規セッション |
| `/redo` | `ctrl+x r` | Undo取消 |
| `/sessions` | `ctrl+x l` | セッション一覧 |
| `/share` | `ctrl+x s` | セッション共有 |
| `/themes` | `ctrl+x t` | テーマ一覧 |
| `/undo` | `ctrl+x u` | メッセージ取消 |

---

## プロバイダ

75+のLLMプロバイダをサポート。主要なもの:

| プロバイダ | 設定方法 |
|-----------|---------|
| OpenCode (Zen) | opencode.ai/auth で認証 |
| OpenAI | APIキー or ChatGPT Plus/Pro |
| Anthropic | APIキー or Claude Pro/Max認証 |
| Google Vertex AI | `GOOGLE_CLOUD_PROJECT` 環境変数 |
| Amazon Bedrock | AWS認証情報チェーン |
| Azure OpenAI | リソース名 + APIキー |
| Ollama | ローカルモデル（OpenAI互換） |
| GitHub Copilot | デバイスログイン |

```bash
# プロバイダ接続（TUI内）
/connect

# または CLI
opencode auth login
```

### 利用可能モデル一覧（2026-02-06時点）

| プロバイダ | モデル | 用途 |
|-----------|--------|------|
| `opencode` | `opencode/big-pickle` | OpenCode独自モデル |
| `opencode` | `opencode/glm-4.7-free` | 無料モデル |
| `opencode` | `opencode/gpt-5-nano` | 軽量モデル |
| `opencode` | `opencode/kimi-k2.5-free` | 無料モデル |
| `opencode` | `opencode/minimax-m2.1-free` | 無料モデル |
| `opencode` | `opencode/trinity-large-preview-free` | 無料プレビュー |
| `openai` | `openai/gpt-5.1-codex` | コーディング特化 |
| `openai` | `openai/gpt-5.1-codex-max` | コーディング特化（最大） |
| `openai` | `openai/gpt-5.1-codex-mini` | コーディング特化（軽量） |
| `openai` | `openai/gpt-5.2` | 汎用 |
| `openai` | `openai/gpt-5.2-codex` | コーディング特化 |
| `openai` | `openai/gpt-5.3-codex` | コーディング特化（最新） |
| `zai-coding-plan` | `zai-coding-plan/glm-5` | GLMシリーズ（最新） |
| `zai-coding-plan` | `zai-coding-plan/glm-4.7` | GLMシリーズ |

---

## Claude Code からの呼び出しパターン

```bash
# 基本: 非対話でタスク委譲
opencode run "コードを分析して問題点を報告" 2>&1

# JSON形式で結果取得（パース可能）
opencode run --format json "テストを実行" 2>&1

# モデル指定（GPT系）
opencode run -m openai/gpt-5.2 "セキュリティレビュー" 2>&1

# コーディング特化モデル
opencode run -m openai/gpt-5.3-codex "このコードをリファクタして" 2>&1

# 無料モデルで軽量タスク
opencode run -m opencode/gpt-5-nano "この関数の説明を書いて" 2>&1

# ファイル添付
opencode run -f src/main.ts "このファイルをレビュー" 2>&1

# セッション継続
opencode run -s <session-id> "前回の続き" 2>&1
```

### Claude Code連携のユースケース

| ユースケース | コマンド例 |
|------------|-----------|
| セカンドオピニオン | `opencode run -m openai/gpt-5.2 "この設計の問題点は？"` |
| コーディングレビュー | `opencode run -m openai/gpt-5.3-codex "セキュリティ観点でレビュー"` |
| GLMモデル利用 | `opencode run -m zai-coding-plan/glm-4.7 "コードを分析"` |
| 軽量タスク（無料） | `opencode run -m opencode/gpt-5-nano "変数名の改善案"` |
| 並列分析 | バックグラウンドで `opencode run` を実行 |
| Codex CLI代替 | GPT系codexモデルによる客観分析 |

---

## Claude Code Web（リモート）での利用

### モデルと認証の関係

| モデル群 | 認証 | リモートでの準備 |
|---------|------|-----------------|
| `opencode/*` (free) | 不要 | opencode インストールのみ |
| `openai/*` | OpenAI OAuth必要 | auth.json の復元が必要 |
| `zai-coding-plan/*` | APIキー必要 | auth.json の復元が必要 |

**無料モデルだけ使うなら `OPENCODE_AUTH_JSON` は不要。** opencode をインストールするだけで動く。有料モデル（`openai/*`, `zai-coding-plan/*`）を使うには auth.json の復元が必要。

### 2つの構成パターン

#### パターンA: 無料モデルのみ（認証なし）

必要なもの: opencode のインストールのみ

```bash
# リモートで使えるコマンド例
opencode run -m opencode/gpt-5-nano "この関数を説明して" 2>&1
opencode run -m opencode/kimi-k2.5-free "コードレビューして" 2>&1
```

#### パターンB: 有料モデル利用（認証あり）

OpenAI Plus/Proサブスクの `openai/*` モデルや、`zai-coding-plan/*` モデルを使う場合。

```bash
# OpenAI モデル（OAuth認証）
opencode run -m openai/gpt-5.3-codex "リファクタして" 2>&1

# zai-coding-plan モデル（APIキー認証）
opencode run -m zai-coding-plan/glm-4.7 "コードを分析して" 2>&1
```

### プロバイダ認証の仕組み

```
opencode auth login
  → 各プロバイダに応じた認証フロー
  → ~/.local/share/opencode/auth.json に保存（マルチプロバイダ対応）
    {
      "openai": {
        "type": "oauth",
        "refresh": "rt_...",    ← リフレッシュトークン（長期有効）
        "access": "eyJ...",     ← アクセストークン（10日間有効）
        "expires": 1771209089613,
        "accountId": "..."
      },
      "zai-coding-plan": {
        "type": "api",
        "key": "sk-..."         ← APIキー（無期限）
      }
    }
```

- **openai**: `access` トークンは10日間有効。`refresh` トークンで自動更新される
- **zai-coding-plan**: APIキーは無期限（プロバイダ側で無効化されない限り）
- **auth.json をリモートに復元すれば全プロバイダの認証が引き継がれる**

### セットアップ手順

#### Step 1: ローカルで auth.json をbase64エンコード（パターンBのみ）

```bash
cat ~/.local/share/opencode/auth.json | base64 | pbcopy
```

#### Step 2: Claude Code のシークレットに登録（パターンBのみ）

Claude Code Web のプロジェクト設定 or `claude --remote` の環境変数として:

```
OPENCODE_AUTH_JSON=<Step 1でコピーしたbase64文字列>
```

設定場所の選択肢:
- **claude.ai のプロジェクト設定** → Environment Variables
- **`~/.claude/.env`** → ローカルの環境変数ファイル（リモートに引き継がれる場合）

#### Step 3: SessionStartフックで自動セットアップ

`.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-claude-remote.sh"
      }]
    }]
  }
}
```

#### スクリプトの動作（setup-claude-remote.sh）

リモート環境（`CLAUDE_CODE_REMOTE=true`）でのみ実行:

```
[起動時]
claude --remote "タスク"
  → SessionStart フック発火
    → setup-claude-remote.sh
      → opencode インストール
      → OPENCODE_AUTH_JSON あれば auth.json 復元（パターンB）
      → なければインストールのみ（パターンA）
  → opencode run が利用可能に
```

### セキュリティ上の注意（パターンB）

| リスク | 対策 |
|--------|------|
| refresh token の漏洩 | シークレットとして管理、リポジトリにコミットしない |
| access token の期限切れ | opencode が refresh token で自動更新（10日周期） |
| auth.json のパーミッション | スクリプト内で `chmod 600` を設定 |
| リモート環境の永続性 | セッション毎にフックで再セットアップされるため問題なし |

### 認証情報の更新（パターンB）

プロバイダ側でトークンが無効化された場合や、新しいプロバイダを追加した場合:

```bash
# ローカルで再ログイン（または新プロバイダを追加）
opencode auth login

# auth.json全体を再エンコード（全プロバイダの情報を含む）
cat ~/.local/share/opencode/auth.json | base64 | pbcopy

# シークレット OPENCODE_AUTH_JSON を更新
```

**注意**: プロバイダを追加・変更した場合は必ず再エンコードしてシークレットを更新すること。auth.json には全プロバイダの認証情報が含まれるため、部分的な更新はできない。

### 動作確認

```bash
# インストール確認
opencode -v

# パターンA: 無料モデルで実行テスト
opencode run -m opencode/gpt-5-nano "Hello, respond with OK" 2>&1

# パターンB: 認証確認 + 有料モデルで実行テスト
opencode auth list
opencode run -m openai/gpt-5.2 "Hello, respond with OK" 2>&1
opencode run -m zai-coding-plan/glm-4.7 "Hello, respond with OK" 2>&1
```
