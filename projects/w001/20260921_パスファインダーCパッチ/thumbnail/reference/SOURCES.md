# 参照画像の出典・用途・除外理由

## 採用

### pia01550_lander_cleanroom_and_mars.jpg
- **出典**: NASA/JPL, PIA01550 "Pathfinder Landers - In Test and On Mars"
  https://www.jpl.nasa.gov/images/pia01550-pathfinder-landers-in-test-and-on-mars/
  （直リンク: https://d2pn8kiwq2w21t.cloudfront.net/original_images/jpegPIA01550.jpg）
- **撮影年**: 左＝1996年（JPL クリーンルームでの試験中のランダー）／右＝1997年（火星表面）
- **用途**: **1990年代の JPL の機材・室内の質感の参考**（金属とケーブルの感じ、当時の設備の雰囲気）。
- **年代の整合**: 題材は1997年7月。参照画像は1996〜1997年で**一致**。
- **注意**: この画像に写るランダー本体（三角のペタル構造）は**今回の絵には描かない**。今回の舞台は地上の試験室であり、描くのは「ラックに組まれた電子系の試験機」。本画像はあくまで年代の質感合わせに使う。

## 探したが見つからなかったもの

- **1997年当時の JPL 試験室（テストベッド）内部の公式写真**: NASA Image and Video Library（images-api.nasa.gov）を "Pathfinder testbed" / "JPL control room 1997" / "Mars Pathfinder engineers" / "Space Flight Operations Facility" で検索したが、該当する年代・場面の画像は得られなかった。JPL の25周年記事にも舞台裏の写真は掲載されていない。
- → 室内の構図・機材は `design-brief.md` の記述（CRT の厚み／むき出しの基板とリボンケーブル／紙のプリントアウト／光源はモニタと卓上灯のみ）でプロンプト側に指定する。

## 除外

- **Getty Images 等のストックフォト**: ライセンス上、生成の参照に使わない。
- **火星表面・ソジャーナの画像**: 今回の絵は地上のラボが舞台であり、結末（火星での成功）の先出しになるため除外。

---

## 追加（2026-10-01・火星案への方針変更にともない取得）

### pia01121_lander_on_mars_from_rover.jpg
- **出典**: NASA/JPL, PIA01121 "Sojourner Rover View of Pathfinder Lander"
  https://www.jpl.nasa.gov/images/pia01121-sojourner-rover-view-of-pathfinder-lander/
- **撮影**: 1997年 sol 33、ソジャーナの左前カメラから見たランダー
- **用途**: **火星上に着陸した状態のランダーの全景・姿勢の正解**（ペタルが開いて地面に伏せた姿、カメラマストと気象マストの位置関係）。
- **注意**: 411×190px・グレースケールと低解像度（ローバのカメラ由来）。構図と姿勢の参照に限る。

### pia00613_terrain_airbags.jpg
- **出典**: NASA/JPL, PIA00613 "Martian Terrain, Unfurled Rover Ramps & Deflated Airbags"
  https://www.jpl.nasa.gov/images/pia00613-martian-terrain-unfurled-rover-ramps-deflated-airbags/
- **撮影**: 1997年7月、IMP（ランダー搭載カメラ）
- **用途**: **しぼんだエアバッグの質感と火星の地面（岩の分布・色）の正解**。
- **年代の整合**: 題材と同じ1997年7月。

### pia01550（既出）の用途を更新
- 左半分（1996年 JPL クリーンルーム）を **ランダーの三角ペタル構造の形状の正解** として使う。


---

## 本番採用（2026-10-01）

### pia01466_imp_panorama_full.jpg → `output/thumbnail.png` の元画像
- **出典**: NASA/JPL, PIA01466「Mars Pathfinder panorama of landing site taken by IMP」
  https://photojournal.jpl.nasa.gov/catalog/PIA01466
  （直リンク: https://d2pn8kiwq2w21t.cloudfront.net/original_images/jpegPIA01466.jpg）
- **原版**: 6222×1086 px・カラー。1997年、着陸機搭載カメラ IMP が撮影した360度パノラマ。
- **加工**: 16:9 の切り出し（原版の左から約28%の位置、1930×1086）＋ 2048×1152 へのリサイズのみ。**色調・内容の改変なし。**
- **ライセンス**: NASA/JPL の画像はパブリックドメイン（クレジット: NASA/JPL）。
- **切り出しの意図（2026-10-01 変更）**: 当初はソジャーナ（本件の不具合と無関係）を外す位置で切り出したが、**ソジャーナが写っていたほうが「マーズ・パスファインダーの話」だと一目で分かる**というユーザー判断により、ソジャーナが右端ぎりぎりに入る位置へ変更した。手前左にランダーの太陽電池パネルとしぼんだエアバッグ（主役）、画面奥の右端に岩「Yogi」のそばのソジャーナ（脇役）、遠景に Twin Peaks。
- **ソジャーナを入れることの整理**: 本文は「ランダー側のソフトで起きた不具合」であり、ソジャーナは無関係。画像では**手前の大きさ＝ランダーが主役、端に小さく＝ソジャーナは脇**という関係にしてあり、本文中でもソジャーナには一切触れていないため、誤解を招かない。

### nasa_lander_diagram.png（生成時の参照。本番画像には不使用）
- **出典**: NASA のマーズ・パスファインダー着陸機の構造線画（ユーザー提供）。
- **用途**: lovart 生成時の機体構造の参照。最終的に生成画像は不採用のため、本番では使っていない。

### 不採用（権利上の理由）
- ユーザーから提示されたブループリント風の設計図（右下に `@BLUEGALAXYDESI1 / bgalaxy.redbubble.com` の表記）は、個人アーティストが販売している商用デザインのため、生成の参照に使わなかった。
