---
title: X インプ通知の条件変更（2 時間以内に 1,500 インプ）と Threads views 通知の新設 — セッション履歴
date: 2026-10-11
sidebar:
  hidden: true
---

# セッション履歴

> 2026-10-11 のセッション作業ログ。

← [報告書へ戻る](../../reports/20261011_imp_alert_threshold_threads_views_alert/)

---

## よーん *(16:42 JST)*

Xポストのインプ通知を、2時間以内に1500インプで通知に変更して

### Claude *(16:42 JST)*

X インプ通知のスクリプトを確認します。

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

X インプ通知を「投稿から 2 時間以内に 1,500 インプ」に変更しました。

- `scripts/x_imp_alert.py` の閾値を 1,000 → 1,500、時間窓を 3 → 2 時間にしました。cron の間隔（30 分おき）はそのままです。
- dry-run で正常動作を確認しました（現在、時間窓内の投稿は 0 件）。
- コミット `dcf1319` を master に push しました。

配布用の GAS 版（`scripts/gas/`）は初期値 1,000 / 3 時間のままにしてあります。こちらも揃える場合は言ってください。

---

## よーん *(16:44 JST)*

threads についても同じような通知ができる？

### Claude *(16:44 JST)*

*[ツール: `Bash`]*

できます。必要な部品はすべて既存のもので揃っています。

**使える仕組み**
- Threads Graph API の `/{user_id}/threads` で自分の投稿一覧（投稿日時付き）が取れ、`/{media_id}/insights?metric=views` で投稿ごとの views が取れます。`fetch_threads_posts.py` が毎朝これと同じ呼び出しをしています。
- トークン（`gcp/threads_token.json`）と Gmail 送信（`send_gmail.sh`）は X 版の `x_imp_alert.py` と共用できます。
- Threads API は無料で、X のような従量課金がありません。30 分おきに回しても費用は増えません。

**X 版との違い**
- 投稿の表示回数は X の「インプ」ではなく `views` です。Threads の views は X のインプより伸びやすいので（10/9 のニューホライズンズは 20,952）、閾値は X と同じ 1,500 でよいか、別の値にするか決める必要があります。
- 1 投稿ごとに insights を 1 回呼ぶので、時間窓内の投稿数ぶんだけ API 呼び出しが増えますが、数件なので問題ありません。
- 親投稿URL のあるリプライ行は除外します。再認可（`threads_read_replies`）が無くても、一覧 API はトップ投稿しか返さないので今の状態で動きます。

**作る場合の形**
- `scripts/threads_views_alert.py` を新設し、`run_threads_views_alert.sh` を X 版と同じ `*/30 * * * *` で cron に追加。通知済み ID は `logs/threads_views_alert_state.json` に保存して 1 投稿 1 回。
- メールの件名・本文は X 版と同じ形式で、「Threads」と分かる表記にします。

作るなら、閾値と時間窓（X と同じ 2 時間以内に 1,500 views でよいか）を教えてください。

---

## よーん *(16:46 JST)*

まずはXと同じ閾値でやってみよう

### Claude *(16:46 JST)*

X 版をもとに Threads 用スクリプトを作ります。まず X 版の全体を読みます。

*[ツール: `Bash`, `Bash`]*

判定ロジックが動いたので、cron に追加してコミットします。

*[ツール: `Bash`]*

Threads 版の通知を作り、cron に載せました。条件は X と同じ「投稿から 2 時間以内に 1,500 views」です。

**追加したもの**
- `scripts/threads_views_alert.py`：Threads API で時間窓内のトップ投稿を取り、投稿ごとに views を確認して閾値到達でメール通知。1 投稿 1 回で、通知済みは `logs/threads_views_alert_state.json` に 7 日間保持します。
- `scripts/run_threads_views_alert.sh`：多重起動防止付きの cron 用ラッパー。ログは `logs/threads_views_alert.log` です。
- crontab に 30 分おきの実行を追加しました（X 版と同じ間隔）。

**動作確認**
- dry-run で、時間窓を 48 時間・閾値 100 に広げると 10/8〜10/9 の 4 投稿を拾い、件名と本文が X 版と同じ形式で組み立てられることを確認しました。本番条件では現在 0 件です。
- 実際のメール送信は、次に該当する投稿が出たときが初回になります。

**補足**
- Threads の一覧 API はリプライを返さないので、セルフリプが対象に入ることはありません。
- 閾値を変えるときは `THRESHOLD` と `WINDOW_HOURS` を書き換えるだけです。

コミット `0912f11` を master に push しました。X の閾値変更と合わせて記録する場合は `/record` でどうぞ。

---
