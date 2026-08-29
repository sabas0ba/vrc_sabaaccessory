#!/usr/bin/env bash
set -euo pipefail

if [ "${SABAACCESSORY_ENV:-}" != "nix-develop" ]; then
  echo "error: enter the development environment with 'nix develop'" >&2
  exit 1
fi

required_commands=(
  actionlint
  bash
  deadnix
  git
  gh
  jq
  make
  nixfmt
  python3
  rg
  shellcheck
  shfmt
  statix
)

for command_name in "${required_commands[@]}"; do
  command_path="$(command -v "$command_name" || true)"
  if [ -z "$command_path" ]; then
    echo "error: required command not found: $command_name" >&2
    exit 1
  fi

  resolved_path="$(readlink -f "$command_path")"
  case "$resolved_path" in
    /nix/store/*) ;;
    *)
      echo "error: $command_name is outside the Nix store: $resolved_path" >&2
      exit 1
      ;;
  esac
done
