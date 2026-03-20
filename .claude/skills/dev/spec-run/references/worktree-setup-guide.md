# WorktreeCreate hook セットアップガイド

`[PARALLEL]` タグ付き Gate を実行するには、Claude Code の WorktreeCreate hook が必要。
このガイドを参考に、プロジェクトに合わせた設定を案内する。

## 前提

- WorktreeCreate hook は **置き換え型**: hook が `git worktree add` から stdout パス返却まで全て担当する
- worktree は `.claude/worktrees/{name}/` に作成される（Claude Code デフォルトと同じ配置）
- `.gitignore` に `**/.claude/worktrees` の追加が必要

## .worktreeinclude

`.worktreeinclude` はプロジェクトルートに作成し、worktree にコピーしたいファイルパターンを列挙する。

- `.gitignore` と `.worktreeinclude` の **両方にマッチ** するファイルのみコピー対象
- CLI v2.1.80 でサポート済み。ただし **置き換え型 hook を使用する場合、CLI の .worktreeinclude 処理はバイパスされる** ため、hook 内で自前コピーが必要

### 対象ファイルの選定基準

| 対象にすべきもの | 対象外にすべきもの |
|---|---|
| `.env.keys` 等の小さな秘密鍵ファイル | symlink（コピーでは不適切） |
| `.env.local` 等の環境固有設定 | 巨大ディレクトリ（`.reference/` 等）→ hook で symlink |
| `.claude/settings.local.json` | `node_modules/` → hook で `install` |

### 例

```
.env.keys
**/.env.keys
*.local
**/*.local
.claude/settings.local.json
**/.claude/settings.local.json
```

> **注意**: bash の glob で `**` を使うには `globstar` が必要だが、macOS のデフォルト bash（v3.2）は未サポート。hook 内では `find` コマンドで代替すること。

## 1. settings.json への hook 追加

`.claude/settings.json` の `hooks` に以下を追加:

```json
{
  "hooks": {
    "WorktreeCreate": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/worktree-setup.sh"
          }
        ]
      }
    ]
  }
}
```

> 既存の hooks がある場合は `WorktreeCreate` キーをマージする。
> `$CLAUDE_PROJECT_DIR` を使うことで worktree 内セッションからも正しくパスが解決される。

## 2. 統合スクリプトの作成

`.claude/hooks/worktree-setup.sh` を作成する。このスクリプト1つで hook の全機能を担当する。

### テンプレート

```bash
#!/bin/bash
# {プロジェクト名} WorktreeCreate hook（統合スクリプト）
#
# stdin: JSON（name, cwd, session_id, hook_event_name）
# stdout: worktree の絶対パスのみ
# stderr: ログ出力用
set -euo pipefail

# --- stdin JSON パース ---
INPUT=$(cat)
NAME=$(echo "$INPUT" | jq -r '.name')
CWD=$(echo "$INPUT" | jq -r '.cwd')

if [ -z "$NAME" ] || [ "$NAME" = "null" ]; then
  echo "ERROR: 'name' field is missing or null" >&2
  exit 1
fi
if [ -z "$CWD" ] || [ "$CWD" = "null" ]; then
  echo "ERROR: 'cwd' field is missing or null" >&2
  exit 1
fi

# --- worktree 作成 ---
DIR="$CWD/.claude/worktrees/$NAME"
mkdir -p "$(dirname "$DIR")"
git -C "$CWD" worktree add "$DIR" HEAD >&2

# ロールバック用 trap
cleanup() {
  echo "ERROR: Setup failed, removing worktree ..." >&2
  git -C "$CWD" worktree remove "$DIR" --force >&2 || true
}
trap cleanup ERR

# --- .worktreeinclude コピー ---
# 置き換え型 hook では CLI の .worktreeinclude 処理がバイパスされるため自前で処理
if [ -f "$CWD/.worktreeinclude" ]; then
  while IFS= read -r pattern || [ -n "$pattern" ]; do
    [ -z "$pattern" ] && continue
    [[ "$pattern" == \#* ]] && continue
    cd "$CWD"
    if [[ "$pattern" == *"**"* ]]; then
      # macOS bash 3.2 は globstar 未サポートのため find で代替
      find_pattern="${pattern//\*\*/\*}"
      find . -path "./$find_pattern" -not -path "./.claude/worktrees/*" -not -path "./node_modules/*" -type f 2>/dev/null | while read -r file; do
        file="${file#./}"
        mkdir -p "$DIR/$(dirname "$file")"
        cp -f "$file" "$DIR/$file"
        echo "Copied $file (.worktreeinclude)" >&2
      done
    else
      for file in $pattern; do
        [ -f "$file" ] || continue
        mkdir -p "$DIR/$(dirname "$file")"
        cp -f "$file" "$DIR/$file"
        echo "Copied $file (.worktreeinclude)" >&2
      done
    fi
  done < "$CWD/.worktreeinclude"
fi

# --- プロジェクト固有のセットアップをここに追加 ---
# 例: symlink 再作成、大きなディレクトリの symlink、依存インストール

# --- 依存インストール ---
# cd "$DIR" && npm install >&2  # or pnpm install / yarn install

# trap 解除（正常完了）
trap - ERR

# stdout に絶対パスを出力（Claude Code が要求）
cd "$DIR" && pwd
```

