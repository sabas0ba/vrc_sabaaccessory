#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$script_dir/../.." && pwd)"
engine="${CONTAINER_ENGINE:-docker}"
image="${SABAACCESSORY_IMAGE:-sabaaccessory-dev}"
network="${CONTAINER_NETWORK:-none}"

if [ "$#" -eq 0 ]; then
  echo "usage: run.sh <command> [args...]" >&2
  exit 2
fi

run_args=(--rm --network "$network" -v "$root:/workspace" -w /workspace)
for variable_name in GITHUB_TOKEN GH_TOKEN GITHUB_REPOSITORY; do
  if [ -n "${!variable_name:-}" ]; then
    run_args+=(-e "$variable_name")
  fi
done

exec "$engine" run "${run_args[@]}" "$image" "$@"
