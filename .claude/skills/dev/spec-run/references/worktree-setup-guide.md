# WorktreeCreate hook セットアップガイド

`[PARALLEL]` タグ付き Gate を実行するには、Claude Code の WorktreeCreate hook が必要。
このガイドを参考に、プロジェクトに合わせた設定を案内する。

## 前提

- Layer 1（汎用スクリプト）は `spec-run/scripts/setup-worktree.sh` に配置済み
- `.claude/skills/dev` → `~/dot-claude-dev/.claude/skills/dev` の symlink が設定済み
- Layer 2（プロジェクト固有）のみ新規作成が必要
- worktree は `.claude/worktrees/{name}/` に作成される（Claude Code デフォルトと同じ配置）
- `.gitignore` に `.claude/worktrees/` の追加が必要

## 1. settings.json への hook 追加

`.claude/settings.json` の `hooks` に以下を追加:

```json
{
  "hooks": {
    "WorktreeCreate": [{
      "hooks": [{
        "type": "command",
        "command": "bash .claude/skills/dev/spec-run/scripts/setup-worktree.sh"
      }]
    }]
  }
}
```

> 既存の hooks がある場合は `WorktreeCreate` キーをマージする。

## 2. プロジェクト固有セットアップの作成

`.claude/hooks/worktree-setup.sh` を作成する。Layer 1 が自動で呼び出す。

### テンプレート

```bash
#!/bin/bash
# {プロジェクト名} 固有の worktree セットアップ
set -euo pipefail

WORKTREE_DIR="$1"   # 新規 worktree の絶対パス
MAIN_DIR="$2"       # メイン worktree の絶対パス

# --- 環境変数コピー ---
# プロジェクトの .env ファイルをここに列挙
# cp "$MAIN_DIR/.env" "$WORKTREE_DIR/"
# cp "$MAIN_DIR/apps/xxx/.env.local" "$WORKTREE_DIR/apps/xxx/"

# --- 大きなディレクトリの symlink ---
# コピーすると遅いものは symlink
# ln -sf "$MAIN_DIR/.reference" "$WORKTREE_DIR/.reference"

# --- 依存インストール ---
cd "$WORKTREE_DIR" && npm install  # or pnpm install / yarn install
```

### プロジェクト分析で確認すべき項目

| 確認項目 | 調べ方 | セットアップに反映 |
|----------|--------|-------------------|
| .env ファイルの場所 | `find . -name '.env*' -not -path '*/node_modules/*'` | cp 行を追加 |
| gitignore されたディレクトリ | `.gitignore` を Read | symlink or cp が必要か判断 |
| パッケージマネージャー | `package.json` の `packageManager` / lock ファイル | install コマンドを決定 |
| サブモジュール / 参照ディレクトリ | `.gitmodules` / 大きな読み取り専用ディレクトリ | symlink で共有 |
| wtp 設定 | `.wtp.yml` が存在すれば参考にする | hook の内容を合わせる |
| モノレポ構成 | `pnpm-workspace.yaml` / `apps/` `packages/` | 各アプリの .env をコピー |

## 3. 実例: ai-codlnk.com プロジェクト

```bash
#!/bin/bash
set -euo pipefail
WORKTREE_DIR="$1"
MAIN_DIR="$2"

# 環境変数（3箇所）
cp "$MAIN_DIR/.env" "$WORKTREE_DIR/" 2>/dev/null
[ -f "$MAIN_DIR/apps/chat-web/.env.local" ] && mkdir -p "$WORKTREE_DIR/apps/chat-web" && cp "$MAIN_DIR/apps/chat-web/.env.local" "$WORKTREE_DIR/apps/chat-web/"
[ -f "$MAIN_DIR/apps/backend/.env.local" ] && mkdir -p "$WORKTREE_DIR/apps/backend" && cp "$MAIN_DIR/apps/backend/.env.local" "$WORKTREE_DIR/apps/backend/"

# 参照用 submodule（38MB+ → symlink）
[ -d "$MAIN_DIR/.reference" ] && ln -sf "$MAIN_DIR/.reference" "$WORKTREE_DIR/.reference"

# 依存インストール
cd "$WORKTREE_DIR" && pnpm install
```

## 案内のフロー

dev:spec の Step 8 で以下の手順で案内する:

1. `.claude/settings.json` を Read し、WorktreeCreate hook が設定済みか確認
2. **未設定の場合**:
   a. プロジェクトを分析（上記「確認すべき項目」テーブルに従う）
   b. 分析結果に基づいて `.claude/hooks/worktree-setup.sh` の内容を提案
   c. `settings.json` への hook 追加方法を案内
3. **設定済みの場合**: スキップ
