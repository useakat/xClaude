---
title: note流入元の取得を1日ずつに変更（流入元 API が期間全体の上位 N 件以外を other に畳む問題） — セッション履歴
date: 2026-10-04
sidebar:
  hidden: true
---

# セッション履歴

> 2026-10-04 のセッション作業ログ。

← [報告書へ戻る](../../reports/20261004_note_referrers_daily_fetch/)

---

## よーん *(19:36 JST)*

DNS 二追加した

### Claude *(19:36 JST)*

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

note流入元の全期間再構築（400日分・1日ずつ）をバックグラウンドで実行中です。5〜7分ほどかかります。完了したら結果をまとめて報告し、commit & push の確認をします。

*[ツール: `Bash`]*

全て完了しました。

**反映した変更**

| 対象 | 内容 | 確認 |
|---|---|---|
| Caddy | `post` を外し、`xpost.usephys.net`（X 投稿）/ `tpost.usephys.net`（Threads 投稿）を追加 | 両ホストで `/n4ce6fbbf837f` 200・ビーコン・Twitterbot 302・`/profile` を確認。既存4ホスト 200 |
| `post_to_x.py` | 投稿直前に `note.com/takaesu7431/n/<ID>` → `xpost.usephys.net/<ID>` に書き換え（自分の記事のみ。他人の note リンクは触らない） | dry-run で確認 |
| `GetMyTweets.js` | noteURL 列（AI）の抽出に `xpost.usephys.net` を追加 | useakat で clasp push 済み（認証ファイルは元に戻しました） |
| `sync_note_referrers.py` | 「X 投稿」「Threads 投稿」列を追加 | 全期間 400 行を再構築 |
| `bio_clicks_ingest.py` | 列が X 投稿 / Threads 投稿 の2列に | 10/3・10/4 を再集計 |

**副産物として見つかった問題と修正**
note の流入元 API は「要求した期間全体での上位 N 件以外を other に畳む」ため、`--full` のような長期間一括取得だと件数の少ない流入元（usephys ホスト）が日別でも「その他」に落ちていました。`sync_note_referrers.py` を **1日ずつ取得**（クライアント共有・0.6 秒間隔・失敗時は待って再試行）に変えました。再構築後、「その他」の累計は 207 → 171 に減り、10/3・10/4 の usephys ホスト到達が正しく列に入っています。cron の `--period 7d` も同じ経路を通るので今後は畳まれません。Threads（l.threads.com）の累計は 55 で変化なし＝過去分は畳まれていませんでした。

**よーんの運用**：変わりません。メール・下書きには生の note URL を書けば、X 投稿時に自動で `xpost` 経由になります。Threads に手で貼るときは `https://tpost.usephys.net/<記事ID>`。

**留意点**
- 次の cron による note リンク付きセルフリプで、X カードの表示（ドメイン表記）を確認します
- VPS 上の旧 `post.usephys.net` の生成ページとログは残してあります（削除は確認してから行います）

**commit & push 待ちのファイル（7件）**
`redirect/redirects.json`・`scripts/redirect_build.py`・`scripts/post_to_x.py`・`scripts/sync_note_referrers.py`・`scripts/fetch_note_referrers.py`・`scripts/bio_clicks_ingest.py`・`gas/GetMyTweets.js`

master に commit & push してよいですか？

---

## よーん *(19:51 JST)*

commit push

### Claude *(19:52 JST)*

*[ツール: `Bash`]*

master に push しました（`cc4aea2`）。

対象7件：`redirect/redirects.json`・`scripts/redirect_build.py`・`scripts/post_to_x.py`・`scripts/sync_note_referrers.py`・`scripts/fetch_note_referrers.py`・`scripts/bio_clicks_ingest.py`・`gas/GetMyTweets.js`

note 導線計測の一連の変更（Threads 列 → noteURL 列 → 比率配分 → usephys.net 転送サイト → 動的キー → xpost/tpost → 流入元の1日ずつ取得）を記録しますか？`/record` で記録できます。

---

## よーん *(19:52 JST)*

もう一回、今の導線計測についてまとめて

### Claude *(19:53 JST)*

現在の note 導線計測の全体像（xpost / tpost 反映後）です。

## 1. 経路ごとの測り方

