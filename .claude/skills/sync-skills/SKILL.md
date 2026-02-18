---
description: "グローバルスキル一覧を参照している外部プロジェクトの CLAUDE.md を最新状態に同期"
---

# dev:sync-skills

グローバルスキルの追加・削除・リネーム時に、参照先プロジェクトの CLAUDE.md を一括更新する。

## Step 0: 用途の確認

AskUserQuestion で同期モードを確認する。

- **既存プロジェクトの同期**: 参照先プロジェクトの CLAUDE.md を最新スキル一覧に更新 → Step 1 へ
- **新規プロジェクトへの追加**: 既存プロジェクトの CLAUDE.md を参考に、新規プロジェクトの CLAUDE.md を作成または編集 → Step 1 で一覧取得後、既存プロジェクトの CLAUDE.md を Read してテンプレートとして利用。対象プロジェクトのパスを聞き、Step 5 で直接作成・編集する

## Step 1: 現在のスキル一覧を取得

`~/dot-claude-dev/.claude/skills/dev/` 配下のディレクトリを走査し、現在のグローバルスキル一覧を構築する。

```bash
ls -d ~/dot-claude-dev/.claude/skills/dev/*/
```

各スキルの SKILL.md から description を取得して一覧を作る。

## Step 2: 同期対象プロジェクトを収集

### 2-1: 本家 CLAUDE.md（必須）

`dot-claude-dev/CLAUDE.md` を同期対象に含める。Step 1 の最新スキル一覧と比較し、不足があれば追加対象とする。

### 2-2: 外部プロジェクト

`dot-claude-dev` のスキルを参照している CLAUDE.md を検索する。

```bash
grep -rl "dot-claude-dev" ~/*/CLAUDE.md ~//*/*/CLAUDE.md 2>/dev/null | grep -v dot-claude-dev
```

## Step 3: 各プロジェクトを pull

差分確認の前に、各プロジェクトで `git pull` を実行してローカルを最新化する。
リモートで既に更新済みの場合、不要な差分を検出せずに済む。

```bash
# 各プロジェクトで並列実行
cd {project_path} && git pull
```

## Step 4: 差分確認

各プロジェクトの CLAUDE.md を Read し、現在のグローバルスキル参照テーブルと Step 1 の最新一覧を比較する。

差分を一覧で表示（**本家を先頭に表示**）:

```
## 同期対象

| プロジェクト | 追加 | 削除 | リネーム |
|---|---|---|---|
| dot-claude-dev（本家） | dev:new-skill | - | - |
| meurai-editer | dev:new-skill | - | - |
| base-ui-design | dev:new-skill | - | - |
```

**AskUserQuestion で同期実行の確認を取る。**

## Step 5: CLAUDE.md 更新

各プロジェクトの CLAUDE.md のグローバルスキルテーブルを Edit で更新する。

更新対象はスキル参照テーブル（`| **dev:xxx** | ... |` 行）のみ。
プロジェクト固有の記述（実行ルール、固有スキル等）は一切変更しない。

## Step 6: コミット＆プッシュ

各プロジェクトで simple-add サブエージェントを並列実行してコミット＆プッシュする。

```
Task({
  prompt: "プロジェクト: {path}\n変更: CLAUDE.md グローバルスキル一覧を同期\n手順: git add CLAUDE.md && commit && push",
  description: "Commit+push {project_name}",
  subagent_type: "simple-add",
  model: "haiku"
})
```

## Step 7: 結果報告

```
## 同期結果

| プロジェクト | コミット | ブランチ | 状態 |
|---|---|---|---|
| meurai-editer | abc1234 | develop | OK |
```
