#!/bin/bash
# チーム全体で1つの Git Worktree をセットアップするスクリプト
# Usage: setup-worktree.sh <slug>
#
# 処理:
# 1. feature/{slug} ブランチを作成
# 2. .worktrees/{slug}/ に worktree を作成
# 3. worktree の絶対パスを stdout に出力

set -euo pipefail

SLUG="$1"
WORKTREE_PATH=".worktrees/${SLUG}"
FEATURE_BRANCH="feature/${SLUG}"

# feature ブランチが既に存在する場合はスキップ
if git show-ref --verify --quiet "refs/heads/${FEATURE_BRANCH}"; then
    echo "Branch ${FEATURE_BRANCH} already exists, reusing" >&2
else
    git branch "${FEATURE_BRANCH}"
    echo "Created branch: ${FEATURE_BRANCH}" >&2
fi

# worktree が既に存在する場合はスキップ
if [ -d "${WORKTREE_PATH}" ]; then
    echo "Worktree ${WORKTREE_PATH} already exists, reusing" >&2
else
    git worktree add "${WORKTREE_PATH}" "${FEATURE_BRANCH}"
    echo "Created worktree: ${WORKTREE_PATH}" >&2
fi

# 絶対パスを stdout に出力（Lead が $WORKTREE_PATH として使用）
cd "${WORKTREE_PATH}" && pwd
