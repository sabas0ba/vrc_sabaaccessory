{ pkgs, self }:

{
  repository =
    pkgs.runCommand "sabaaccessory-check"
      {
        nativeBuildInputs = import ./packages.nix { inherit pkgs; };
      }
      ''
        cp -R ${self} source
        chmod -R u+w source
        cd source
        export SABAACCESSORY_ENV=nix-develop
        export PYTHONDONTWRITEBYTECODE=1
        bash scripts/check.sh
        touch "$out"
      '';
}
