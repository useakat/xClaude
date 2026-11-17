---
title: X 投稿の予約カレンダー Web アプリ（postcal）を新設し、cron 4 枠の最優先キューにする
date: 2026-11-17
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261117_postcal_schedule_calendar/)

## 背景・動機

X への投稿は Gmail の受信箱がキューになっている（スキルが下書きを作る → よーんが自分宛に送信 → 06/12/17/20 の cron が件名・時刻ラベルで拾って X と Threads に投稿）。よーん自身が書く投稿（自己開示・フォロワー感謝・販促など）を「どの日のどの枠に出すか」を見渡しながら登録する手段が無く、件名と Gmail ラベルで枠を管理するのは限界があった。

要件：投稿文・画像/動画・セルフリプ・投稿種類を、cron の 4 枠（6:00 / 12:00 / 17:00 / 20:00）に限定した日時で登録できる。投稿は X と同時に Threads にも出る。セルフリプの note リンクは投稿時に転送サイト URL へ変換される。カレンダーで日ごとの予約を見られ、そこから登録もできる。既存の投稿スクリプトを使い回す。

よーんの決定（2026-11-15）：
- 公開サブドメイン `post.usephys.net` ＋ Basic 認証（スマホから使う）
- 投稿種類 → what_id：短文=z01 / 長文=W001 / 自己研鑽=W004 / 自己開示=W004 / フォロワー感謝=W004 / 販促=W007（自己研鑽・フォロワー感謝は what シートに行を作らず W004 で記録）。2026-11-17 にワンポイント解説=W003 を追加
- 動画は初回から対応。Threads のセルフリプに note リンクが含まれる段は現行どおり Threads には載せない

## 実施内容

- **Web アプリ `postcal/`**（Starlette + Jinja2 + SQLite）：月カレンダー（日セルの「＋」から登録・チップに時刻/種類/状態色）、登録・編集・削除フォーム、同一日・同一枠は 1 件まで（枠＝1 投稿の現行ルール）、画像最大 4 枚（png/jpg/gif）または動画 1 本（mp4/mov）、セルフリプは `=====` 区切り、`/m/<uuid>.<ext>` でメディアを公開配信（Threads API が取得する）。`postcal/data/` は git 管理外
- **枠ランナー `scripts/post_scheduled.py <6|12|17|20>`**：今日のその枠の `queued` 行を `UPDATE … WHERE status='queued'` で原子的に確保 → `post_to_x.py`（本文＋メディア） → セルフリプを `--reply-to` で返信チェーン → `record_output.py <url> <what_id> --neta-id postcal[<id>]` → Threads 転載（`note.com` を含む段だけ除外） → `posted` / `failed` に更新。失敗は `send_gmail.sh` で通知。rc 0=投稿 / 20=予約なし / 1=失敗
- **cron 4 枠のラッパー**（`run_xonepoint_post.sh` / `run_question_post.sh` / `run_xlong_post.sh` / `run_xshort_post.sh`）の先頭で `post_scheduled.py <枠>` を呼び、rc=20 のときだけ従来の Gmail キュー（`post_by_label.sh` → 件名検索 → Threads 下書き）へ進む
- **`post_to_x.py`**：`--image` を複数可（最大 4）、`--video` 追加（tweepy の `chunked_upload(media_category="tweet_video")` ＋手動ポーリング。tweepy は `failed` 状態で黙って返るため `processing_info.state` を検査。全体 5 分上限）。既存の呼び出しと `https://x.com/i/web/status/<id>` の出力は不変
- **`post_threads.py`**：`--video-url` / `--reply-video-url` 追加。動画コンテナは 300 秒待ち。画像と動画の混在カルーセル可
- **Caddy**：`redirect/redirects.json` に `proxies` を追加し、`redirect_build.py` が `post.usephys.net` の reverse_proxy ブロックを生成（`@auth not path /m/*` ＋ `basic_auth`、`X-Robots-Tag: noindex`、JSON ログ）。ハッシュは `.env` の `POSTCAL_BASIC_AUTH='yohn:<bcrypt>'` から埋め込む（Caddy は `caddy` ユーザーで動き `.env` を読めないため）。値が無ければ apply を中断し、認証なしのホストを書かない
- **配備**：`postcal/postcal.service`（uvicorn を 127.0.0.1:8787 で常駐、`Restart=always`、`.env` は渡さない）と `scripts/postcal_install.sh`（ユニット設置 → `systemctl enable --now` → healthz → `redirect_build.py --apply`）
- `docs/workflows/x-auto-post.md` に枠の処理順（postcal → 時刻ラベル → 件名）を追記

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `postcal/app.py` `db.py` `kinds.py` `templates/*` `static/*` | 新規。Web アプリ本体（ルート・SQLite・種類表・テンプレート・CSS/JS） |
| `postcal/postcal.service` | 新規。systemd ユニット |
| `scripts/post_scheduled.py` | 新規。枠ランナー |
| `scripts/postcal_install.sh` | 新規。配備スクリプト |
| `scripts/post_to_x.py` | `--image` 複数・`--video` 追加 |
| `scripts/post_threads.py` | `--video-url` / `--reply-video-url` 追加・動画待機 300 秒 |
| `scripts/run_xonepoint_post.sh` `run_question_post.sh` `run_xlong_post.sh` `run_xshort_post.sh` | 先頭で `post_scheduled.py <枠>` を呼ぶ |
| `scripts/redirect_build.py` `redirect/redirects.json` | `proxies` の Caddy ブロック生成 |
| `.gitignore` | `/postcal/data/` を除外 |
| `docs/workflows/x-auto-post.md` | 枠の処理順を追記 |

