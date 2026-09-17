# 参照画像の出典・用途・除外理由

対象記事: 20260903_ルナ9号FAX（1966年2月・ジョドレルバンク天文台）

## 機体形状の正解（最優先の参照）

| ファイル | 出典 | ライセンス | 用途 |
|---|---|---|---|
| `jodrell_markI_1963.jpg` | Wikimedia Commons `File:Jodrell Bank (5960779768).jpg`（The National Archives UK 提供 / Jodrell Bank クレジット）<br>https://commons.wikimedia.org/wiki/File:Jodrell_Bank_(5960779768).jpg | **No known copyright restrictions** | **機体形状の唯一の正解。撮影 1963年12月＝題材（1966年2月）の2年2ヶ月前で、Mark I 期の実機。** |

**この写真から確定した Mark I の姿**（生成時に必ず守る）:
- 支持塔は**開いた鉄骨の骨組みだけ**。白い箱形の大きな駆動室や、窓のある建物のような塔は**当時は存在しない**。
- 皿の背面は**格子状の骨組みが露出**し、透けて見える。厚い一枚板のパネルではない。
- 色は白ではなく**淡いグレー〜シルバー**。

## 構図・アオリ角度の参照（形状は真似させない）

| ファイル | 出典 | ライセンス | 用途 |
|---|---|---|---|
| `lovell_telescope_full.jpg` | Commons `File:Lovell Telescope1.jpg` | CC BY-SA 4.0 | 皿・トラス・2本の塔の**位置関係のみ** |
| `lovell_telescope_lowangle.jpg` | Commons `File:Lovell Telescope 16.jpg` | CC BY-SA 4.0 | **皿の凹面（内側）の質感の正解**＝滑らかで連続した淡い白の反射面。あわせてアオリ角度の手本 |
| `lovell_telescope_towers.jpg` | Commons `File:Lovell Telescope 02.jpg` | CC BY-SA 4.0 | 支持塔・駆動部の形状補足 |

**注意**: この3枚はいずれも **1970〜71年の Mark IA 改修後**の姿。ただし**皿の凹面が滑らかな連続面である点は Mark I も同じ**で、
1963年の写真が格子に見えるのは**背面**を写しているため。皿の反射面が張り替えられ、背面に補強のホイールガーダーが追加され、
白い箱形の駆動室が付いている。**表面の造作と白い箱形の塔は決して再現させない。**構図と角度の参照に限る。

## 年代の経緯（記録）

初回生成（`thumbnail/lovart/_v1_markIA_based.png`）は改修後の3枚だけを参照したため、
**白い箱形の駆動室とパネル張りの皿という Mark IA の特徴が入ってしまった**。
2026-09-17 に Mark I 期（1963年12月）の実写が見つかったため、これを第1参照にして新規スレッドから再生成し差し替えた。

## 除外した候補

- `File:Snugburys Lovell Telescope straw sculpture 2007 10.jpg` — 望遠鏡を模した**藁の彫刻**で実機ではないため除外。
- `File:Lovell Telescope analogue computer 1.jpg` — 制御室のアナログ計算機。**本文の解決手段（信号処理・受信機）を連想させる**ため除外。
- ルナ9号のパノラマ実写・月面クローズアップ — **本文の結末そのもの**のため参照にも使わない。

## 既知の限界

- **月の満ち欠けは実際の1966年2月3日に合わせていない。**当日は新月から約13日で満月に近かったが、生成画像はそれより欠けている。
  画像内で日付を主張していないため許容している。

## 追加参照（2026-09-17）

| ファイル | 出典 | ライセンス | 用途 |
|---|---|---|---|
| `jodrell_markI_1965.jpg` | Wikimedia Commons `File:Jodrell Bank radio telescopes, 1965 - geograph.org.uk - 2129035.jpg`（Robin Webster）<br>https://commons.wikimedia.org/wiki/File:Jodrell_Bank_radio_telescopes,_1965_-_geograph.org.uk_-_2129035.jpg | CC BY-SA 2.0 | 1965年9月＝題材の5ヶ月前の Mark I。**背面からの撮影のため受信機マストは写っていない**。骨格の補助確認用 |

## 受信機マストの形状について（2026-09-17 の調査結果）

- **Mark I 期（1957〜70）に皿の正面＝受信機マスト側が写った写真は、Commons・Web 調査では見つからなかった。**
  1963年・1965年の2枚はいずれも皿の背面からの撮影。
- 形状の根拠は次の2つ:
  1. 現代の見上げ写真（`lovell_telescope_lowangle.jpg`）を拡大すると、皿の中心から**先細りの鉄骨マスト1本**が伸び、
     先端に小さな箱形の受信機と細い歩廊が付いている。**三脚ではない。**
  2. Mark I の建設記録に "the **focal mast** was changed from timber to steel before construction was complete" と
     **単数形**で記述がある（jb.man.ac.uk / ICE）。
- 以上と、よーんの「Mark I のアンテナが映っている写真が無ければ現代の形状を参考にしてよい」という指示に基づき、
  **1本マスト**で確定した。
