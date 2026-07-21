---
title: cron の Threads 投稿を複数画像（カルーセル）対応にし、record_output.py の記録ハングを再修正 — セッション履歴
date: 2026-07-21
sidebar:
  hidden: true
---

# セッション履歴

> 2026-07-21 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260721_threads_carousel_and_record_ipv4/)

---
## よーん *(20:35 JST)*

cron の threads 投稿処理って今日動いてる？

### Claude *(20:35 JST)*

Not logged in · Please run /login

*[ツール: `Bash`]*

cron は動いていますが、**今日の投稿はすべて失敗しています**（6時・17時・20時とも）。同じ下書き（動物園の投稿・thread_id 19f7d260ec6a3745）でエラーが続いています。

## 原因

Threads API が画像を取得できずエラー（`素材下载失败`）。エラーの URI を見ると：

```
https://pbs.twimg.com/media/HNkUvnIb0AAH8j7.jpg  ←4枚のURLが
https://pbs.twimg.com/media/HNkUvqRb0AAPir1.jpg  ←区切りなしで
https://pbs.twimg.com/media/HNkUvqOaoAAAdqY.jpg  ←連結され
https://pbs.twimg.com/media/HNkUvqEbAAEmPBV.jpg  ←1つのURLに化けている
```

これは昨日私が作成した**動物園の投稿（行1229）**です。この投稿は**画像が4枚**あり、X投稿一覧の「画像URL」列に4つのURLが連結して入っていました。`make_threads_draft.py` がそれをそのまま `[画像URL]` に入れたため、壊れたURLになっていました。

つまり **複数画像の投稿に対応できていない**のが根本原因です（Threads は1投稿に複数画像を載せるにはカルーセル形式が必要で、単純連結URLは不正）。

## 当面の対処

この下書きは複数画像のため今の仕組みでは投稿できません。放置すると毎回 cron が失敗し続けます。対処案：
1. **この下書きを削除**（動物園投稿は複数画像なので転載を諦める）— 最短
2. 下書きを編集して `[画像URL]` を**1枚だけ**に手動修正して再送信
3. `make_threads_draft.py`/`post_threads.py` を**複数画像（カルーセル）対応**に改修（要スクリプト変更・別途計画）

まず1か2で詰まりを解消し、3は必要なら別途どうしますか？

---

## よーん *(20:42 JST)*

3 をお願い

### Claude *(20:42 JST)*

了解しました。複数画像（カルーセル）対応を実装します。まず現状を調査します。

*[ツール: `Bash`]*

画像URLは**改行区切り**で格納されていました。既存スクリプトの画像処理を確認します。

*[ツール: `Read`]*

画像URLは改行区切りで格納され、`extract_tag` 経由で `post_threads.py` まで届いています。つまり**修正が必要なのは `post_threads.py` だけ**（複数URLを分割してカルーセル投稿する）で、`make_threads_draft.py` とシェルは既に複数URLを運んでいます。まず Threads カルーセルAPIの仕様を確認します。

*[ツール: `ToolSearch`, `WebFetch`]*

カルーセル仕様を確認しました（2〜20枚、item container→CAROUSEL container→publish）。`post_threads.py` を複数画像対応に改修します。

*[ツール: `Edit`]*

Now update `main` to parse URL lists and update the callers/dry-run:

*[ツール: `Edit`]*

Also update the docstring to reflect multi-image support:

*[ツール: `Edit`]*

Now dry-run test with the stuck draft (4 images):

*[ツール: `Bash`]*

カルーセル・単一画像とも正しくパースされます。構文チェックとコミットをします。

*[ツール: `Bash`, `Bash`]*

*[ツール: `Bash`]*

master に push しました（`fc7c900`）。

修正が完了しました。動作の最終確認として、詰まっている動物園の下書き（4枚画像）を今ここで実際に投稿してカルーセルが通るか検証したいのですが、これは Threads への実投稿になります。どうしますか？

*[ツール: `AskUserQuestion`]*

詰まっている動物園の下書きを実投稿して検証します。

*[ツール: `Bash`]*

投稿成功しました（timeout はログ確認の待ちで、投稿自体は成功）。後続処理（ラベル・記録）の完了を確認します。

*[ツール: `Bash`]*

投稿は成功しましたが、Bash ツール側の2分制限で後続処理（ラベル・記録）の途中で切れた可能性があります。**再実行は二重投稿の恐れがある**ので、まず状態を確認します。

*[ツール: `Bash`]*

動物園スレッドは `Label_103`（投稿済み）付与＋INBOX解除済みなので**再処理・二重投稿の心配はありません**。outputs 記録が完了したか確認します。

*[ツール: `Bash`]*

ラベルは付いたが outputs 記録が私の2分制限で切れていました。手動で補完します（x_url は元ポスト＝動物園投稿）。

*[ツール: `Bash`, `Bash`]*

read は通るのに record_output.py の書き込みが止まる状況です。ネットワークの間欠的な問題の可能性があるため、直接実行で再試行します（記録0件確認済みなので二重記録の心配なし）。

*[ツール: `Bash`]*

record_output.py が90秒でも完了しません。書き込み経路のどこで止まるか、タイミング付きで切り分けます。

*[ツール: `Bash`]*