## 設計判断

- **アプリは「予約の保管庫」に徹し、投稿は cron 側で行う**：X への投稿は cron 定時実行のみ（CLAUDE.md）。アプリに「今すぐ投稿」は付けず、X/Threads の秘密もアプリには渡さない
- **公開メディア URL は自前配信**：Threads API は公開 URL からメディアを取得する。X の CDN から取り直す `fetch_tweet_media.py` は動画に対応できないため、`/m/*` を Basic 認証の対象外にして自前で配信する。ファイル名は UUID で推測不能にする
- **Caddyfile は全生成**：`redirect_build.py --apply` が `/etc/caddy/Caddyfile` を丸ごと生成するため、手編集ではなく `redirects.json` の `proxies` に足す形にした
- **日付・枠は JST 文字列で保持**：UTC 変換をせず、cron の実行日と文字列比較する

## 確認結果

- ローカル起動で登録 → カレンダー表示 → 同枠重複は 400 → 編集（種類変更・画像削除）→ 削除、`/m/<uuid>.png` が `image/png` で取得できることを確認
- `post_scheduled.py 20 --dry-run`：X 本文（画像付き）→ リプ 2 段の返信チェーン → 記録（W007・`postcal[1]`・note_url）→ Threads（note リンク入りの段を除外）の順でコマンド列が出る。予約の無い枠は rc=20
- `post_to_x.py --dry-run` で複数画像と note リンク変換、`post_threads.py --dry-run` で画像＋動画のカルーセル判定を確認
- 生成した Caddyfile が `caddy validate` を通過。配備後 `https://post.usephys.net/` が 401（Basic 認証）、`/m/*` は認証なしで通過、Let's Encrypt 証明書発行済み。既存の転送 6 ホストは変化なし
- systemd `postcal` が enabled・active、`/healthz` 200
- 配備時のつまずき：(1) レコード追加前に `dig` したため VPS 側 ISP リゾルバに NXDOMAIN のネガティブキャッシュ（約 20 分）が残り、追加後も解決できなかった → 待って解消。(2) `.env` への bcrypt ハッシュ追記を `echo "…"`（二重引用符）で案内したため `$2a$14$` がシェルで展開されて壊れた。2 回目は `printf "%s" "$(…)"` でも壊れたため、最終的にハッシュをチャットで受け取り Edit ツールで書き込んだ。**bcrypt ハッシュを `.env` に入れるときはシェルを通さない**
- 実投稿（cron 経由）はまだ未確認。よーんがテスト予約を 1 件登録 → cron 実行後に outputs シートの X 行（what_id・`postcal[id]`）と Threads 行（x_url 付き）、カレンダーの「投稿済み」を確認する

## 今後の課題

- 枠を過ぎて未投稿の行の自動繰り越し（v1 は赤表示のみ。よーんが日付を直す）
- Gmail 受信箱の既存キューをカレンダーに表示する読み取り統合
- `redirect_build.py --apply` は validate 失敗時も Caddyfile を書き換えた状態で止まる（稼働中の Caddy は旧設定で動くが、再起動すると読み込めない）。書き込み前に一時ファイルで validate する方が安全
- 動画の長さ（140 秒）はサーバー側で検査していない（ffprobe なし）
