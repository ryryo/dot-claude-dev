---
description: "外部プロジェクトの setup-claude-remote.sh の共有セクションを最新テンプレートに同期"
---

# sync-setup-remote

外部プロジェクトにコピーされた `scripts/setup-claude-remote.sh` の共有管理セクションを、
dot-claude-dev の最新テンプレートに同期する。プロジェクト固有のカスタマイズは保持する。

## マーカー仕様

```
SHARED_REPO="..."                          ← プロジェクト固有（保持）
SHARED_DIR="..."                           ← プロジェクト固有（保持）

# === DOT-CLAUDE-DEV MANAGED BEGIN ===
... 共有セクション ...                      ← テンプレートから置換
# === DOT-CLAUDE-DEV MANAGED END ===

# --- プロジェクト固有セットアップ ---
...                                        ← プロジェクト固有（保持）
```

## Step 0: テンプレート読み込み

dot-claude-dev の最新テンプレートを Read で読み込む。

```
Read: dot-claude-dev/.claude/skills/setup-project/scripts/setup-claude-remote.sh
```

`# === DOT-CLAUDE-DEV MANAGED BEGIN ===` から `# === DOT-CLAUDE-DEV MANAGED END ===` までを
**テンプレート共有セクション**として抽出・保持する。

## Step 1: 同期対象プロジェクトを収集

`setup-claude-remote.sh` を持つ外部プロジェクトを検索する。

```bash
find ~/*/scripts ~//*/*/scripts -name "setup-claude-remote.sh" -not -path "*/dot-claude-dev/*" 2>/dev/null
```

見つからない場合は AskUserQuestion でパスを確認する。

## Step 2: 各プロジェクトを pull

差分確認の前に最新化する。

```bash
cd {project_path} && git pull
```

## Step 3: 差分確認

各プロジェクトの `setup-claude-remote.sh` を Read し、以下を分析:

1. **マーカーの有無**: `DOT-CLAUDE-DEV MANAGED BEGIN/END` が存在するか
2. **共有セクションの差分**: テンプレートと比較して差分があるか
3. **プロジェクト固有部分**: マーカー外の内容を確認

結果を一覧表示:

```
## 同期対象

| プロジェクト | マーカー | 共有セクション | 固有セクション |
|---|---|---|---|
| project-a | あり | 差分あり | npm install, docker |
| project-b | なし（初回） | 全体が旧形式 | なし |
```

**AskUserQuestion で同期実行の確認を取る。**

## Step 4: 同期実行

### マーカーありの場合（通常）

Edit で `MANAGED BEGIN` から `MANAGED END` までをテンプレートの共有セクションで置換する。
前後のプロジェクト固有部分はそのまま保持。

### マーカーなしの場合（初回マイグレーション）

旧形式のスクリプトにマーカーを導入する。

1. Read で既存スクリプトの全内容を確認
2. ヘッダー部分（`SHARED_REPO`, `SHARED_DIR`）を特定・保持
3. `exit 0` の直前にあるプロジェクト固有コードを特定・保持
4. テンプレートをベースに、保持した部分を組み込んで Write

**注意**: 初回マイグレーションでは必ず diff を表示してユーザー確認を取ること。

## Step 5: コミット & プッシュ

各プロジェクトで simple-add サブエージェントを並列実行。

```
Task({
  prompt: "プロジェクト: {path}\n変更: setup-claude-remote.sh の共有セクションを同期\n手順: git add scripts/setup-claude-remote.sh && commit && push",
  description: "Commit+push {project_name}",
  subagent_type: "Bash",
  model: "haiku"
})
```

## Step 6: 結果報告

```
## 同期結果

| プロジェクト | 状態 | 備考 |
|---|---|---|
| project-a | OK | 共有セクション更新 |
| project-b | OK | マーカー導入（初回） |
```
