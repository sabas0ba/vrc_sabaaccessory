# Changelog

## 0.2.1 - 2026-08-30

- Apache-2.0ライセンス表記とCI検証を統一
- ReleaseコンテナのGit safe.directory設定を追加
- Dissolve=0で全Rectを表示する挙動を保証
- 親Transform回転時のRenderer boundsを拡張

## 0.2.0 - 2026-08-30

- Circle、Quad、Line、Wing の4種類の point cloud shape を追加
- shape ごとの接線情報に基づく水平・垂直 Rect の生成に対応
- World 座標ベースの変位、出現、歪み、欠落ノイズを追加
- モノクロ、5種類の固定パレット、単色、色範囲の4色モードを追加
- Rect 単位の頂点歪み、Surface Warp、Edge Blur、Haze、Dissolve を追加
- shape の point cloud 頂点から Particle を生成
- Particle の Lifetime、発生率、最大数、サイズを増加
- Demo Scene を4形状と4色モードの比較ギャラリーへ変更

## 0.1.0 - 2026-08-29

- Digital Halo generator を追加
- モノクロームの Body/Glow 2 pass glitch/noise shader を追加
- Digital Halo Demo Scene とUnityへの取り込みメニューを追加
- 平面リングを、厚みのある主リング、内外レール、中央レールを持つ立体 mesh へ再設計
- 外周破片を板ポリゴンから20個の立体ブロックへ変更
- シアン/マゼンタ表現を廃止し、白、グレー、黒によるモダンな材質へ変更
- グリッチを色ずれから輝度欠落、明暗反転、微小なレイヤーずれへ変更
- 完全なトーラスを廃止し、point cloud と Geometry Shader による不連続な四角形へ変更
- 四角形のサイズ、水平変位、高さ、出現率、重複数、乱数 seed を Material parameter 化
- Halo を地面と平行に配置し、短寿命のブロック Particle を追加
- Demo Scene から人体を模した mesh を削除
- 水平 Rect と垂直 Rect を混在させ、真横からの視認性を追加
- Geometry Shader の変位、出現、歪み、欠落ノイズを World 座標ベースへ変更
- モノクロ、5種類の固定パレット、単色、色範囲の4色モードを追加
- Rect 単位の頂点歪み、Surface Warp、Edge Blur、Haze、Dissolve を追加
- Circle、Quad、Line、Wing の4種類の point cloud shape を追加
- shape ごとの接線情報を mesh UV に格納し、Rect の生成方向を形状へ追従
- Particle の発生元を各 shape の point cloud 頂点へ変更
- Particle の Lifetime、発生率、最大数、サイズを増加
- Demo Scene を4形状と4色モードの比較ギャラリーへ変更
- PC Avatar、Unity 2022.3、VRChat Avatars SDK 3.10.x に対応
