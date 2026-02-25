---
name: setup-project
description: "指定プロジェクトに dot-claude-dev の共通設定をセットアップする"
allowed-tools: Bash, Read, Edit, Write, AskUserQuestion
---

# setup-project

指定したプロジェクトに対して、setup-guide.md の手順に従い Claude Code 共通設定をセットアップする。

## トリガー

`/setup-project` または「セットアップ」「プロジェクトにセットアップ」「setup-project」

## Step 0: プロジェクトパスの確認

スキル起動時の引数にパスが含まれていればそれを使う（例: `/setup-project ~/my-project`）。

パスが指定されていない場合のみ、AskUserQuestion で確認する:

```
「どのプロジェクトにセットアップしますか？（絶対パスまたは ~/... 形式で入力）」
```

パスが `~` で始まる場合は `$HOME` に展開して使う。

## Step 1: 事前確認

```bash
# プロジェクトディレクトリの存在確認
ls "{PROJECT_PATH}"

# 現在のリンク状態を確認
bash "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/scripts/check-claude-setup.sh" "{PROJECT_PATH}"
```

- **終了コード 0（全リンク正常）** → セットアップ済みである旨を伝え、再実行するか AskUserQuestion で確認
- **終了コード 1（未リンク・別パスあり）** → Step 2 へ進む

## Step 2: setup-claude.sh 実行

```bash
cd "{PROJECT_PATH}" && bash "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/setup-claude.sh"
```

実行後、リンクが正しく作成されたか再確認:

```bash
bash "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/scripts/check-claude-setup.sh" "{PROJECT_PATH}"
```

終了コードが 1 の場合はエラー内容をユーザーに報告して停止する。

## Step 3: リモートセットアップスクリプトのコピー

```bash
mkdir -p "{PROJECT_PATH}/scripts"
cp "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/.claude/skills/setup-project/scripts/setup-claude-remote.sh" "{PROJECT_PATH}/scripts/"
cp "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/scripts/setup-opencode.sh" "{PROJECT_PATH}/scripts/"
```

## Step 4: .gitignore の更新

```bash
bash "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/.claude/skills/setup-project/scripts/update-gitignore.sh" "{PROJECT_PATH}"
```

## Step 5: settings.json の作成

```bash
bash "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/.claude/skills/setup-project/scripts/create-settings-json.sh" "{PROJECT_PATH}"
```

既存の `settings.json` がある場合はスクリプトがスキップし、手動確認が必要な旨を出力する。

## Step 6: 結果サマリー表示

```
## セットアップ完了: {PROJECT_PATH}

| 項目 | 状態 |
|------|------|
| シンボリックリンク（setup-claude.sh） | ✓ |
| scripts/setup-claude-remote.sh | ✓ |
| scripts/setup-opencode.sh | ✓ |
| .gitignore 更新 | ✓ |
| .claude/settings.json | ✓ 新規作成 / ⚠️ 既存（要確認） |
```
