# SabaAccessory Digital Halo

PC 版 VRChat Avatar 向けの Geometry Block Effect です。Circle、Quad、Line、Wing の point cloud から Geometry Shader が不連続な四角形を生成します。Circle は完全なトーラス mesh を使用せず、四角形の集合が出現・消失することで偶然円形に見える構成です。

VFX は shader 内で生成するため、テクスチャを使用しません。

- 水平面と垂直面のサイズが異なる四角形を最大3層まで重複生成
- 出現サイクルごとに四角形の幅、奥行き、高さ、接線方向位置を再抽選
- 水平方向グリッチの最小値、最大値、ランダム性を Material から調整可能
- World 座標を基準に出現位置、水平変位、歪み、欠落ノイズを評価
- モノクロ、固定パレット、単色、下限–上限グラデーションを選択可能
- Rect ごとに四隅の歪み、表面 Warp、エッジぼかし、かすれ、欠落を生成
- Halo 面は地面と平行
- Circle、Quad、Line、Wing の4形状を選択可能
- 各 shape の point cloud 頂点付近に短寿命のブロック Particle を生成
- 実行時 MonoBehaviour とテクスチャは不使用

## 使用方法

1. Hierarchy で Avatar の Head bone を選択する
2. `Tools > SabaAccessory > Digital Halo Generator` を開く
3. Shape から Circle、Quad、Line、Wing のいずれかを選ぶ
4. Size、Radial Span、Source Points、Head からの高さを設定する
5. `Create Digital Halo` を押す
6. 生成された `DigitalHaloMaterial` の shader properties を調整する

point cloud mesh、Halo material、Particle material は `Assets/SabaAccessory/Generated/` 以下に生成されます。Avatar 上には `MeshFilter`、`MeshRenderer`、子 Particle System が配置されます。

## Demo Scene

`Tools > SabaAccessory > Digital Halo > Import and Open Demo Scene` を選ぶと、標準の Unity Samples ディレクトリへ Demo を取り込み、`DigitalHaloDemo.unity` を開きます。

Demo Scene に人体 mesh は含まれません。Circle、Quad、Line、Wing を2×2で配置し、形状と色モードを同時に比較できます。Play Mode に入ると四角形と Particle の出現状態が変化します。

| Sample Object | Shape | Color Mode |
| --- | --- | --- |
| Circle Effect | Circle | Monochrome |
| Quad Effect | Quad | Fixed Palette / Cold Steel |
| Line Effect | Line | Single Color |
| Wing Effect | Wing | Color Range |

## Material parameters

| Property | 内容 |
| --- | --- |
| Color Mode | Monochrome、Fixed Palette、Single Color、Color Range を選択 |
| Fixed Palette | Neutral、Cold Steel、Amber、Violet、Terminal から選択 |
| Color Range Min / Max | 単色またはグラデーションで使用する色の下限と上限 |
| Monochrome Lower | モノクロ時の下限色と不透明度 |
| Opacity | 四角形全体の不透明度 |
| Emission | 明るい四角形の Additive Glow 強度 |
| Rectangle Width Min / Max | 接線方向の四角形サイズ範囲 |
| Horizontal Depth Min / Max | 水平 Rect の半径方向サイズ範囲 |
| Vertical Height Min / Max | 垂直 Rect の高さ範囲 |
| Vertical Rectangle Ratio | 水平 Rect に対する垂直 Rect の生成比率 |
| Size Randomness | サイズ範囲内のランダム性。0 で中間値に固定 |
| World Horizontal Glitch Min / Max | World 接線方向へ移動する距離の範囲 |
| Horizontal Randomness | 水平方向移動のランダム性。0 で中間値に固定 |
| World Appearance Height Min / Max | World Y 方向の出現位置範囲 |
| Height Randomness | 高さ方向のランダム性。0 で中間値に固定 |
| World Noise Scale | World 座標ノイズの空間密度 |
| Appearance Rate | 出現サイクルの更新速度 |
| Spawn Probability | 各 point から四角形が生成される確率 |
| Maximum Overlap | 1 point から同時生成する四角形の最大数 |
| Random Seed | ランダムパターン全体の変更 |
| Per Rectangle Distortion | Rect の四隅へ個別に加える World 空間歪み |
| Distortion Speed | 歪みと表面ノイズの更新速度 |
| Surface Warp | Rect 内部の UV 歪み |
| Edge Blur | Rect の縁のぼかし幅 |
| Rectangle Haze | Rect 内部の濃度むらと、かすれ |
| Rectangle Dissolve | World noise による部分欠落量 |

## 制約

- Geometry Shader を使用するため PC Avatar 専用です
- Android/Quest では Geometry Shader が利用できないため動作対象外です
- Halo は 2 pass、Particle は 1 pass です。同種 Props の多数配置は避けてください
- shader が Safety System でブロックされた場合は `UnlitTransparent` にフォールバックします

## License

MIT License。詳細は `LICENSE.md` を参照してください。
