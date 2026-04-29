#!/bin/bash
# spec-agent-run worktree setup
# Usage: setup-worktree.sh <slug>

set -euo pipefail

if [ $# -lt 1 ] || [ -z "${1:-}" ]; then
    echo "Usage: setup-worktree.sh <slug>" >&2
    exit 1
fi

SLUG="$1"

if ! [[ "$SLUG" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]]; then
    echo "ERROR: Invalid slug '${SLUG}'. Must match ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$" >&2
    exit 1
fi

WORKTREE_PATH=".worktrees/${SLUG}"
FEATURE_BRANCH="feature/${SLUG}"

BASE_BRANCH=""
if BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'); then
    :
elif git show-ref --verify --quiet refs/heads/master; then
    BASE_BRANCH="master"
elif git show-ref --verify --quiet refs/heads/main; then
    BASE_BRANCH="main"
else
    echo "ERROR: Cannot detect base branch (symbolic-ref failed, master/main not found)" >&2
    exit 2
fi
echo "Base branch: ${BASE_BRANCH}" >&2

if ! git fetch origin --quiet 2>/dev/null; then
    echo "WARNING: git fetch origin failed (offline?). Continuing with local refs." >&2
fi

if git show-ref --verify --quiet "refs/heads/${FEATURE_BRANCH}"; then
    echo "Branch ${FEATURE_BRANCH} already exists, reusing" >&2
    if git show-ref --verify --quiet "refs/remotes/origin/${BASE_BRANCH}"; then
        if ! git merge-base --is-ancestor "origin/${BASE_BRANCH}" "${FEATURE_BRANCH}" 2>/dev/null; then
            echo "WARNING: ${FEATURE_BRANCH} is behind origin/${BASE_BRANCH}. Merge is recommended after worktree setup." >&2
        fi
    fi
else
    if ! git branch "${FEATURE_BRANCH}" "${BASE_BRANCH}"; then
        echo "ERROR: Failed to create branch ${FEATURE_BRANCH} from ${BASE_BRANCH}" >&2
        exit 3
    fi
    echo "Created branch: ${FEATURE_BRANCH} (from ${BASE_BRANCH})" >&2
fi

if [ -d "${WORKTREE_PATH}" ]; then
    echo "Worktree ${WORKTREE_PATH} already exists, reusing" >&2
else
    if ! git worktree add "${WORKTREE_PATH}" "${FEATURE_BRANCH}"; then
        echo "ERROR: Failed to create worktree at ${WORKTREE_PATH}" >&2
        exit 3
    fi
    echo "Created worktree: ${WORKTREE_PATH}" >&2
fi

cd "${WORKTREE_PATH}" && pwd
