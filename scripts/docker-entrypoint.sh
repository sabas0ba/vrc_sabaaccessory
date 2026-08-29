#!/bin/sh
set -eu

profile="${SABAACCESSORY_PROFILE:-/nix/var/nix/profiles/sabaaccessory-dev}"

if [ ! -e "$profile" ]; then
  echo "error: development profile not found: $profile" >&2
  exit 1
fi

if [ "$#" -eq 0 ]; then
  exec nix develop "$profile" --command bash
fi

exec nix develop "$profile" --command "$@"
