# セットアップガイド

## 概要

このリポジトリは、複数のプロジェクト間で共有するClaude Code設定を提供します。シンボリックリンクを使用することで、共通設定の更新が全プロジェクトに即座に反映されます。

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
# シンボリックリンクを確認
ls -la .claude/rules/
ls -la .claude/skills/
ls -la .claude/hooks/

# リンク先を確認
readlink .claude/rules/languages
# 出力例: /Users/yourname/.claude-shared/.claude/rules/languages
```

### 4. .gitignoreの設定

**重要**: `.claude/`全体を除外してはいけません。プロジェクト固有の設定がgit管理できなくなります。

以下の内容を`.gitignore`に追加してください：

```gitignore
# Claude Code - shared configuration (symlinks only)
.claude/rules/languages
.claude/rules/workflow
.claude/skills/dev
.claude/skills/meta-skill-creator
.claude/skills/agent-browser
.claude/commands/dev
.claude/hooks/dev

# Claude Code - local settings only
.claude/settings.local.json
```

**除外されるもの**:

- 共有設定へのシンボリックリンク（各自が`setup-claude.sh`で作成）
- ローカル設定ファイル（個人の環境設定）

**git管理されるもの**:

- `.claude/rules/project/` - プロジェクト固有のルール（チーム共有）
- `.claude/skills/custom/` - プロジェクト固有のスキル（チーム共有）
- `.claude/commands/custom/` - プロジェクト固有のコマンド（チーム共有）
- `.claude/hooks/project/` - プロジェクト固有のフック（チーム共有）
- `.claude/settings.json` - プロジェクトのフック設定等（チーム共有）

## プロジェクト固有の設定

プロジェクト固有の設定が必要な場合、手動で作成します：

```bash
# プロジェクト固有のルール
mkdir -p .claude/rules/project
cat > .claude/rules/project/api-conventions.md << 'EOF'
# API Conventions

## エンドポイント命名
- RESTful: /api/v1/users/:id
- GraphQL: /graphql

## エラーハンドリング
...
EOF

# プロジェクト固有のスキル
mkdir -p .claude/skills/custom

# プロジェクト固有のフック
mkdir -p .claude/hooks/project

# コマンド（スキルのショートカット）
mkdir -p .claude/commands

# ローカル設定
cat > .claude/settings.local.json << 'EOF'
{
  "model": "sonnet",
  "autoApprove": ["read", "glob", "grep"]
}
EOF
```

## WSL環境でのセットアップ

WSL2ではLinuxのシンボリックリンクが問題なく動作します：

```bash
# WSL内で実行
git clone <this-repo-url> ~/.dot-claude-dev
cd /path/to/your-project
bash ~/.dot-claude-dev/setup-claude.sh
```

### 注意事項

- **推奨**: WSLファイルシステム内（`~/.dot-claude-dev`）に配置
- **可能**: Windowsファイルシステム（`/mnt/c/...`）上でも動作しますが、パフォーマンスに注意

## 更新

### 共通設定の更新

```bash
cd ~/.dot-claude-dev
git pull
# すべてのプロジェクトに自動的に反映される
```

### 個別プロジェクトの再リンク（壊れた場合）

```bash
cd /path/to/your-project
rm -rf .claude/rules/languages .claude/rules/workflow
rm -rf .claude/skills/dev .claude/skills/meta-skill-creator
rm -rf .claude/hooks/dev
bash ~/.dot-claude-dev/setup-claude.sh
```

## リモート環境（Claude Code on the Web）での利用

ウェブ上のClaude Codeではリポジトリがクリーンな状態でクローンされるため、`~/.dot-claude-dev/` が存在せずシンボリックリンクが壊れます。SessionStartフックで自動的にクローン＆リンクを行うことで解決します。

### セットアップ手順

#### 1. スクリプトをプロジェクトにコピー

```bash
cp ~/.dot-claude-dev/scripts/setup-claude-remote.sh /path/to/your-project/scripts/
```

必要に応じて `SHARED_REPO` のURLを変更してください。

#### 2. SessionStartフックを登録

プロジェクトの `.claude/settings.json` に追加:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-claude-remote.sh"
          }
        ]
      }
    ]
  }
}
```

#### 3. 動作確認

Claude Code on the Web でセッションを開始し、以下を確認:

```bash
ls -la ~/.dot-claude-dev/          # クローンされている
ls -la .claude/rules/languages     # シンボリックリンクが張られている
```

### 仕組み

- 環境変数 `CLAUDE_CODE_REMOTE=true` でリモート環境を判別（ローカルではスキップ）
- `git clone --depth 1` で共有リポジトリを `~/.dot-claude-dev/` にクローン
- 既存の `setup-claude.sh` を実行してシンボリックリンクを作成

### 注意事項

- 共有リポジトリがプライベートの場合、Claude GitHub Appのアクセス権が必要
- リモート環境は毎セッション使い捨てのため、クローンは毎回実行される
- クローン失敗時はエラーにせず継続する（共有設定なしでも動作可能）

## ベストプラクティス

### 共通設定の変更

1. `~/.dot-claude-dev` で変更を加える
2. テストプロジェクトで動作確認
3. コミット＆プッシュ
4. 他のマシンで `git pull`

### プロジェクト固有設定の管理

- `.claude/settings.local.json`: `.gitignore` に追加（ローカルのみ）
- `.claude/settings.json`: プロジェクトにコミット（フック設定等）
- `.claude/rules/project/`: プロジェクトにコミット（チーム共有）
- `.claude/skills/custom/`: プロジェクトにコミット（チーム共有）
- `.claude/hooks/project/`: プロジェクトにコミット（チーム共有）

### チーム開発

各メンバーが以下を実行：

```bash
# 1. 共有リポジトリをクローン
git clone <shared-repo> ~/.dot-claude-dev

# 2. プロジェクトで適用
cd /path/to/team-project
bash ~/.dot-claude-dev/setup-claude.sh
```

これにより、チーム全体で統一されたルールとワークフローを使用できます。
