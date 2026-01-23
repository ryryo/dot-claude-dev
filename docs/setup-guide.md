# セットアップガイド

## 概要

このリポジトリは、複数のプロジェクト間で共有するClaude Code設定を提供します。シンボリックリンクを使用することで、共通設定の更新が全プロジェクトに即座に反映されます。

## ディレクトリ構造

### 共有リポジトリ（このリポジトリ）

```
~/.claude-shared/
├── .claude/
│   ├── rules/
│   │   ├── languages/     # 言語別コーディング規約（共通）
│   │   └── workflow/      # TDD/E2E/TASKワークフロー（共通）
│   ├── skills/
│   │   ├── dev/           # ストーリー駆動開発スキル（共通）
│   │   ├── meta-skill-creator/
│   │   └── agent-browser/
│   └── commands/
│       └── dev/           # /dev:story, /dev:developing 等（共通）
└── setup-claude.sh        # セットアップスクリプト
```

### 各プロジェクト（シンボリックリンク後）

```
your-project/.claude/
├── rules/
│   ├── languages -> ~/.claude-shared/.claude/rules/languages  # リンク
│   ├── workflow -> ~/.claude-shared/.claude/rules/workflow    # リンク
│   └── project/                                               # プロジェクト固有（任意）
├── skills/
│   ├── dev -> ~/.claude-shared/.claude/skills/dev             # リンク
│   ├── meta-skill-creator -> ...                              # リンク
│   └── custom/                                                # プロジェクト固有（任意）
├── commands/
│   ├── dev -> ~/.claude-shared/.claude/commands/dev           # リンク
│   └── custom/                                                # プロジェクト固有（任意）
├── settings.local.json                                        # プロジェクト固有
└── hooks/                                                     # プロジェクト固有
```

## インストール手順

### 1. 共有リポジトリのクローン

```bash
# デフォルトの場所（推奨）
git clone <this-repo-url> ~/.claude-shared

# または任意の場所（環境変数で指定）
export CLAUDE_SHARED_DIR="$HOME/repos/claude-shared"
git clone <this-repo-url> "$CLAUDE_SHARED_DIR"
```

### 2. プロジェクトへの適用

```bash
cd /path/to/your-project
bash ~/.claude-shared/setup-claude.sh
```

### 3. 確認

```bash
# シンボリックリンクを確認
ls -la .claude/rules/
ls -la .claude/skills/

# リンク先を確認
readlink .claude/rules/languages
# 出力例: /Users/yourname/.claude-shared/.claude/rules/languages
```

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
git clone <this-repo-url> ~/.claude-shared
cd /path/to/your-project
bash ~/.claude-shared/setup-claude.sh
```

### 注意事項

- **推奨**: WSLファイルシステム内（`~/.claude-shared`）に配置
- **可能**: Windowsファイルシステム（`/mnt/c/...`）上でも動作しますが、パフォーマンスに注意

## 更新

### 共通設定の更新

```bash
cd ~/.claude-shared
git pull
# すべてのプロジェクトに自動的に反映される
```

### 個別プロジェクトの再リンク（壊れた場合）

```bash
cd /path/to/your-project
rm -rf .claude/rules/languages .claude/rules/workflow
rm -rf .claude/skills/dev .claude/skills/meta-skill-creator
bash ~/.claude-shared/setup-claude.sh
```

## トラブルシューティング

### シンボリックリンクが機能しない

**症状**: Claude Codeがルールやスキルを認識しない

**原因**: リンク先のパスが間違っている

**解決策**:
```bash
readlink .claude/rules/languages
# 実際のパスを確認して、存在するか確認
ls -la ~/.claude-shared/.claude/rules/languages
```

### 環境変数で場所を指定したい

```bash
# .bashrc または .zshrc に追加
export CLAUDE_SHARED_DIR="$HOME/repos/claude-shared"

# セットアップ実行時に参照される
bash "$CLAUDE_SHARED_DIR/setup-claude.sh"
```

### プロジェクト固有の設定を誤ってコミットしてしまった

```bash
# .gitignoreに追加
echo ".claude/settings.local.json" >> .gitignore
echo ".claude/hooks/" >> .gitignore

# 履歴から削除
git rm --cached .claude/settings.local.json
git commit -m "chore: remove local settings from git"
```

## ベストプラクティス

### 共通設定の変更

1. `~/.claude-shared` で変更を加える
2. テストプロジェクトで動作確認
3. コミット＆プッシュ
4. 他のマシンで `git pull`

### プロジェクト固有設定の管理

- `.claude/settings.local.json`: `.gitignore` に追加（ローカルのみ）
- `.claude/rules/project/`: プロジェクトにコミット（チーム共有）
- `.claude/skills/custom/`: プロジェクトにコミット（チーム共有）

### チーム開発

各メンバーが以下を実行：

```bash
# 1. 共有リポジトリをクローン
git clone <shared-repo> ~/.claude-shared

# 2. プロジェクトで適用
cd /path/to/team-project
bash ~/.claude-shared/setup-claude.sh
```

これにより、チーム全体で統一されたルールとワークフローを使用できます。