### プロジェクト分析で確認すべき項目

| 確認項目 | 調べ方 | セットアップに反映 |
|----------|--------|-------------------|
| .env / .env.keys の場所 | `find . -name '.env*' -not -path '*/node_modules/*'` | .worktreeinclude に追加 |
| .local ファイル | `.gitignore` で `*.local` が除外されているか | .worktreeinclude に追加 |
| gitignore された symlink | `.gitignore` を Read | hook で symlink 再作成 |
| 巨大ディレクトリ | `.gitmodules` / 大きな読み取り専用ディレクトリ | hook で symlink |
| パッケージマネージャー | `package.json` の `packageManager` / lock ファイル | hook で install |
| モノレポ構成 | `pnpm-workspace.yaml` / `apps/` `packages/` | 各アプリの .env を .worktreeinclude に |

## 3. 実例: ai-codlnk.com プロジェクト

### .worktreeinclude

```
.env.keys
**/.env.keys
*.local
**/*.local
.claude/settings.local.json
**/.claude/settings.local.json
```

### .claude/hooks/worktree-setup.sh

```bash
#!/bin/bash
set -euo pipefail

INPUT=$(cat)
NAME=$(echo "$INPUT" | jq -r '.name')
CWD=$(echo "$INPUT" | jq -r '.cwd')
# ... (テンプレートの JSON パース + worktree 作成 + .worktreeinclude コピー)

# dot-claude-dev symlink の再作成
for dir in rules skills hooks commands; do
  src_dir="$CWD/.claude/$dir"
  [ -d "$src_dir" ] || continue
  for entry in "$src_dir"/*/; do
    [ -d "$entry" ] || continue
    entry_name=$(basename "$entry")
    main_link="$CWD/.claude/$dir/$entry_name"
    worktree_link="$DIR/.claude/$dir/$entry_name"
    if [ -L "$main_link" ] && [ ! -e "$worktree_link" ]; then
      target=$(readlink "$main_link")
      mkdir -p "$DIR/.claude/$dir"
      ln -s "$target" "$worktree_link"
    fi
  done
done

# 参照用 submodule（38MB+ → symlink）
[ -d "$CWD/.reference" ] && rm -rf "$DIR/.reference" && ln -s "$CWD/.reference" "$DIR/.reference"

# 依存インストール
cd "$DIR" && pnpm install >&2

trap - ERR
cd "$DIR" && pwd
```

## 案内のフロー

dev:spec の Step 8 で以下の手順で案内する:

1. `.claude/settings.json` を Read し、WorktreeCreate hook が設定済みか確認
2. **未設定の場合**:
   a. プロジェクトを分析（上記「確認すべき項目」テーブルに従う）
   b. `.worktreeinclude` の内容を提案
   c. `.claude/hooks/worktree-setup.sh` の内容を提案（テンプレート + プロジェクト固有処理）
   d. `settings.json` への hook 追加方法を案内
3. **設定済みの場合**: スキップ
