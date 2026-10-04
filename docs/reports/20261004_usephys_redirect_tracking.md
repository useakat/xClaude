---
title: usephys.net 転送サイトで bio・固定・投稿からの note クリック／到達を経路別に計測
date: 2026-10-04
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261004_usephys_redirect_tracking/)

## 背景・動機

X / Threads の bio と固定ポストからの note クリックは、X・Threads 側のどの数字にも出ない。note 側でも、X・Threads のアプリ内ブラウザは参照元を付けないため「直接・不明」に落ち、どの導線から来たのか分からなかった。経路ごとに「クリック数」と「note 到達数」を取る仕組みが必要だった。

候補は (A) 既存の短縮 URL サービス、(B) 自ドメインの HTML 転送、(C) 302 転送。(C) は参照元が元ページ（X など）のまま引き継がれて経路が分からない。(B) なら転送ページ自身が参照元になり、note の流入元に自ホスト名で経路別の行が立つ。ユーザーが (B) を選び、ドメインは `usephys.com` → `usephys.net`（.com は商用サイトに見える懸念）に変更した。

## 実施内容

### 転送サイト（Caddy、VPS 133.18.181.39）

- `redirect/redirects.json` にホスト→転送先を定義し、`scripts/redirect_build.py --apply` が `/var/www/redirect/<host>/…/index.html` と `/etc/caddy/Caddyfile` を生成して `caddy validate` → `systemctl reload caddy`
- **人向け**：HTML 転送ページ（`redirect/template.html`）。`<meta name="referrer" content="origin">` で参照元を自ホストに固定し、meta refresh と `location.replace()` で note へ。JS が `navigator.sendBeacon("/hit?k=<キー>")` を送る
- **クローラ向け**：`Twitterbot` / `facebookexternalhit` 等の UA には 302 で転送先へ。クローラは JS も meta refresh も追わないので、HTML を返すと OG カード（サムネ）が出ない。302 なら note 本体の OG でカードが出る
- `route {}` で `respond /hit 204` → `redir @crawler` → `try_files` → `file_server` の順を固定（既定の順序では `try_files` が先に動き `/hit` が `index.html` に書き換わって 405 になった）
- **動的キー**：`dynamic.pattern` `^/(n[0-9a-f]{10,16})(?:/([A-Za-z0-9_-]{1,32}))?/?$` に一致すると、Caddy の `templates` が記事 ID を埋めた転送ページ（`_dyn.html`）を返す。`xpost.usephys.net/<記事ID>/<投稿キー>` の形で、記事ごとの設定が不要。ビーコンのキーは `<記事ID>/<投稿キー>`
- **名前付きキー**：`paths` で `/<キー>` → 転送先を定義（`map {path} {target}`）。差し替え前提の導線用
- `caddy validate` を root で実行するとログファイルが root 所有で作られ、caddy ユーザーが開けず reload が失敗した。validate 後に `/var/log/caddy/*` を chown する処理を追加

### ホスト構成（最終）

| ホスト | 用途 | 貼る URL |
|---|---|---|
| `usephys.net` | X bio | `https://usephys.net/note` |
| `threads.usephys.net` | Threads bio | `https://threads.usephys.net/note` |
| `xpost.usephys.net` | X 投稿（固定ポスト含む） | `post_to_x.py` が自動で `…/<記事ID>/<投稿キー>` に書き換え |
| `tpost.usephys.net` | Threads 投稿（固定ポスト含む） | 手で `…/<記事ID>/<日付>` |
| `note.usephys.net` / `tnote.usephys.net` | （旧）固定ポスト用。未使用化、ホストは残置 | — |

途中経過：`post.usephys.net` を Threads 投稿用に作った後、X セルフリプも同方式にするため `xpost` / `tpost` に改名（`post` の DNS は削除）。

### 集計

- `scripts/bio_clicks_ingest.py`（cron 05:40）：Caddy の JSON ログから前日分のビーコンを集計し、`bioクリック`（経路列＋除外・合計・参照元あり）と `転送クリック明細`（日付／ホスト／キー／クリック）に upsert
- `scripts/sync_note_referrers.py`：note流入元に X bio / Threads bio / X 固定 / Threads 固定 / X 投稿 / Threads 投稿 列を追加
- `scripts/post_to_x.py`：投稿直前に本文の `note.com/takaesu7431/n/<ID>` を `xpost.usephys.net/<ID>/<投稿キー>` に書き換え。投稿キーはセルフリプなら `--reply-to` の tweet ID（X投稿一覧の行とそのまま結合できる）、本文内リンクなら投稿日時 `YYYYMMDD-HHMM`。他人の note リンクは触らない
- `gas/GetMyTweets.js`：noteURL 列の抽出に `xpost.usephys.net` を追加
- `scripts/record_pinned_post.py`（cron 05:50）：X API の `pinned_tweet_id` を毎日確認し、変わっていれば `固定ポスト履歴` シートに終了日・新規行を記録。記事ID・投稿キーは X投稿一覧の noteURL 列（本文→セルフリプ）から拾う。Threads は API に固定情報が無いため手入力

