{
  description = "SabaAccessory: VRChat Avatar 向け VPM package 開発環境";

  inputs = {
    # dotfiles と同じ nixpkgs revision を使用し、flake.lock と併せて固定する。
    nixpkgs.url = "github:NixOS/nixpkgs/597283ad8aa0b331c788e97c4c262d58877074ef";
  };

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      forAllSystems =
        function:
        nixpkgs.lib.genAttrs systems (
          system:
          function (
            import nixpkgs {
              inherit system;
              config = { };
              overlays = [ ];
            }
          )
        );
    in
    {
      devShells = forAllSystems (pkgs: {
        default = import ./nix/devshell.nix { inherit pkgs; };
      });

      packages = forAllSystems (pkgs: {
        default = pkgs.buildEnv {
          name = "sabaaccessory-toolchain";
          paths = import ./nix/packages.nix { inherit pkgs; };
        };
      });

      checks = forAllSystems (pkgs: import ./nix/checks.nix { inherit pkgs self; });

      formatter = forAllSystems (pkgs: pkgs.nixfmt-tree);
    };
}
