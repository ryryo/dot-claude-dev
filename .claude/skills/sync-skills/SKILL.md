---
description: "グローバルスキル一覧を参照している外部プロジェクトの CLAUDE.md を最新状態に同期"
---

# dev:sync-skills

グローバルスキルの追加・削除・リネーム時に、参照先プロジェクトの CLAUDE.md を一括更新する。

## Step 1: 現在のスキル一覧を取得

`~/dot-claude-dev/.claude/skills/dev/` 配下のディレクトリを走査し、現在のグローバルスキル一覧を構築する。

```bash
ls -d ~/dot-claude-dev/.claude/skills/dev/*/
```

各スキルの SKILL.md から description を取得して一覧を作る。

## Step 2: 参照先プロジェクトを検索

`dot-claude-dev` のスキルを参照している CLAUDE.md を検索する。

```bash
grep -rl "dot-claude-dev" ~/*/CLAUDE.md ~//*/*/CLAUDE.md 2>/dev/null | grep -v dot-claude-dev
```

## Step 3: 差分確認

各プロジェクトの CLAUDE.md を Read し、現在のグローバルスキル参照テーブルと Step 1 の最新一覧を比較する。

差分を一覧で表示:

```
## 同期対象

| プロジェクト | 追加 | 削除 | リネーム |
|---|---|---|---|
| meurai-editer | dev:team-run | - | - |
| base-ui-design | dev:team-run | - | - |
```

**AskUserQuestion で同期実行の確認を取る。**

## Step 4: CLAUDE.md 更新

各プロジェクトの CLAUDE.md のグローバルスキルテーブルを Edit で更新する。

更新対象はスキル参照テーブル（`| **dev:xxx** | ... |` 行）のみ。
プロジェクト固有の記述（実行ルール、固有スキル等）は一切変更しない。

## Step 5: コミット＆プッシュ

各プロジェクトで simple-add サブエージェントを並列実行してコミット＆プッシュする。

```
Task({
  prompt: "プロジェクト: {path}\n変更: CLAUDE.md グローバルスキル一覧を同期\n手順: git add CLAUDE.md && commit && push",
  description: "Commit+push {project_name}",
  subagent_type: "simple-add",
  model: "haiku"
})
```

## Step 6: 結果報告

```
## 同期結果

| プロジェクト | コミット | ブランチ | 状態 |
|---|---|---|---|
| meurai-editer | abc1234 | develop | OK |
```
