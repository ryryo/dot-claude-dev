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

現在の作業内容を把握している Codex が、変更確認、ステージング、コミット、必要に応じた push までを軽量に実行する。

## オプション

ユーザー指定または引数に `-p` が含まれる場合は、コミット後に `git push` も実行する。

## 実行フロー

### Step 1: 状態確認

以下を確認して、コミット対象と直近の履歴を把握する。

```bash
git status
git diff --stat
git log --oneline -3
```

必要に応じて `git diff` を読み、コミットメッセージに反映する変更点を特定する。

### Step 2: ステージング

ユーザーが対象ファイルを指定していない場合は、現在の変更をまとめてステージする。

```bash
git add .
```

ステージ後に `git status --short` を確認し、意図しない大きな生成物や秘密情報が含まれていないか確認する。疑わしい場合はコミット前に止めてユーザーに確認する。

### Step 3: コミット

変更内容に合う type と emoji を選び、日本語の要約でコミットする。

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

- [変更点1]
- [変更点2]

Co-Authored-By: OpenAI <noreply@openai.com>
```

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
- コミット対象に不明な変更が混ざる場合は、コミット前にユーザーへ確認する。
- push は `-p` 指定または明示指示がある場合だけ行う。
