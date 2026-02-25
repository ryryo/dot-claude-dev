# dev:fix-symlinks

`.claude/` 配下の壊れた・循環シンボリックリンクを検出・修復する。

## Triggers

- symlink修復, リンク切れ修正, fix-symlinks

## 実行手順

### Step 1: 検出

```bash
# 壊れたシンボリックリンクを検出（循環含む）
find .claude/ -type l ! -exec test -e {} \; -print 2>/dev/null
```

結果が空なら「問題なし」と報告して終了。

### Step 2: 詳細表示

検出されたリンクごとに、リンク先と状態を表示する。

```bash
# 各リンクの詳細
for link in $(find .claude/ -type l ! -exec test -e {} \; -print 2>/dev/null); do
  target=$(readlink "$link")
  echo "  $link → $target"
done
```

### Step 3: 削除

AskUserQuestion で確認後、壊れたリンクを削除する。

```bash
find .claude/ -type l ! -exec test -e {} \; -delete
```

### Step 4: 再リンク（任意）

削除したリンクが共有設定（rules/workflow, skills/dev, hooks/dev, commands/dev）だった場合、`setup-claude.sh` を再実行してリンクを再作成する。

```bash
bash "${CLAUDE_SHARED_DIR:-$HOME/dot-claude-dev}/scripts/setup-claude.sh"
```