インライン書き込みは1.3秒で成功しました（データは記録済み）。`record_output.py` 固有のハングが残るので、重複がないか確認しつつ原因箇所を特定します。

*[ツール: `Bash`]*

記録は**1件のみ・正しいデータ**（x_url=元Xポスト）で確定。二重記録なしです。record_output.py 固有のハング原因を確認するため中身を読みます（cron の記録信頼性に関わるため）。

*[ツール: `Read`]*

**根本原因を発見しました。** `record_output.py` から **IPv4 固定パッチが消えています**（24-25行目で `import gspread` の前にパッチがない）。7/12 に追加したはずのパッチが、7/13-15 の x_url 対応リファクタ（`9be5617`）で失われていました。だから IPv6 AAAA 解決でハングします（インライン版は全てパッチ入りなので成功していた）。再追加します。

*[ツール: `Edit`]*

Now verify record_output.py runs fast (it will create a 2nd row — I'll delete it after confirming, since data is already recorded):

*[ツール: `Bash`]*

1.3秒で完了。修正確認できました。テスト行を削除します。

*[ツール: `Bash`]*

テスト行削除、最終状態クリーン（動物園1件のみ）。record_output.py の修正をコミットします。

*[ツール: `Bash`]*

両方 master に push しました。完了です。

## 完了サマリー

**質問への回答**: cron は動いていましたが、今日は6/17/20時とも**投稿失敗**していました。原因は2つ見つかり、両方修正しました。

| # | 問題 | 原因 | 対応 |
|---|---|---|---|
| 1 | 複数画像の投稿が失敗 | 4枚の画像URLが1つに連結され不正URL化。Threads の複数画像はカルーセル形式が必要 | `post_threads.py` を**カルーセル対応**に改修（2枚以上→item container→CAROUSEL→publish）。`6e99d78` |
| 2 | outputs 記録がハング | `record_output.py` の**IPv4固定パッチが消失**（7/13-15 の x_url リファクタ `9be5617` で欠落）→ IPv6 で接続ハング再発 | パッチを再追加（60秒超ハング→1.3秒）。`257f6be` |

**検証結果**（実投稿で確認）:
- 詰まっていた動物園の下書き（4枚画像）→ **カルーセルで投稿成功** https://www.threads.com/@usephys1/post/DbDcokaHazV
- ラベル付与・INBOX解除・outputs 記録（x_url付き）まで完走。二重投稿・二重記録なし

これで今後の cron は複数画像投稿も正しくカルーセル化し、記録も安定します。

補足: この一連（カルーセル対応＋record_output 再修正）は原因調査の経緯が有用なので、`/record` での記録をお勧めします。どうしますか？

STEP 1・2 を実行します。

*[ツール: `Read`, `Bash`]*

STEP 3: 未記録変更の候補を提案します。

changelog（最新 7/20）と直近コミットを照合しました。

---

**変更ログ候補（未記録）**

以下が記録されていません。記録するものを選んでください（複数選択可）：

1. **cron の Threads 投稿を複数画像（カルーセル）対応にし、record_output.py の記録ハングを再修正** — 複数画像の投稿が「画像URL連結」で全失敗していた不具合を、`post_threads.py` のカルーセル対応（2枚以上→item container→CAROUSEL→publish）で解消。あわせて `record_output.py` の IPv4 固定パッチが x_url 対応リファクタ（`9be5617`）で消失し記録ハングが再発していたのを再追加。実投稿で動物園4枚画像のカルーセル投稿＋記録完走を確認。
   - 関連コミット: `fc7c900`（カルーセル対応）、`257f6be`（record_output IPv4 再追加）
   - 変更ファイル: `scripts/post_threads.py`、`scripts/record_output.py`
   - 関連する過去の変更: 「Threads 自動投稿の不具合修正（threads_manage_replies 再認証＋record_output の IPv6 ハング解消）」（7/12）、「reporter-daily に threads/note 投稿の種類判定と x_url 連携を追加」（7/15）

2. **Threads 下書き自動作成の運用調整（[XURL]タグ付与・件数6件化・候補条件緩和・投稿cron時刻変更）** — 数日にわたる細かい調整の束。`make_threads_draft.py` に元X投稿URLの `[XURL]` タグ付与、下書き件数 4→6件、候補条件の緩和（リプライ・引用RT/誘導・紹介のみ除外）、threads 投稿 cron を 6/17/20時に変更。
   - 関連コミット: `2931620`（候補緩和・cron時刻）ほか（[XURL]・count 変更）
   - 変更ファイル: `scripts/make_threads_draft.py`、`scripts/run_threads_draft.sh`、`scripts/run_threads_post.sh`
   - 関連する過去の変更: 「X投稿一覧からランダム選択して【threads投稿】Gmail下書きを自動作成する仕組みを追加」（7/12）

（記録するものを番号で指定してください。すべて記録不要なら「スキップ」と言ってください。）

---

## よーん *(21:03 JST)*

1。２は記録不要

### Claude *(21:03 JST)*

STEP 4: 報告書を作成します。

*[ツール: `Bash`]*

両ファイルとも未コミット変更なし・直近コミットに存在（STEP 4.7 OK）。報告書を作成します。

*[ツール: `Write`]*

