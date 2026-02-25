# 使用例

## 基本的な使い方

### 新規プロジェクトへの適用

```bash
# 1. 新規プロジェクト作成
mkdir my-new-project
cd my-new-project
git init

# 2. Claude設定をリンク
bash ~/.claude-shared/scripts/setup-claude.sh

# 3. プロジェクトのCLAUDE.mdを作成（任意）
cat > CLAUDE.md << 'EOF'
# プロジェクト固有の指示

このプロジェクトは...

## 技術スタック
- TypeScript + React
- Vite
- Vitest

## 開発フロー
- `/dev:story` でタスク生成
- `dev:developing` で実装
- `/dev:feedback` で振り返り
EOF

# 4. Claude Codeで開く
claude-code .
```

### 既存プロジェクトへの適用

```bash
cd /path/to/existing-project

# 既存の.claudeディレクトリをバックアップ（念のため）
mv .claude .claude.backup

# 共通設定をリンク
bash ~/.claude-shared/scripts/setup-claude.sh

# プロジェクト固有の設定を復元（必要に応じて）
cp .claude.backup/settings.local.json .claude/
cp -r .claude.backup/hooks .claude/
```

## プロジェクト固有設定の追加例

### 例1: APIルールを追加

```bash
mkdir -p .claude/rules/project

cat > .claude/rules/project/api.md << 'EOF'
# API規約

## エンドポイント命名
- RESTful: `/api/v1/resources/:id`
- 複数形を使用

## レスポンス形式
```json
{
  "data": { ... },
  "meta": { "total": 100 },
  "errors": []
}
```

## 認証
- Bearer Token: `Authorization: Bearer <token>`
EOF
```

### 例2: プロジェクト固有コマンドを追加

```bash
mkdir -p .claude/commands/project

cat > .claude/commands/project/deploy.md << 'EOF'
---
description: "本番環境へのデプロイ"
---

# /project:deploy

本番環境にデプロイします。

## 手順
1. テストを実行
2. ビルド
3. デプロイスクリプト実行
EOF
```

### 例3: ローカル設定

```bash
cat > .claude/settings.local.json << 'EOF'
{
  "model": "sonnet",
  "autoApprove": ["read", "glob", "grep"],
  "diffStrategy": "unified"
}
EOF
```

## マルチプロジェクト管理

### プロジェクト1: React SPA

```bash
cd ~/projects/react-app
bash ~/.claude-shared/scripts/setup-claude.sh

# プロジェクト固有
mkdir -p .claude/rules/project
echo "# Reactプロジェクト特有のルール" > .claude/rules/project/react-conventions.md
```

### プロジェクト2: Laravel API

```bash
cd ~/projects/laravel-api
bash ~/.claude-shared/scripts/setup-claude.sh

# プロジェクト固有
mkdir -p .claude/rules/project
echo "# Laravel特有のルール" > .claude/rules/project/laravel-conventions.md
```

### 共通設定の更新

```bash
cd ~/.claude-shared
git pull

# 両方のプロジェクトに即座に反映される
```

## WSL環境での例

### WSL2でのセットアップ

```bash
# WSL内で実行
cd ~
git clone https://github.com/yourname/dot-claude-dev.git .claude-shared

# Windowsプロジェクトでも使える
cd /mnt/c/Users/yourname/projects/my-project
bash ~/.claude-shared/scripts/setup-claude.sh
```

### Windows側で確認

```powershell
# PowerShell（WSLからリンクされたプロジェクト）
cd C:\Users\yourname\projects\my-project
dir .claude
# シンボリックリンクが表示される
```

## チーム開発での例

### チームでの共通設定共有

```bash
# 1. チーム共通リポジトリをクローン
git clone https://github.com/your-team/claude-shared.git ~/.claude-shared

# 2. プロジェクトで適用
cd /path/to/team-project
bash ~/.claude-shared/scripts/setup-claude.sh

# 3. プロジェクト固有設定（各自）
cat > .claude/settings.local.json << 'EOF'
{
  "model": "sonnet"
}
EOF
```

### プロジェクトの.gitignore

```gitignore
# .gitignore
.claude/settings.local.json
.claude/hooks/
```

これにより：
- チーム共通: rules, skills, commands（シンボリックリンク）
- 個人設定: settings.local.json, hooks（gitignore）

## トラブルシューティング例

### リンク切れの修復

```bash
# リンクを確認
ls -la .claude/rules/
ls -la .claude/skills/

# 壊れたリンクを削除
find .claude -type l ! -exec test -e {} \; -delete

# 再リンク
bash ~/.claude-shared/scripts/setup-claude.sh
```

### 共有ディレクトリ移動

```bash
# 古い場所から新しい場所へ移動
mv ~/.claude-shared ~/repos/claude-shared

# 環境変数を設定
export CLAUDE_SHARED_DIR="$HOME/repos/claude-shared"
echo 'export CLAUDE_SHARED_DIR="$HOME/repos/claude-shared"' >> ~/.bashrc

# 全プロジェクトで再リンク
cd /path/to/project1
find .claude -type l -delete
bash "$CLAUDE_SHARED_DIR/scripts/setup-claude.sh"
```
