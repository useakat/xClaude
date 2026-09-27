# 採用した画像の出典・ライセンス

> 添付画像 `output/thumbnail.png` は、**実在する2枚の歴史写真を横並びに組んだもの**。
> 実在人物の肖像を AI で生成しない方針のため、本人たちの実写を使用している。
> 原本は W002 記事と共用（`projects/w002/2026-08-10_チャンドラセカール/draft/images/_photos/`）。

---

## 左パネル — アーサー・スタンリー・エディントン

| | |
|---|---|
| 内容 | 観測機器のそばに立つ肖像 |
| 撮影年 | 1944年以前（チャンドラセカールの写真と同時代） |
| 撮影 | Transocean（写真会社・ベルリン） |
| 出典 | Smithsonian Institution Libraries（Flickr Commons 経由） |
| 説明ページ | https://commons.wikimedia.org/wiki/File:Portrait_of_Arthur_Stanley_Eddington_(1882-1944),_Astronomer_(2575160361).jpg |
| ライセンス | **パブリックドメイン**（Flickr Commons「no known copyright restrictions」） |
| クレジット | 法的義務はないが慣例として `Transocean / Smithsonian Institution Libraries` を記載 |

## 右パネル — スブラマニアン・チャンドラセカール

| | |
|---|---|
| 内容 | 若き日の肖像（スタジオ撮影の胸像・モノクロ） |
| 撮影年 | **1934年ごろ**。本編が扱う1935年当時＝24歳の頃にあたる |
| 出典 | AIP Emilio Segrè Visual Archives |
| 取得元 | https://chandra.harvard.edu/graphics/resources/illustrations/chandraYoungPose-tif.tif （NASA/CXC） |
| 説明ページ | https://commons.wikimedia.org/wiki/File:Subrahmanyan_Chandrasekhar_harvard.jpg |
| ライセンス | **Attribution only license**（AIP 提供。帰属表示のみが条件） |
| クレジット | **必須**。画像内に `AIP Emilio Segrè Visual Archives` と焼き込み済み |

AIP の包括許諾（https://aip.libguides.com/esvaguide/copyright ）に基づき、帰属表示付きで使用する。Wikimedia Commons 側の「古いから著作権切れ」という根拠は弱いため採らない。

## 加工の内容

| 加工 | 理由 |
|---|---|
| グレースケールへ正規化 | エディントンの原本はセピア調。並べたときに質感を揃えるため |
| トリミング | エディントン側は台紙の黄色い縁と背景の望遠鏡を除去。両者の頭部の大きさを揃えるため |
| オートコントラスト（cutoff=1） | 経年による全体的な眠さの補正 |

**左右反転・カラー化・顔の加筆修整は行っていない**（歴史資料の改変にあたるため）。

---

## 使用しなかった参照画像

情景を生成する当初方針で収集したもの。方針変更により不使用。**ファイルは経緯の記録として残す。**

| ファイル | 内容 | 不使用の理由 |
|---|---|---|
| `burlington_house_meeting_1868.jpg` | バーリントン・ハウスでの学会の会合を描いた1868年の挿絵（Charles Robinson / The Illustrated London News / Wellcome Collection・**CC BY 4.0**） | 情景生成をやめたため。生成時は構図の参考に使ったが、1868年の服装が1935年と合わず、生成結果が古い時代に寄る一因になった |
| `RAS_council_room_2011.jpg` | 王立天文学会カウンシル・ルーム（Mike Peel・**CC BY-SA 4.0**）。https://commons.wikimedia.org/wiki/File:Royal_Astronomical_Society_-_Council_Room.jpg | 同上。会議室であって講堂ではなく、薄型テレビ等の現代設備も写っている |

検討のうえ最初から除外したもの：王立天文学会の講堂で話者と聴衆が写る2025年の写真2点（Mike Peel・CC BY-SA 4.0）。**実在する存命の人物の顔が判別できる**ため。