| 経路 | 貼るリンク | クリック数 | note 到達数 |
|---|---|---|---|
| ① X 投稿・セルフリプ | 生の note URL を書く → 投稿時に自動で `xpost.usephys.net/<記事ID>` | 転送クリック明細（記事 ID 別）・bioクリック「X 投稿」 | note流入元「X 投稿」 |
| ② X 固定ポスト | `note.usephys.net` | bioクリック「X 固定」 | note流入元「X 固定」 |
| ③ X bio | `usephys.net` | bioクリック「X bio」 | note流入元「X bio」 |
| ④ 他人の X 投稿 | （他人が貼る生リンク） | 投稿件数のみ `logs/x_note_mentions.csv` | note流入元「X」列 ※①が抜けたので、ほぼ④のみ |
| ⑤ Threads bio | `threads.usephys.net` | bioクリック「Threads bio」 | note流入元「Threads bio」 |
| ⑥ Threads 投稿 | 手で貼るとき `tpost.usephys.net/<記事ID>` | 転送クリック明細（記事 ID 別）・bioクリック「Threads 投稿」 | note流入元「Threads 投稿」※生リンクなら「Threads」列 |
| ⑦ Threads 固定ポスト | `tnote.usephys.net` | bioクリック「Threads 固定」 | note流入元「Threads 固定」 |
| 検索・note 内 | — | — | Google / Yahoo / Bing / note.com 列 |

インプ・プロフィール閲覧（クリックの手前）は X アナリティクス／Threads インサイトの値。X 投稿別のインプ・リンククリックは従来どおり X投稿一覧（CSV 取り込み）で、記事別のクリックはビーコンで、と使い分けます。

## 2. 転送サイト（usephys.net）の仕組み

- **経路別に note 到達が分かる理由**：302 ではなく HTML ページで転送し `referrer=origin` を付けるので、note の参照元に自ホスト名が残る。X・Threads のアプリ内ブラウザで参照元が落ちて「直接・不明」になる問題を回避
- **クリックの定義**：転送ページの JS が送るビーコン `/hit?k=<キー>` の件数。CT ログ由来のスキャナ（ブラウザ風 UA、1日 100〜200 件）は JS を実行しないので自動的に除外（除外数は参考列）
- **カード表示**：Twitterbot 等のクローラには 302 を返し、note 本体の OG でサムネ付きカードを作らせる
- **キー**：`xpost` / `tpost` の `/<note 記事ID>` は設定不要の動的キー（ビーコンのキー＝記事 ID）。`/profile` は差し替え前提の名前付きキー（`redirects.json` の `paths`）
- **転送先の変更**：`redirect/redirects.json` を編集 → `sudo python3 scripts/redirect_build.py --apply`

## 3. データの流れ（自動）

| タイミング | 処理 | 書き込み先 |
|---|---|---|
| X 投稿時 | `post_to_x.py` が自分の note リンクを `xpost` に書き換え（他人の note リンクは触らない） | — |
| 毎日 03:00 | `record_note_posts` 内で `sync_note_referrers.py --period 7d`（1日ずつ取得） | 発信記録「note流入元」 |
| 毎日 05:40 | `bio_clicks_ingest.py`（前日の Caddy ログ集計） | 「bioクリック」「転送クリック明細」 |
| 日曜 07:00 | `x_note_mentions.py`（他人の note リンク投稿を検索） | `logs/x_note_mentions.csv` |
| GAS 定期 | `GetMyTweets`（本文・セルフリプの note / xpost URL を AI 列へ） | 「X投稿一覧」 |
| 手動 | X アナリティクス CSV 取り込み（投稿別インプ・リンククリック） | 「X投稿一覧」 |
| 月次（手動） | `x_note_mentions.py --reconcile YYYY-MM` | 画面表示 |

## 4. 「直接・不明」の扱い

参照元が落ちた分。①②③⑤⑥⑦がすべて転送経由になったので、今後の「直接・不明」は④（他人の生リンク）と検索由来に絞られ、ほぼ消える見込みです。月次 reconcile の比率配分（X：note.com：Threads）はそのまま残しますが、出番は小さくなります。

## 5. note API の注意点（今日判明）

note の流入元 API は「要求した期間全体での上位 N 件以外を other に畳む」ので、長期間を一括取得すると件数の少ない流入元が日別でも「その他」に落ちます。`sync_note_referrers.py` は1日ずつ取得する方式に変えました（短時間に数百回叩くとレート制限で非 JSON 応答になるため、0.6 秒間隔・失敗時は待って再試行）。

## 6. 留意点・未確認

- 次の cron の note リンク付きセルフリプで、X カードのドメイン表記（`xpost.usephys.net` と出る可能性）を確認
- Threads ミラーは note リンクを落とす方針のまま（⑤⑦の導線性能を見るため）
- 10/3・10/4 の bioクリック・転送クリック明細・note流入元の usephys 列はテストクリックを含む
- VPS 上の旧 `post.usephys.net` の生成ページ・ログは残置

この内容はそのまま `/record` の報告書に載せられます。記録しますか？

---
