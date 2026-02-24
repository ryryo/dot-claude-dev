---
description: "指定プロジェクトに dot-claude-dev の共通設定をセットアップする"
---

# setup-project

指定したプロジェクトに対して、setup-guide.md の手順に従い Claude Code 共通設定をセットアップする。

## トリガー

`/setup-project` または「セットアップ」「プロジェクトにセットアップ」「setup-project」

## Step 0: プロジェクトパスの確認

AskUserQuestion でセットアップ対象のプロジェクトパスを確認する。

```
「どのプロジェクトにセットアップしますか？（絶対パスまたは ~/... 形式で入力）」
```

パスが `~` で始まる場合は `$HOME` に展開して使う。

## Step 1: 事前確認

```bash
# プロジェクトディレクトリの存在確認
ls "{PROJECT_PATH}"

# 既存の .claude/ ディレクトリ確認
ls -la "{PROJECT_PATH}/.claude/" 2>/dev/null || echo "(未作成)"

# dot-claude-dev の場所確認
echo "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}"
```

既存リンクがある場合は現状を表示し、上書きしてよいか AskUserQuestion で確認する。

## Step 2: setup-claude.sh 実行

```bash
cd "{PROJECT_PATH}" && bash "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/setup-claude.sh"
```

成功を確認:

```bash
ls -la "{PROJECT_PATH}/.claude/rules/"
ls -la "{PROJECT_PATH}/.claude/skills/"
ls -la "{PROJECT_PATH}/.claude/commands/"
ls -la "{PROJECT_PATH}/.claude/hooks/"
```

## Step 3: setup-claude-remote.sh のコピー

```bash
mkdir -p "{PROJECT_PATH}/scripts"
cp "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/scripts/setup-claude-remote.sh" "{PROJECT_PATH}/scripts/"
```

## Step 4: .gitignore の更新

`{PROJECT_PATH}/.gitignore` を Read し、以下のエントリが不足していれば追記する。

追加するエントリ:

```gitignore
# Claude Code - shared configuration (symlinks)
.claude/rules/workflow
.claude/skills/dev
.claude/commands/dev
.claude/hooks/dev

# Claude Code - local settings
.claude/settings.local.json
```

**注意**: `.claude/` 全体を除外しないこと。プロジェクト固有設定が git 管理できなくなる。

## Step 5: settings.json の作成

`{PROJECT_PATH}/.claude/settings.json` が存在しない場合のみ作成する。

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

既存の `settings.json` がある場合は、フック設定が不足していれば追記が必要な旨をユーザーに通知するのみ（自動変更しない）。

## Step 6: 結果サマリー表示

```
## セットアップ完了: {PROJECT_PATH}

| 項目 | 状態 |
|------|------|
| シンボリックリンク（setup-claude.sh） | ✓ |
| scripts/setup-claude-remote.sh | ✓ |
| .gitignore 更新 | ✓ |
| .claude/settings.json | ✓ 新規作成 / ⚠️ 既存（要確認） |

### 次のステップ
- チーム開発の場合: 他メンバーも同手順を実行
- 更新時: `cd ~/dot-claude-dev && git pull`
- リンク修復時: 本スキルを再実行
```
