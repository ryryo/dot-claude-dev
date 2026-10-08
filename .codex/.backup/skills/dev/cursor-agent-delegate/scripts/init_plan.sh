#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: init_plan.sh --workspace PATH --slug SLUG [--date YYMMDD]

Creates docs/PLAN/YYMMDD_slug.md from the bundled template.
USAGE
}

workspace="$PWD"
slug=""
plan_date="$(date +%y%m%d)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) workspace="${2:?}"; shift 2 ;;
    --slug) slug="${2:?}"; shift 2 ;;
    --date) plan_date="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! "$slug" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "--slug must use lowercase letters, digits, hyphens, and underscores" >&2
  exit 2
fi
if [[ ! "$plan_date" =~ ^[0-9]{6}$ ]]; then
  echo "--date must be YYMMDD" >&2
  exit 2
fi

workspace="$(cd "$workspace" && pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
template="$script_dir/../templates/plan.md"
target="$workspace/docs/PLAN/${plan_date}_${slug}.md"

if [[ -e "$target" ]]; then
  echo "Plan already exists: $target" >&2
  exit 1
fi

mkdir -p "$(dirname "$target")"
cp "$template" "$target"
echo "$target"
