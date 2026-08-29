{ pkgs }:

pkgs.mkShellNoCC {
  name = "sabaaccessory";

  packages = import ./packages.nix { inherit pkgs; };

  env = {
    SABAACCESSORY_ENV = "nix-develop";
    LC_ALL = "C.UTF-8";
    NIX_PATH = "nixpkgs=${pkgs.path}";
    PYTHONDONTWRITEBYTECODE = "1";
  };

  shellHook = ''
    if root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
      export SABAACCESSORY_ROOT="$root"
      export PATH="$root/scripts:$PATH"
    fi

    echo "SabaAccessory development shell (${pkgs.stdenv.hostPlatform.system})"
    echo "  make check: repository validation"
  '';
}
