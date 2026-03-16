#!/bin/bash
# WorktreeCreate hook 用汎用セットアップスクリプト
#
# Claude Code の WorktreeCreate hook から呼ばれる。
# stdin: JSON（name, cwd, session_id, permission_mode, hook_event_name）
# stdout: worktree の絶対パスのみ（他のテキスト不可）
# stderr: ログ出力用
# exit 0: 成功 / 非ゼロ: 失敗

set -euo pipefail

# stdin から JSON を読み取り
INPUT=$(cat)
NAME=$(echo "$INPUT" | jq -r '.name')
CWD=$(echo "$INPUT" | jq -r '.cwd')

if [ -z "$NAME" ] || [ "$NAME" = "null" ]; then
  echo "ERROR: 'name' field is missing or null in stdin JSON" >&2
  exit 1
fi

if [ -z "$CWD" ] || [ "$CWD" = "null" ]; then
  echo "ERROR: 'cwd' field is missing or null in stdin JSON" >&2
  exit 1
fi

# worktree ディレクトリを決定
DIR="$CWD/../worktrees/$NAME"
mkdir -p "$(dirname "$DIR")"

echo "Creating worktree at $DIR ..." >&2

# git worktree add（HEAD から detached ではなく新規ブランチを作成）
git -C "$CWD" worktree add "$DIR" HEAD >&2

echo "Worktree created successfully." >&2

# Layer 2: プロジェクト固有セットアップ（存在する場合のみ実行）
SETUP_HOOK="$CWD/.claude/hooks/worktree-setup.sh"
if [ -f "$SETUP_HOOK" ]; then
  echo "Running project-specific setup: $SETUP_HOOK" >&2
  bash "$SETUP_HOOK" "$DIR" "$CWD" >&2
  echo "Project-specific setup completed." >&2
else
  echo "No project-specific setup found at $SETUP_HOOK (skipping)" >&2
fi

# stdout に絶対パスを出力（Claude Code が要求）
cd "$DIR" && pwd