### スキャナ対策

- 証明書が CT ログに載ると数分でスキャナが来る（ブラウザ風 UA、1日 100〜200 件、全ホストに対称）。当初の「ページ取得＋ヘッダ判定」では除けず、クリックの定義を **JS ビーコン**に変更
- その後、**JS を実行する headless 型のスキャナ**がビーコンまで送ることが判明（xpost / tpost 公開直後の 10 分で `k=_root` が十数件、送信元は Scaleway・AWS・GCP、Accept-Language は `en-US` か無し）。スキャナが知っているのはホスト名だけなので必ず `/` に来る → **`_root` は数えない**（除外に計上）ことにし、bio のリンクも `/note` のパス付きにした。候補だった Accept-Language `ja` フィルタは、日本語ロケールの headless が1件いたこと・日本語以外の読者を除外することから不採用

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `redirect/redirects.json`（新規） | ホスト・転送先・`paths`・`dynamic` の定義 |
| `redirect/template.html`（新規） | 転送ページ（referrer=origin / meta refresh / ビーコン / noscript） |
| `scripts/redirect_build.py`（新規） | ページと Caddyfile の生成、DNS 確認、validate、ログ chown、reload |
| `scripts/bio_clicks_ingest.py`・`run_bio_clicks_ingest.sh`（新規） | ビーコン集計 → bioクリック・転送クリック明細。`_root` 除外 |
| `scripts/post_to_x.py` | note リンクを `xpost` ＋投稿キーに書き換え |
| `scripts/record_pinned_post.py`・`run_record_pinned_post.sh`（新規） | 固定ポスト履歴の自動記録 |
| `scripts/sync_note_referrers.py` | 転送ホスト用の列を追加 |
| `gas/GetMyTweets.js` | `xpost.usephys.net` も noteURL として抽出 |

git 管理外：DNS A レコード（Cloudflare、プロキシ off）、Caddy v2.11.7（`/etc/caddy/Caddyfile` は生成物）、`/var/www/redirect`、`/var/log/caddy`、cron 2 本（05:40・05:50）。

## 設計判断

- **302 ではなく HTML 転送**：参照元を自ホストにするため。クローラだけ 302 にしてカードを両立
- **クリック＝ビーコン**：ページ取得では JS を実行しないスキャナを除けない。ビーコンでも headless 型は残るため、最終的に「パス付きキーのみ数える」を加えた
- **記事 ID をキーにする動的転送**：記事ごとに `paths` を書いて apply する運用は続かない。URL の `n/` 以降を貼るだけにした
- **投稿キー＝元ポストの tweet ID**：投稿ごとに違えばよく、日時・連番・ランダムより X投稿一覧と直接結合できる tweet ID を選んだ。本文内リンク（ID が投稿前に無い）だけ日時にフォールバック
- **固定ポストは通常リンクのまま**：固定を変えるたびにリンクを固定用ホストに書き換えるのは嫌、というユーザー要望。固定期間を `固定ポスト履歴` で持てば、転送クリック明細のキー `<記事ID>/<固定ポストの tweet ID>` で日別クリックが追える。失うのは note 到達の「固定／通常」の分離だけ（到達率は経路共通でほぼ一定）
- **Threads の投稿キーは日付**：手で貼るため、投稿前に分かる ID が無い

## 確認結果

- 全ホストで `/`・`/<キー>`・`/<記事ID>`・`/<記事ID>/<投稿キー>`・末尾スラッシュ・不正キーのフォールバックが期待どおり（200・ビーコンキー・転送先）。Twitterbot UA は 302。`POST /hit` は 204
- `post_to_x.py --dry-run` でセルフリプ（tweet ID キー）・本文内リンク（日時キー）・他人の note リンク（不変）を確認
- `bio_clicks_ingest.py` で `転送クリック明細` に記事 ID／投稿キー別の行が立つことを確認。`_root` 除外後、10/4 の bio・固定は 0（残りはテスト分のみ）
- note流入元に `usephys.net` 等の到達が 10/3・10/4 から記録され、転送 → note 到達が端から端まで動いている
- `record_pinned_post.py` 初回実行で現在の固定ポスト（7/25 カッシーニ、記事 ne410d5bd0b1f、生リンク）を登録。2回目は「変更なし」
- ユーザーが X・Threads の bio を `/note` 付き URL に差し替え済み

## 今後の課題

- 次の cron セルフリプで X カードの表示（ドメイン表記が `xpost.usephys.net` になるか）を確認
- 旧 `post.usephys.net` の生成ページ・ログの削除、`X 固定` / `Threads 固定` 列の整理
- 月次突合（`--reconcile`）の配分対象の見直し（直接・不明がほぼ消える見込み）
- 現在の固定ポストは生 note リンクなのでビーコンに乗らない。今日以降の投稿を固定すれば日別クリックが追える
- Threads の固定ポストは `固定ポスト履歴` に手入力
