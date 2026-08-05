#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf '%s\n' \
    'Usage: install_agent.sh [--agent-dir PATH] [--force]' \
    '' \
    '  --agent-dir PATH  Custom Agent directory (default: ~/.codex/agents)' \
    '  --force           Replace an existing different agent configuration'
}

luna_agent_dir="${HOME:?}/.codex/agents"
luna_force=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent-dir) luna_agent_dir="${2:?}"; shift 2 ;;
    --force) luna_force=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

luna_skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
luna_source="$luna_skill_dir/agents/luna-sprint-worker.toml"
luna_agent_dir="$(mkdir -p "$luna_agent_dir" && cd "$luna_agent_dir" && pwd)"
luna_target="$luna_agent_dir/luna-sprint-worker.toml"

if [[ -e "$luna_target" ]] && ! cmp -s "$luna_source" "$luna_target"; then
  if [[ "$luna_force" -ne 1 ]]; then
    printf 'Existing agent configuration differs: %s\n' "$luna_target" >&2
    printf 'Review it or rerun with --force to replace it.\n' >&2
    exit 1
  fi
fi

cp "$luna_source" "$luna_target"
printf 'Installed luna_sprint_worker configuration: %s\n' "$luna_target"
