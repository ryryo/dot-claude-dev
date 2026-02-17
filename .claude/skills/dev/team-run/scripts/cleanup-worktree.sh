#!/bin/bash
# Worktree クリーンアップスクリプト
# Usage: cleanup-worktree.sh <slug>
#
# 処理:
# 1. .worktrees/{slug}/ の worktree を削除
# 2. worktree を prune
# 注意: feature/{slug} ブランチは PR 用に残す

set -euo pipefail

SLUG="$1"
WORKTREE_PATH=".worktrees/${SLUG}"

echo "=== Cleanup Worktree: ${SLUG} ==="

# worktree の削除
if [ -d "${WORKTREE_PATH}" ]; then
    git worktree remove "${WORKTREE_PATH}" --force 2>/dev/null || true
    echo "Removed worktree: ${WORKTREE_PATH}"
fi

# .worktrees ディレクトリが空なら削除
if [ -d ".worktrees" ] && [ -z "$(ls -A .worktrees 2>/dev/null)" ]; then
    rmdir .worktrees
    echo "Removed empty .worktrees directory"
fi

# worktree の整理
git worktree prune

echo "=== Cleanup Complete ==="
