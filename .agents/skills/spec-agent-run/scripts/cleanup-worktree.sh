#!/bin/bash
# spec-agent-run worktree cleanup
# Usage: cleanup-worktree.sh <slug>

set -euo pipefail

if [ $# -lt 1 ] || [ -z "${1:-}" ]; then
    echo "Usage: cleanup-worktree.sh <slug>" >&2
    exit 1
fi

SLUG="$1"

if ! [[ "$SLUG" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]]; then
    echo "ERROR: Invalid slug '${SLUG}'. Must match ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$" >&2
    exit 1
fi

WORKTREE_PATH=".worktrees/${SLUG}"
FEATURE_BRANCH="feature/${SLUG}"

echo "=== Cleanup Worktree: ${SLUG} ===" >&2

if [ -d "${WORKTREE_PATH}" ]; then
    if DIRTY=$(git -C "${WORKTREE_PATH}" status --porcelain 2>/dev/null) && [ -n "${DIRTY}" ]; then
        echo "ERROR: Worktree ${WORKTREE_PATH} has uncommitted changes:" >&2
        echo "${DIRTY}" >&2
        echo "Commit or stash changes before cleanup." >&2
        exit 2
    fi
fi

if [ -d "${WORKTREE_PATH}" ]; then
    if ! git worktree remove "${WORKTREE_PATH}"; then
        echo "ERROR: Failed to remove worktree ${WORKTREE_PATH}" >&2
        exit 2
    fi
    echo "Removed worktree: ${WORKTREE_PATH}" >&2
else
    echo "Worktree ${WORKTREE_PATH} does not exist, skipping" >&2
fi

git worktree prune

if [ -d ".worktrees" ] && [ -z "$(ls -A .worktrees 2>/dev/null)" ]; then
    rmdir .worktrees
    echo "Removed empty .worktrees directory" >&2
fi

if git show-ref --verify --quiet "refs/heads/${FEATURE_BRANCH}"; then
    if ! git branch -d "${FEATURE_BRANCH}"; then
        echo "ERROR: Failed to delete branch ${FEATURE_BRANCH} (not merged?). Use cleanup-branches for force delete." >&2
        exit 3
    fi
    echo "Deleted branch: ${FEATURE_BRANCH}" >&2
else
    echo "Branch ${FEATURE_BRANCH} does not exist, skipping" >&2
fi

echo "=== Cleanup Complete: ${SLUG} ===" >&2
echo "Cleaned up worktree and branch for ${SLUG}"
