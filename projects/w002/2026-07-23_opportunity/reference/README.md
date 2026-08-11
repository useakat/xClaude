# reference/ の再取得方法

大容量のバイナリ（3Dモデル・地図の元データ・中間生成物）は `.gitignore` で除外している。
必要になったら以下で再取得・再生成できる。

## 3Dモデル（reference/3d/）

```bash
# 高精細モデル（44,117頂点・テクスチャ12枚・11.9MB）
curl -L -o mer_static_highpoly.glb \
  "https://mars.nasa.gov/system/resources/gltf_files/24883_MER_static.glb"

# ローポリ版（NASA-3D-Resources・Draco 圧縮のためデコードが必要）
curl -L -o opportunity_mer-b.glb \
  "https://raw.githubusercontent.com/nasa/NASA-3D-Resources/master/3D%20Models/Mars%20Exploration%20Rover%20-%20Opportunity%20(MER-B)/Mars%20Exploration%20Rover%20-%20Opportunity%20(MER-B).glb"
npx --yes @gltf-transform/cli@4 copy opportunity_mer-b.glb opportunity_decoded.glb

# 10視点レンダリング（views_hi/ と一覧シート・zip を生成）
OUT=views_hi python3 render_views.py

# 対話式ビューア（opportunity_viewer.html を再生成）
python3 make_viewer.py

# セクション画像①の構造図（roll pitch yaw はビューアの値）
python3 make_structure_fig.py -3 3 -9 --tag white --bg white
```

## 走行経路マップ（reference/maps/）

```bash
# NASA 公式の最終トラバースマップ（PIA23178）
curl -L -o opportunity_final_traverse_PIA23178.jpg \
  "https://d2pn8kiwq2w21t.cloudfront.net/original_images/jpegPIA23178.jpg"
```
`mars_basemap_clean.png`（英語ラベルを除去し火星色に着色した下地）はリポジトリに含めている。

## 写真素材

`output/images/写真クレジット.md` に PIA 番号と出典を記載。いずれも NASA 公開画像（パブリックドメイン）で、
`https://d2pn8kiwq2w21t.cloudfront.net/original_images/jpeg<PIA番号>.jpg` から再取得できる。
