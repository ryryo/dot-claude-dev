---
description: "Git commit自動化 - 変更内容を把握しているエージェントが直接コミットを実行。軽量・高速。オプション「-p」でプッシュも実行。"
argument-hint: "[-p]"
---

以下の手順でTaskツール（model: haiku, subagent_type: simple-add）を使ってください。

# Git Simple Commit Agent

タスク実行中のエージェント向けシンプルコミットエージェント。
変更内容を既に把握しているエージェントが、直接コミットを実行します。

## オプション

引数に `-p` が含まれている場合は、コミット後に `git push` も実行します。

## 実行フロー

### Step 1: 状態確認（並列実行）

```bash
git status
git diff --stat
git log --oneline -3
```

これらを**並列実行**して現在の状態を素早く把握。

### Step 2: ステージング＆コミット（連結実行）

```bash
git add . && git commit -m "$(cat <<'EOF'
<emoji> <type>: <description(日本語)>

- [変更点1]
- [変更点2]

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Step 3: プッシュ（-p オプション時のみ）

引数に `-p` が含まれている場合のみ実行：

```bash
git push
```

### Step 4: 完了確認

```bash
git status
```

## コミットメッセージ形式

```
<emoji> <type>: <description>

- [変更点1]
- [変更点2]

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Type と Emoji の対応

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
| `ci`       | 🚀    | CI/CD改善              |
