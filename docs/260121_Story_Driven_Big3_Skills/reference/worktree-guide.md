# Worktree運用ガイド

> **参考**: `docs/SAMPLE/dev/Claude Code Best Practices.md`

---

## 概要

Git Worktreeを使用して、**1ストーリー = 1 Worktree**の独立した作業環境を構築する。
主目的は**衝突の防止**であり、並列開発は副次的な効果。

---

## 基本フロー

```
1. ストーリー受領
       ↓
2. Worktree作成 + ブランチ作成
       ↓
3. Claude起動 → Big 3実行
       ↓
4. PR作成 → レビュー → マージ
       ↓
5. Worktree削除
```

---

## コマンド

### Worktree作成

```bash
# 新しいブランチを作成してWorktreeを追加
git worktree add ../project-{story-slug} -b feature/{story-slug}

# 既存ブランチからWorktreeを追加
git worktree add ../project-{story-slug} feature/{story-slug}
```

### Claude起動

```bash
cd ../project-{story-slug} && claude
```

### Worktree一覧確認

```bash
git worktree list
```

### Worktree削除

```bash
# マージ完了後
git worktree remove ../project-{story-slug}

# ブランチも削除する場合
git branch -d feature/{story-slug}
```

---

## 命名規則

| 対象 | 形式 | 例 |
|------|------|-----|
| Worktreeディレクトリ | `../project-{story-slug}` | `../project-login-form` |
| ブランチ名 | `feature/{story-slug}` | `feature/login-form` |
| story-slug | ストーリーを表す短いスラッグ | `login-form`, `password-reset` |

---

## 運用パターン

### パターン1: 単一ストーリー開発

最も基本的なパターン。1つのストーリーを最後まで完了してからマージ。

```
main ─────────────────────────────────●─────
                                      ↑
feature/login-form ───○───○───○───○──┘
                      ^             ^
                  Worktree作成   PR/マージ
```

### パターン2: 複数ストーリー並列開発

独立したストーリーを複数のWorktreeで同時進行。

```
main ─────────────────────────────●───●─────
                                  ↑   ↑
feature/login-form ───○───○───○──┘   │
feature/password-reset ─○───○────────┘
```

**注意**: 同じファイルを触るストーリーは並列しない。

### パターン3: 緊急対応の割り込み

開発中のストーリーを一時停止し、緊急対応を優先。

```
main ─────────────────●─────────────────●───
                      ↑                 ↑
feature/login-form ──○│─ (一時停止) ───○┘
                      │
hotfix/urgent-fix ────┘
```

---

## Big 3との統合

### story-to-tasks起動時

```bash
# Worktree内でClaude起動後
# /dev:story コマンドでstory-to-tasksスキルを呼び出し
```

### developing実行時

```bash
# Worktree内でTDD/PLANフローを実行
# 各タスク完了ごとにコミット
```

### feedback実行時

```bash
# 実装完了後
# /dev:feedback コマンドでfeedbackスキルを呼び出し
# DESIGN.md更新 → コミット
```

### PR作成・マージ

```bash
# feedbackまで完了後
gh pr create --title "feat: ログインフォーム実装" --body "..."

# レビュー・マージ後
git worktree remove ../project-{story-slug}
```

---

## ベストプラクティス

### すべきこと

| プラクティス | 理由 |
|-------------|------|
| 一貫した命名規則を使用 | 管理しやすい |
| Worktreeごとに1ターミナルタブ | 混乱を防ぐ |
| 完了後は速やかにWorktree削除 | ディスク容量とブランチ整理 |
| IDE/エディタも別ウィンドウで開く | 作業環境の分離 |

### 避けるべきこと

| アンチパターン | 問題 |
|---------------|------|
| 同じファイルを触るストーリーの並列 | マージコンフリクト |
| Worktreeを放置 | ディスク消費、ブランチ増殖 |
| mainで直接開発 | 衝突、ロールバック困難 |

---

## 通知設定（推奨）

複数Worktreeを並列運用する場合、Claudeが入力待ちになったら通知を受け取る設定が便利。

**iTerm2（Mac）の場合**:
1. Preferences → Profiles → Terminal
2. "Notification center alerts" を有効化
3. Claudeが入力待ちになると通知が届く

→ 詳細: [Claude Code公式ドキュメント - Notification Setup](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#notification-setup)

---

## トラブルシューティング

### Worktreeが削除できない

```bash
# 強制削除
git worktree remove --force ../project-{story-slug}

# それでもダメな場合
rm -rf ../project-{story-slug}
git worktree prune
```

### ブランチが削除できない

```bash
# マージされていないブランチを強制削除
git branch -D feature/{story-slug}
```

### Worktree内でgit statusがおかしい

```bash
# Worktree情報の修復
git worktree repair
```

---

## 関連リソース

- **Best Practices原文**: `docs/SAMPLE/dev/Claude Code Best Practices.md`
- **Git Worktree公式**: https://git-scm.com/docs/git-worktree
