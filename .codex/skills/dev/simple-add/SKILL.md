---
name: dev:simple-add
description: |
  Git commit automation for Codex. Use when the user asks for simple-add,
  a lightweight commit, or committing the current work with an optional push.

  Trigger:
  simple-add, simple commit, 軽量コミット, 変更をコミット, コミットして, -p で push
user-invocable: true
---

# simple-add

現在の変更を、最小限の確認でステージング、コミット、必要に応じた push まで実行する。

## オプション

ユーザー指定または引数に `-p` が含まれる場合は、コミット後に `git push` も実行する。

## 基本方針

- 既知の作業文脈がある場合は、`git status --short` と必要最小限の差分確認だけで進める。
- 詳細な `git diff`、`git log`、長い分析は標準手順に含めない。
- ユーザーが対象ファイルを指定していない場合は、作業文脈が不足していても現在の変更をまとめてコミット対象にする。
- 新規セッションやコンテキスト圧縮後で対象ファイルを特定できない場合も、`git add -A` で全変更をステージしてよい。
- 追加確認するのは、生成物や秘密情報、意図しない削除など危険な差分の疑いがある場合だけにする。
- 完了報告はコミット結果と必要な確認結果だけに留める。

## 実行フロー

### Step 1: 状態確認

まず以下でコミット対象の有無と範囲だけを確認する。

```bash
git status --short
git diff --stat
```

ここで得たファイル一覧と作業文脈からコミットメッセージを作る。作業文脈が不足している場合は、`git diff --stat` の範囲から要約する。

以下の場合だけ、必要な範囲で `git diff` や `git log --oneline -3` を確認する。

- コミットメッセージを作る根拠が不足している。
- 大きな生成物、秘密情報、意図しない削除の疑いがある。

### Step 2: ステージング

ユーザーが対象ファイルを指定していない場合は、現在の変更をまとめてステージする。

```bash
git add -A
```

ユーザーが対象ファイルを明示した場合だけ、指定範囲に絞ってステージする。

```bash
git add -- <pathspec...>
```

ステージ後に `git status --short` と `git diff --cached --stat` を確認し、意図しない大きな生成物や秘密情報が含まれていないか確認する。疑わしい場合はコミット前に止めてユーザーに確認する。

```bash
git status --short
git diff --cached --stat
```

必要に応じて `git diff --cached` でステージ済み差分だけを確認する。

### Step 3: コミット

変更内容に合う type と emoji を選び、日本語の要約でコミットする。変更が小さい場合は本文を 1〜2 行に留める。内容が十分に明らかな場合は長い箇条書きにしない。

```bash
git commit -m "$(cat <<'EOF'
<emoji> <type>: <description(日本語)>

- [変更点1]
- [変更点2]

Co-Authored-By: OpenAI <noreply@openai.com>
EOF
)"
```

既存リポジトリにコミットメッセージ規約がある場合は、その規約を優先する。

### Step 4: Push

`-p` 指定時のみ実行する。

```bash
git push
```

### Step 5: 完了確認

```bash
git status
```

push した場合は push の成功も確認する。

## コミットメッセージ形式

```text
<emoji> <type>: <description>

[- 変更点]

Co-Authored-By: OpenAI <noreply@openai.com>
```

本文は任意。単純な変更で件名だけで十分な場合は、件名と `Co-Authored-By` だけでよい。

## Type と Emoji

| Type       | Emoji | 説明                   |
| ---------- | ----- | ---------------------- |
| `feat`     | ✨    | 新機能                 |
| `fix`      | 🐛    | バグ修正               |
| `docs`     | 📝    | ドキュメント           |
| `style`    | 💄    | フォーマット・スタイル |
| `refactor` | ♻️    | リファクタリング       |
| `perf`     | ⚡️    | パフォーマンス改善     |
| `test`     | ✅    | テスト                 |
| `chore`    | 🔧    | ツール・設定           |
| `ci`       | 🚀    | CI/CD 改善             |

## 注意

- ユーザーが明示した範囲外の変更は勝手に戻さない。
- ユーザーが対象ファイルを指定していない場合は、作業文脈が不足していても全変更をコミット対象にする。
- 秘密情報や大きな生成物など危険な差分が見える場合はコミット前に止める。
- push は `-p` 指定または明示指示がある場合だけ行う。
- 文脈から分かる変更をコミットする時は、調査ログのような長いシンキングを挟まない。
