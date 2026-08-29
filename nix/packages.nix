# 開発シェル、Nix profile、コンテナで共有するツールの単一情報源。
{ pkgs }:

with pkgs;
[
  # 基本ユーティリティ
  bashInteractive
  coreutils
  findutils
  gnumake
  gnugrep
  gnused
  which

  # VPM package と listing の生成・検査
  git
  gh
  jq
  python312
  ripgrep

  # 静的検査
  actionlint
  shellcheck
  shfmt
  nixfmt
  statix
  deadnix
]
