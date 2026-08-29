# SabaAccessory

VRChat Avatar 向け Props を Unity Package Manager/VPM package として開発・配布する
repository です。複数の独立した package を `Packages/` 以下に収容します。

## 開発環境

Unity project は VRChat がサポートする Unity `2022.3.22f1` を使用します。VCC または
ALCOM で本ディレクトリを Avatar project として管理し、VPM Resolver から Avatar SDK を
復元してください。

repository の検証・Release tooling は Nix で固定されています。

```sh
nix develop
make check
make nix-check
```

Nix を直接使用しない環境では、digest 固定したコンテナを使用できます。

```sh
make docker-check CONTAINER_ENGINE=podman
```

package の追加と Release 手順は [開発手順](docs/development.md) を参照してください。

## Packages

- [Digital Halo](Packages/io.github.sabas0ba.sabaaccessory.digital-halo/README.md):
  Circle、Quad、Line、Wing に対応した Geometry Shader ベースの PC Avatar 向け Geometry Block Effect

形状、色モード、各パラメータ、Demo 画像は [Digital Halo 使用ガイド](docs/digital-halo.md) にまとめています。

## VPM repository

GitHub Pages を有効化した後、VCC/ALCOM に次の URL を追加します。

```text
https://sabas0ba.github.io/vrc_sabaaccessory/index.json
```

## License

MIT License。詳細は [LICENSE](LICENSE) を参照してください。
