# Digital Halo Demo

`DigitalHaloDemo.unity` は、人体 mesh を使用せずに Geometry Shader 版 Effect の4形状を比較する Demo Scene です。

## 確認方法

1. `DigitalHaloDemo.unity` を開く
2. Game view を表示する
3. Play Mode へ入る
4. `Geometry Block Shape Gallery` 以下の Effect を選択する
5. 各 Effect Material の shader properties を調整する

| Object | Point cloud | Material | 初期色モード |
| --- | --- | --- | --- |
| Circle Effect | `CirclePointCloud.asset` | `CircleEffect.mat` | Monochrome |
| Quad Effect | `QuadPointCloud.asset` | `QuadEffect.mat` | Fixed Palette / Cold Steel |
| Line Effect | `LinePointCloud.asset` | `LineEffect.mat` | Single Color |
| Wing Effect | `WingPointCloud.asset` | `WingEffect.mat` | Color Range |

Material から水平・垂直 Rect の比率、サイズ、World 水平変位、World 高さ、各ランダム性、出現率、最大重複数を調整できます。`Color Mode` ではモノクロ、固定パレット、単色、色範囲を選択できます。

`Per Rectangle Distortion`、`Surface Warp`、`Edge Blur`、`Rectangle Haze`、`Rectangle Dissolve` は個別 Rect の歪みとかすれを制御します。各 Effect の子 Object `Block Noise Particles` は対応する point cloud 頂点から Particle を生成します。

Particle は Lifetime 0.24–0.82秒、Emission 42 particles/sec、最大120個に設定しています。

Halo の Transform rotation は identity です。水平 Rect は地面と平行で、垂直 Rect は真横からの視認性を確保します。実際の Avatar へ導入するときは Generator で Head bone を選択してください。
