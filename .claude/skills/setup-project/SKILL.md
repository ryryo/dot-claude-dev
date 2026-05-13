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
bash "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/.claude/skills/setup-project/scripts/check-claude-setup.sh" "{PROJECT_PATH}"
```

出力の `セットアップ種別` を見て、以降の見出しを選ぶ。

- **新規** → 「新規セットアップ」へ進む。
- **更新（既存セットアップ正常・再適用可能）** → 「既存セットアップ更新」へ進む。
- **更新/修復（不足または別パスあり）** → 「既存セットアップ更新」へ進む。再リンクで修復する。

## 新規セットアップ

初回セットアップでは Step 2 から Step 7 まで順に実行する。

## 既存セットアップ更新

既存プロジェクトの更新では Step 2 を必ず実行する。`setup-claude.sh` は idempotent なので、既存リンクを維持しつつ不足分だけ反映する。

Step 3 以降は必要に応じて確認として実行する。ただし `scripts/setup-claude-remote.sh` / `scripts/setup-local.sh` を上書きしたくない場合は Step 3 をスキップする。

## Step 2: setup-claude.sh 実行（新規・更新共通）

```bash
cd "{PROJECT_PATH}" && bash "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/scripts/setup-claude.sh"
```

`setup-claude.sh` は `.claude/{rules/workflow, skills/dev, commands/dev, hooks/dev}` と `.codex/{skills/dev, hooks/dev}` にシンボリックリンクを作成し、`.gitignore` と Codex hooks 設定も差分反映する。

実行後、リンクが正しく作成されたか再確認:

```bash
bash "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/.claude/skills/setup-project/scripts/check-claude-setup.sh" "{PROJECT_PATH}"
```

終了コードが 1 の場合はエラー内容をユーザーに報告して停止する。

## Step 3: リモートセットアップスクリプトのコピー

```bash
mkdir -p "{PROJECT_PATH}/scripts"
TEMPLATE_DIR="${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/.claude/skills/setup-project/scripts"
cp "$TEMPLATE_DIR/setup-claude-remote.sh" "{PROJECT_PATH}/scripts/"
cp "$TEMPLATE_DIR/setup-local.sh" "{PROJECT_PATH}/scripts/"
```

## Step 4: .gitignore の確認

```bash
bash "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/.claude/skills/setup-project/scripts/update-gitignore.sh" "{PROJECT_PATH}"
```

`setup-claude.sh` 内でも実行される。ここでは再確認として idempotent に実行する。

## Step 5: Codex hooks 設定の確認

```bash
bash "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/.claude/skills/setup-project/scripts/create-codex-hooks.sh" "{PROJECT_PATH}"
```

`setup-claude.sh` 内でも実行される。ここでは再確認として idempotent に実行する。

既存の `.codex/hooks.json` がある場合はスクリプトが上書きせず、手動確認が必要な旨を出力する。

## Step 6: settings.json の作成

```bash
bash "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/.claude/skills/setup-project/scripts/create-settings-json.sh" "{PROJECT_PATH}"
```

既存の `settings.json` がある場合はスクリプトがスキップし、手動確認が必要な旨を出力する。

## Step 7: 結果サマリー表示

```
## セットアップ完了: {PROJECT_PATH}

| 項目 | 状態 |
|------|------|
| .claude シンボリックリンク（rules/skills/commands/hooks） | ✓ |
| .codex シンボリックリンク（skills/hooks） | ✓ |
| scripts/setup-claude-remote.sh | ✓ |
| scripts/setup-local.sh | ✓ |
| .gitignore 更新 | ✓ |
| .claude/settings.json | ✓ 新規作成 / ⚠️ 既存（要確認） |
| .codex/config.toml / hooks.json | ✓ 新規作成・更新 / ⚠️ 既存（要確認） |
```
