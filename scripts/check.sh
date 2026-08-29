#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$script_dir/.." && pwd)"
cd "$root"

bash scripts/check-env.sh

mapfile -t shell_files < <(find scripts .github/scripts -type f -name '*.sh' -print | sort)
mapfile -t nix_files < <(find . -path './.git' -prune -o -path './.direnv' -prune -o -name '*.nix' -print | sort)

shellcheck "${shell_files[@]}"
shfmt --indent 2 --case-indent --diff "${shell_files[@]}"
nixfmt --check "${nix_files[@]}"
statix check .
deadnix --fail .
actionlint
python3 -m unittest discover -s tests -v
python3 .github/scripts/check_package.py --source source.json --packages Packages
