# CLAUDE.md

本リポジトリは VRChat Avatar 向け Props を VPM package として開発・配布する。
利用者全体の規約を優先し、環境設計は `sabas0ba/dotfiles` の Nix/コンテナ構成に従う。

## 作業環境

作業は `nix develop` または `make docker-shell` で構築した環境内で行う。開始時に
`bash scripts/check-env.sh` を実行し、使用するツールが Nix store に由来することを確認する。
ホストのグローバル環境へツールを追加しない。

ツール一覧の単一情報源は `nix/packages.nix` である。依存、flake input、Docker base
image、GitHub Actions を追加・更新する場合は、事前に利用者の承認を得て revision または
digest を固定する。

## Package

- package は `Packages/io.github.sabas0ba.sabaaccessory.<name>/` に置く
- `package.json` の `name` とディレクトリ名を一致させる
- Avatar SDK 依存は `com.vrchat.avatars: 3.10.x` とする
- Unity Editor API を使用するコードは `Editor/` 以下に置く
- Runtime/Editor の C# assembly には asmdef を用意する
- 配布元 `package.json` に `url` と `zipSHA256` を記述しない。Release 時に生成する
- package を追加・削除した場合は `source.json` の `packages` を同時に更新する

## Release

tag は `<package-id>/v<version>` とし、version は package manifest と一致させる。
Release workflow が決定論的 ZIP、配布 manifest、VPM listing、GitHub Pages を生成する。
生成物を手作業でコミットしない。

## 検証

変更後は `make check` と `make nix-check` を実行する。Dockerfile または `nix/` を変更した
場合は `make docker-check` も実行する。検査を通すために検査自体を弱めない。
