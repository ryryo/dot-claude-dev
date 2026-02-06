# セットアップガイド

## 概要

このリポジトリは、複数のプロジェクト間で共有するClaude Code設定を提供します。シンボリックリンクにより、共通設定の更新が全プロジェクトに即座に反映されます。

セットアップは3つに分かれます。

| 環境              | 内容                                         | 参照セクション           |
| ----------------- | -------------------------------------------- | ------------------------ |
| **ローカル**      | クローン、リンク作成、.gitignore設定         | 「インストール手順」     |
| **settings.json** | フック設定（コミット促進、コンパクト提案等） | 「settings.json設定」    |
| **リモート**      | SessionStartフックで自動セットアップ         | 「リモート環境での利用」 |

## ディレクトリ構造

### 共有リポジトリ（このリポジトリ）

```
~/.dot-claude-dev/
├── .claude/
│   ├── rules/
│   │   ├── languages/     # 言語別コーディング規約（共通）
│   │   └── workflow/      # TDD/E2E/TASKワークフロー（共通）
│   ├── skills/
│   │   ├── dev/           # ストーリー駆動開発スキル（共通）
│   │   ├── meta-skill-creator/
│   │   └── agent-browser/
│   ├── commands/
│   │   └── dev/           # /dev:story, /dev:developing 等（共通）
│   └── hooks/
│       └── dev/           # 共通フックスクリプト
│           ├── commit-check.sh
│           ├── memory-persistence/
│           └── strategic-compact/
└── setup-claude.sh        # セットアップスクリプト
```

### 各プロジェクト（シンボリックリンク後）

```
your-project/.claude/
├── rules/
│   ├── languages -> ~/.dot-claude-dev/.claude/rules/languages  # リンク
│   ├── workflow -> ~/.dot-claude-dev/.claude/rules/workflow    # リンク
│   └── project/                                               # プロジェクト固有（任意）
├── skills/
│   ├── dev -> ~/.dot-claude-dev/.claude/skills/dev             # リンク
│   ├── meta-skill-creator -> ...                              # リンク
│   └── custom/                                                # プロジェクト固有（任意）
├── commands/
│   ├── dev -> ~/.dot-claude-dev/.claude/commands/dev           # リンク
│   └── custom/                                                # プロジェクト固有（任意）
├── hooks/
│   ├── dev -> ~/.dot-claude-dev/.claude/hooks                  # リンク
│   └── project/                                               # プロジェクト固有（任意）
├── settings.json                                              # プロジェクト固有（フック設定等）
└── settings.local.json                                        # ローカル設定
```

## インストール手順

### 1. 共有リポジトリのクローン

```bash
# デフォルトの場所（推奨）
git clone <this-repo-url> ~/.dot-claude-dev

# または任意の場所（環境変数で指定）
export CLAUDE_SHARED_DIR="$HOME/repos/claude-shared"
git clone <this-repo-url> "$CLAUDE_SHARED_DIR"
```

### 2. プロジェクトへの適用

```bash
cd /path/to/your-project
bash ~/.dot-claude-dev/setup-claude.sh
```

### 3. 確認

```bash
ls -la .claude/rules/
ls -la .claude/skills/
readlink .claude/rules/languages
```

### 4. .gitignoreの設定

**重要**: `.claude/`全体を除外しないでください。プロジェクト固有の設定がgit管理できなくなります。

以下を`.gitignore`に追加します。

```gitignore
# Claude Code - shared configuration (symlinks)
.claude/rules/languages
.claude/rules/workflow
.claude/skills/dev
.claude/skills/meta-skill-creator
.claude/skills/agent-browser
.claude/commands/dev
.claude/hooks/dev

# Claude Code - local settings
.claude/settings.local.json
```

| 区分               | 対象                                                                                      | git管理  |
| ------------------ | ----------------------------------------------------------------------------------------- | -------- |
| シンボリックリンク | 共有設定（各自が`setup-claude.sh`で作成）                                                 | 除外     |
| ローカル設定       | `settings.local.json`                                                                     | 除外     |
| プロジェクト固有   | `rules/project/`, `skills/custom/`, `commands/custom/`, `hooks/project/`, `settings.json` | コミット |

## settings.json設定

シンボリックリンク作成後、`.claude/settings.json` にフック設定を追加します。

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-claude-remote.sh"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/dev/suggest-compact.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/dev/commit-check.sh"
          }
        ]
      }
    ]
  }
}
```

### フック一覧

| イベント         | スクリプト               | 説明                                               |
| ---------------- | ------------------------ | -------------------------------------------------- |
| **SessionStart** | `setup-claude-remote.sh` | リモート環境で共有リポジトリを自動クローン・リンク |
| **PreToolUse**   | `suggest-compact.sh`     | ツール呼び出し50回で `/compact` を提案             |
| **Stop**         | `commit-check.sh`        | 未コミット変更（10行以上）があればコミットを促す   |

## リモート環境（Claude Code on the Web）での利用

ウェブ上のClaude Codeではセッション毎にクリーンな環境が作られるため、`~/.dot-claude-dev/` が存在しません。settings.jsonのSessionStartフックで自動セットアップされます。

### 手順

1. セットアップスクリプトをプロジェクトにコピーし、必要に応じて `SHARED_REPO` のURLを変更する

   ```bash
   cp ~/.dot-claude-dev/scripts/setup-claude-remote.sh /path/to/your-project/scripts/
   ```

2. 「settings.json設定」セクションの設定を `.claude/settings.json` に適用する

### 補足

- スクリプトは `CLAUDE_CODE_REMOTE=true` のときだけ実行され、ローカルではスキップされる
- プライベートリポジトリの場合はClaude GitHub Appのアクセス権が必要
- gh利用時はサンドボックスの制約で `-R owner/repo` が必要な場合がある

## 更新

```bash
# 共通設定の更新（全プロジェクトに自動反映）
cd ~/.dot-claude-dev && git pull

# リンクが壊れた場合は再実行
cd /path/to/your-project && bash ~/.dot-claude-dev/setup-claude.sh
```

## チーム開発

各メンバーが「インストール手順」のステップ1〜4 + 「settings.json設定」を実行するだけで、チーム全体で統一されたルールとワークフローを使用できます。

共通設定を変更する場合は `~/.dot-claude-dev` で修正し、テストプロジェクトで確認してからプッシュしてください。
