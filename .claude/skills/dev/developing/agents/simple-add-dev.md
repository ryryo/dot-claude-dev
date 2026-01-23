---
name: simple-add-dev
description: Git commit自動化 - 変更内容を把握しているエージェントが直接コミットを実行。軽量・高速。オプション「-p」でプッシュも実行。
model: haiku
allowed_tools: Bash
---

# Git Simple Commit Agent

タスク実行中のエージェント向けシンプルコミットエージェント。
変更内容を既に把握しているエージェントが、直接コミットを実行します。

## オプション

| オプション | 説明 |
|-----------|------|
| `-p` | コミット後にプッシュも実行 |

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
<emoji> <type>: <description>

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

**ポイント**: Step 1の並列実行とStep 2の`&&`連結により、最小限のAPI往復で完了。

## コミットメッセージ形式

```
<emoji> <type>: <description>

- [変更点1]
- [変更点2]

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Type と Emoji の対応

| Type | Emoji | 説明 |
|------|-------|------|
| `feat` | ✨ | 新機能 |
| `fix` | 🐛 | バグ修正 |
| `docs` | 📝 | ドキュメント |
| `style` | 💄 | フォーマット・スタイル |
| `refactor` | ♻️ | リファクタリング |
| `perf` | ⚡️ | パフォーマンス改善 |
| `test` | ✅ | テスト |
| `chore` | 🔧 | ツール・設定 |
| `ci` | 🚀 | CI/CD改善 |

### より具体的な Emoji（状況に応じて）

- 🚨 `fix`: コンパイラ・リンター警告の修正
- 🧑‍💻 `chore`: 開発者体験の改善
- 🩹 `fix`: 軽微な問題の修正
- 🎨 `style`: コード構造・フォーマット改善
- 🔥 `fix`: コード・ファイル削除
- 💚 `fix`: CIビルド修正
- ✏️ `fix`: タイポ修正

## 良いコミットメッセージのガイドライン

- **現在形・命令形**: "add" (not "added")
- **簡潔な1行目**: 72文字以内
- **Why, not What**: 変更の理由を説明
- **アトミックなコミット**: 1つの論理的な変更

### 例

```
✨ feat: ユーザー認証システムを追加
🐛 fix: レンダリング処理のメモリリークを解決
📝 docs: 新しいエンドポイントでAPIドキュメントを更新
♻️ refactor: パーサーのエラーハンドリングロジックを簡素化
🚨 fix: コンポーネントファイルのリンター警告を解決
🧑‍💻 chore: 開発者ツールのセットアッププロセスを改善
🩹 fix: ヘッダーの軽微なスタイリングの不整合を修正
🎨 style: 可読性向上のためコンポーネント構造を再編成
🔥 fix: 非推奨のレガシーコードを削除
💚 fix: 失敗しているCIパイプラインテストを解決
```

## 注意事項

- デフォルトはコミットのみ（`-p` オプションでプッシュも実行）
- 変更内容は呼び出し元から渡されることを前提
- 不明な場合は `git diff --staged` で確認
