# lovart 生成プロンプト — マーズ・パスファインダー X長文ポスト 添付画像

> 仕様は `design-brief.md` を正とする。生成は `/lovart` スキル。出力は `output/thumbnail.png`（16:9）。
> 参照画像: `reference/pia01550_lander_cleanroom_and_mars.jpg` を**1枚だけ添付**する。役割は「**1990年代の JPL の機材と室内の質感の正解**」。※この画像に写る三角形のランダー本体は描かせない（今回の舞台は地上の試験室）。

## プロンプト（日本語・構造化）

**画角**: 16:9 の横長。1600×900px 相当。中景。

**場面**: 1997年夏、アメリカ・カリフォルニアの研究所の試験室。夜。窓はなく、室内は暗い。

**主役**: ブラウン管モニタの前に座る技術者ひとり。**背中から斜め後ろのアングル**で、顔は見えない。前傾して画面を見つめている。白いシャツ、袖をまくっている。

**中心となる機材**: 机の横に立つ**試験用の機材ラック**。むき出しの回路基板が段に差さり、束ねられたリボンケーブルがラック間を渡る。小さな赤と緑のインジケータランプが数点灯っている。製品ではなく「試験用に組まれた一式」であることが見て取れる姿。

**周囲**: 1990年代の試験室。灰色の金属机、厚みのあるブラウン管モニタ、メカニカルキーボード、連続紙のプリントアウトの束、紙コップ、**空いた椅子が数脚**。人の気配が引いた後の空気。

**光**: 光源は**モニタの画面光と卓上の一灯だけ**。全体は青灰色からチャコール。モニタの光は**緑がかって**技術者の輪郭を縁取る。画面の表示は**崩れた走査線**で、文字も数字も判読できない。

**配色**: 彩度は低め。報道写真の質感。騒がしくない、静かに張り詰めたトーン。

**視線誘導**: 技術者の背中 → 緑に光る画面 → 奥のラックのインジケータ。

**禁止**: 画面に読める文字や数字を出さない。ロゴ・ワッペン・透かしを入れない。液晶の薄型ディスプレイ、ノートPC、スマートフォン、LEDパネルなど現代の機材を混ぜない。火星の地表、赤い空、探査車、歓喜の表情を入れない。白い防護服のクリーンルームにしない。

## Negative prompt (English)

text, letters, numbers, words, captions, logo, watermark, signage, readable screen content, legible display, LCD, flat panel monitor, thin bezel, laptop, notebook computer, smartphone, tablet, modern hardware, LED panel, RGB lighting, bright clean lighting, daylight, window, Mars surface, red sky, rover, planet, spacecraft exterior, crowd, celebration, cheering, applause, smiling faces, identifiable face, frontal portrait, cartoon, anime, illustration style, oversaturated colors, lens flare, cluttered composition

## レビュー基準（生成後にこの順で確認）

1. 文字・ロゴ・読める表示が写っていないか
2. 画面が液晶になっていないか（ブラウン管の厚みがあるか）
3. 火星の地表・探査車・歓喜など、結末が写り込んでいないか
4. 「夜・機械のラック・画面に向かう人影」が小さいサムネでも読めるか
5. 1997年の試験室として不自然な機材が混じっていないか
