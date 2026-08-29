# 開発手順

## Package の追加

`Packages/io.github.sabas0ba.sabaaccessory.<name>/` を作成し、最低限次を配置します。

```text
package.json
README.md
CHANGELOG.md
LICENSE.md
Runtime/ または Editor/
```

`package.json` の例です。

```json
{
  "name": "io.github.sabas0ba.sabaaccessory.example",
  "displayName": "SabaAccessory Example",
  "version": "0.1.0",
  "unity": "2022.3",
  "description": "Package description.",
  "author": {
    "name": "sabas0ba",
    "email": "sabas0ba@outlook.com",
    "url": "https://github.com/sabas0ba"
  },
  "license": "MIT",
  "vpmDependencies": {
    "com.vrchat.avatars": "3.10.x"
  }
}
```

package directory を追加したら `source.json` の `packages` に同じ ID を辞書順で追加します。
Unity が生成する `.meta` ファイルも対応する asset と同じ commit に含めます。

現在の package は次のとおりです。

- `io.github.sabas0ba.sabaaccessory.digital-halo`: PC Avatar 向け Digital Halo

## 検証

```sh
nix develop
make check
make nix-check
```

`make check` は次を検査します。

- shell、Nix、GitHub Actions の静的検査
- package ID、SemVer、Unity version、Avatar SDK dependency
- Release 専用 field が配布元 manifest に混入していないこと
- UnityEditor API が `Editor/` 外にないこと
- 決定論的 ZIP と配布 manifest の unit test

Unity 上では、対象 package を開発 project に埋め込んだ状態で compile と EditMode test を
実行します。Unity Editor は Nix container の対象外です。

## Release

1. `package.json` と `CHANGELOG.md` の version を更新する
2. 検証を通して default branch に反映する
3. `<package-id>/v<version>` tag を作成して push する、または `Build Release` workflow を
   package ID 指定で手動実行する
4. GitHub Release の ZIP と JSON、および GitHub Pages の `index.json` を確認する

Release workflow は package directory の内容から決定論的 ZIP を生成します。Release 用
manifest に download URL と SHA-256 を追加し、listing workflow が全 Release を集約します。

## GitHub repository の初期設定

- repository の default branch を `main` にする
- Settings → Pages → Build and deployment → Source を `GitHub Actions` にする
- Actions に `contents: write`、`actions: write`、Pages deployment の使用を許可する
- branch protection では `Verify / Repository validation` を必須 check にする
