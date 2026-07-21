---
title: X投稿をThreadsにも自動転載し、下書き投稿を「X投稿が無い時だけ」のフォールバックに変更
date: 2026-07-21
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260721_x_to_threads_mirror_integration/)

## 背景・動機

Threads は「過去X投稿を転載する下書き（【threads投稿】メール）」を `run_threads_post.sh`（6/17/20時）で投稿していた。一方 X には毎日 onepoint(6時)/question(12時)/xlong(17時)/xshort(21時) を投稿しており、両者が別系統で走るため Threads に「新規X投稿」が載らなかった。

これを統合し、**Xに投稿したポストをそのまま Threads にも転載**する。よーんの要望は「4つのX cron 全部を転載対象にする」「X投稿して Threads に転載できた回は下書き投稿を行わない」「X投稿が一切無かった回だけ下書き投稿をフォールバック実行する」。

技術的な鍵は、Threads API が公開URL（image_url）しか受け付けない点。X投稿はローカル画像（Gmail添付）を上げているため、投稿直後に **pbs.twimg.com** の公開URLを syndication API（認証不要）から取得して Threads に渡す。

## 実施内容

- **`scripts/fetch_tweet_media.py` を新規作成**: tweet_id を引数に、`cdn.syndication.twimg.com/tweet-result` から `mediaDetails[].type=="photo"` の `media_url_https` を空白区切りで出力。投稿直後のインデックス遅延に備え6回×3秒リトライ。画像なしは即時空出力。IPv4固定パッチ付き。
- **`scripts/post_from_email.sh` に Threads 転載ブロックを追加**: 環境変数 `MIRROR_THREADS=1` のときだけ、X投稿成功＋record の直後に転載する。`fetch_tweet_media.py` で画像URL取得 → `post_threads.py --text/--image-url/--reply-text` → `PERMALINK` 抽出 → `record_output.py --x-url` で Threads 行を記録。**非致命**（転載失敗でも警告ログのみ、exit code は変えない＝ラッパーは「X投稿あり」と判断）。dry-run にも転載プレビューを追加。
- **X 4ラッパーを改修**: `export MIRROR_THREADS=1` を追加し、rc をフォールバック連鎖で受け継ぎ、**最終 rc=20（X投稿ゼロ）のときだけ `run_threads_post.sh`（下書き投稿）をフォールバック実行**。`run_xshort_post.sh` は `exec` をやめて rc 受けに変更。
- **crontab**: 独立していた `run_threads_post.sh`（6/17/20時）の行を削除。`run_threads_draft.sh`（8時・フォールバック用下書きプール）、`run_threads_fetch.sh`（5時・メトリクス）、月次 token_refresh、X 4本は維持。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/fetch_tweet_media.py` | 新規。tweet_id→pbs.twimg.com 画像URL（syndication・IPv4・リトライ） |
| `scripts/post_from_email.sh` | `MIRROR_THREADS=1` 時にX投稿後 Threads 転載＋x_url記録（非致命）。dry-run プレビュー追加 |
| `scripts/run_xonepoint_post.sh` / `run_question_post.sh` / `run_xlong_post.sh` / `run_xshort_post.sh` | `MIRROR_THREADS` export＋X投稿ゼロ時に `run_threads_post.sh` フォールバック |
| crontab | 独立 `run_threads_post.sh`（6/17/20時）行を削除 |

## 設計判断

- **転載を post_from_email.sh に一元化**: 全X cron が共用するため、ここに入れれば4種すべてが自動で転載対象になる。ラッパー側は `MIRROR_THREADS` の有無だけ制御。
- **画像は pbs.twimg.com（syndication）**: X投稿済みの同じ画像がそこにホストされ、Threads で実績のあるURL形式。Drive公開URL案より確実・軽量。取得失敗時はテキストのみ転載。
- **転載は非致命**: X投稿の成否とデカップリング。転載が失敗しても X は成功済みで、ラッパーはフォールバックしない（＝二重投稿を防ぐ）。
- **下書き投稿をフォールバック化**: 「Xに新規投稿があればそれをThreadsに、無ければ過去投稿の下書きを」という優先順位を、rc=20 連鎖の末尾に `run_threads_post.sh` を置くことで表現。

## 確認結果

- 全スクリプト `bash -n` / `ast.parse` 構文OK。
- `fetch_tweet_media.py 2078715634469478471` → pbs URL 4件を空白区切りで出力。
- 転載パイプライン（`fetch_tweet_media` → `post_threads.py --dry-run --image-url ... --reply-text ...`）が「本文1件＋リプ1件／カルーセル4枚」と正しく連結することを確認。
- crontab から独立 `run_threads_post.sh` 行が消え、X4本＋fetch/token/draft が維持されていることを確認。
- 実X投稿を伴うエンドツーエンド検証は、INBOX が空・かつ X投稿は cron 専用のため次回の実 cron（翌朝6時 onepoint〜）に委ねる。

## 留意点 / 今後

- **下書きプールの消費**: `run_threads_draft.sh`（8時・6件）は X投稿一覧 AH列に「転載済み」マークを付けるが、下書きは今後フォールバック時しか投稿されない。X投稿がほぼ毎回ある想定だと、未投稿のまま候補が「転載済み」化して減っていく。運用を見て下書き作成本数の削減 or 一時停止を別途検討。
- syndication のインデックス遅延で稀に画像が取れない場合はテキストのみ転載＋警告ログ。
- 動画つきX投稿は photo のみ転載（動画は対象外）。
