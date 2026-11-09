# サムネイル画像の出典（ジェネシス）

## 採用画像

- **ファイル**: `missionswebgenesis_original.jpg`（1000×745・原寸のまま保存）
- **内容**: ジェネシス探査機が収集板を開いた状態の画像（JPLサイトの「Genesis - Sun Missions」に掲載のもの）。収集板（六角形ウェハーが並ぶ円盤）が2枚展開し、手前と奥のカバーも開いている。左右に青い太陽電池パネル
- **取得元（ファイル）**: https://d2pn8kiwq2w21t.cloudfront.net/original_images/missionswebgenesis_i0SDszF.jpg
  - JPLのサイト（jpl.nasa.gov）の画像配信用ドメイン。alt 属性は "Genesis - Sun Missions - NASA Jet Propulsion Laboratory (JPL)"
  - 選定者（よーん）が JPL のページから指定した画像
- **クレジット**: NASA/JPL（JPLのGenesis関連資料で、探査機の画像は "Photo: NASA/JPL" 表記が使われている。**この画像個別のクレジット表記は、今回の取得経路では確認できていない**）
- **ライセンス**: NASA/JPLが制作・公開した画像。NASAのメディア利用ガイドラインに従い、出典（NASA/JPL）を明示すること。**個別のライセンス表示は未確認**
- **要確認**: 画像が実機の写真か想像図／模型かを、掲載ページで確認していない（見た目は精密な想像図または模型写真）。投稿で「写真」とは書かない

## 加工

- 背景がほぼ純黒（RGB 0〜1）のため、元画像の幅いっぱいで16:9の範囲（1000×562）を、機体が全部入る位置（上から97〜659px）で切り出し、1600×900に拡大して `output/thumbnail.png` として保存。
- 機体の色・形には手を加えていない。文字・ロゴは入れていない。
- 右端中ほどに、元画像由来の小さな赤い点がある（機体の一部ではなく、背景のごく小さなノイズ）。

## 用途と選定理由

- 本文の冒頭「太陽のかけらを持ち帰ろう」と、可視ブロックの「収集板を広げて…粒子を捉え続けた」に対応する場面。
- 墜落・回収・洗浄の場面は写さない（物語の展開と結末を先に明かさないため）。

## 検討して採用しなかった画像

- **`GenSC_collection2_150dpi_original.jpg`（NASA/JPL想像図・1200×850）**: ファイルは `thumbnail/reference/` に残してあるが、今回は不採用。出典: https://commons.wikimedia.org/wiki/File:GenSC_collection2_150dpi.jpg （Wikimedia Commons の表示はパブリックドメイン）
- **墜落したカプセルと2機のヘリコプター（NASA/ARC撮影の実写）**: 解像度が800×549と低く、墜落という物語の転換点を先に見せてしまうため不採用。出典: https://www.planetary.org/space-images/genesis-landing-site
