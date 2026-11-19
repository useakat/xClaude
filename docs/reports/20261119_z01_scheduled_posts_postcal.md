---
title: z01 投稿を Gmail 下書き→予約ファイル + postcal インポーターに変更
date: 2026-11-19
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261119_z01_scheduled_posts_postcal/)

## 背景・動機

z01（X 短文）の投稿キューは Gmail 受信箱だった（スキルが下書きを作る → よーんが自分宛に送信 → 6/12/17/20 時の cron が件名・ラベルで拾って X/Threads に投稿）。よーんの依頼で、**Gmail 下書きをやめ、確定稿を Markdown の「記録」として残しつつ、2026-11-17 に新設した予約カレンダー postcal（`post.usephys.net`）に予約する方式**へ一本化したい。

最大の制約は、**クラウドで走る z01 ルーチンは `post.usephys.net` に直接つなげない**こと（エージェントプロキシが `post.usephys.net:443` を 403 policy denial で拒否。postcal の登録口は VPS 上の Basic 認証付き Web フォームのみ、DB も VPS 上）。クラウドから到達できるのは GitHub(git) と Gmail(MCP) だけなので、**git 受け渡し + VPS 側インポーター**の構成にした。

もう一つ、postcal 経由だと `record_output.py` に渡る neta-id が `postcal[予約id]` になり、**SS1 の「短文最終使用日」が更新されない**（元シート参照 `noteNeta[..]` と形が違い、STEP 2 の 180 日フィルタが効かなくなる）問題があったため、予約に出所（neta_id）を持たせて同時に解消した。

## 実施内容

- **予約ファイル方式（案 A: git 受け渡し + VPS インポーター）**：z01 フローは Gmail 下書きを作らず、確定稿を `outputs/scheduled-posts/z01/<日時>_<topic>.md`（front-matter + `## 投稿文` + `## セルフリプ` + `## 記録`）に書いて master へ push する。`## 記録` に従来 Gmail 下書きに入れていたソース・候補・チェック証跡を全部残す。
- **新規 `scripts/postcal_import.py`（VPS で systemd timer 実行）**：`git pull --ff-only` → 予約ファイルを走査 → front-matter の `uid` をキーに `postcal.db` へ upsert（新規は週間短文パターンの最寄り空き枠へ `db.create`、queued は `db.update`、posted は不可）。取込状態は `postcal/data/import_state.json`（git 管理外）で管理。失敗は `send_gmail.sh` 通知。
- **週間短文枠（よーん決定 2026-11-19）**：1 短文の日は 6:00、2 短文の日は 6:00→17:00。月[6] 火[6,17] 水[6] 木[6,17] 金[なし] 土[6] 日[6]。枠の割当は DB が見えるインポーター側が「今日以降の最も近い空き枠」で行う（クラウド側は枠を指定しない）。
- **SS1 短文最終使用日の更新を復活**：`postcal/db.py` の posts に `neta_id` 列を追加（既存 DB は `connect()` 時の `ALTER TABLE` で後付け）。インポーターが front-matter の `source`（`noteNeta[..]`/`newsTopics[..]` の形のみ）を予約の neta_id に保存し、`post_scheduled.py` が投稿時に `--neta-id` として渡す（無ければ `postcal[id]` にフォールバック）。
- **更新ルールの変更**：旧「1 投稿 1 下書き・作成後は一切触らない」を、「投稿実行（postcal status=posted）までは同じ uid のファイルを上書き更新してよい（インポーターが既存予約を更新・枠は動かさない）」に変更。
- **配備**：`scripts/postcal_install.sh` に `postcal-import.service`/`.timer`（10 分ごと）の設置・有効化を追記。`docs/workflows/x-auto-post.md` に新経路を追記。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/postcal_import.py` | 新規。予約ファイル → postcal.db の upsert、週間短文枠の最寄り空き枠探索、state 管理、エラー通知 |
| `postcal/postcal-import.service` / `postcal/postcal-import.timer` | 新規。10 分ごとにインポーターを実行する systemd ユニット |
| `postcal/db.py` | posts に `neta_id` 列を追加（既存 DB は connect 時の ALTER で後付け）、create/update が neta_id を扱う |
| `postcal/app.py` | Web 編集時に既存 neta_id を保つ（フォームに項目は無い） |
| `scripts/post_scheduled.py` | 投稿時 `--neta-id` に予約の neta_id（無ければ `postcal[id]`） |
| `scripts/postcal_install.sh` | `postcal-import.timer` の設置・有効化を追加 |
| `projects/z01/spec.md` | Output/Naming/STEP6/STEP7/その他/Verification を予約ファイル方式に改訂、更新ルール変更、SS1 更新の仕組みを追記 |
| `docs/workflows/x-auto-post.md` | z01 の予約ファイル → インポーター → カレンダー → cron 経路を追記 |

## 設計判断

- **案 A（git 受け渡し）を採用した理由**：クラウド環境は `post.usephys.net` を 403 で弾かれ直接 POST できない。git/GitHub は通る。秘密情報（Basic 認証資格）をクラウド無人フローに置かずに済み、「アプリに X/Threads の秘密を渡さない」postcal の方針とも整合する。直接 HTTP POST（案 B）はネットワーク許可の追加と資格情報の受け渡しが要るため見送った。
- **枠割当を VPS 側に置く理由**：クラウドは postcal.db を見られず空き枠を判断できない。DB が見えるインポーターが週間パターンと `slot_taken` を突き合わせて割り当てる。
- **neta_id 列の追加**：予約 id（postcal[id]）では元シート行に紐付かず SS1 を更新できない。front-matter の source を予約に載せて投稿時に渡すのが最小の改修で、outputs の neta_id も旧来どおり `noteNeta[..]` に戻り追跡性も回復する。
- **インポーターの実行は systemd timer**：既存の `postcal.service` と同じ systemd 運用に揃え、「入れたら勝手に回る」ようにした（10 分ごと）。git push 契機（Actions/webhook）は設定が重いので見送り。

## 確認結果

ローカル（クラウド）で検証：

- サンプル予約ファイルのパース（front-matter・`## 投稿文`・`## セルフリプ`「なし」）、週間短文枠の選択（木曜 09:41 JST は 6 時経過済みのため 17 時枠を選択）を `--dry-run` で確認。
- fresh DB への取込で、source=`noteNeta[143]` → 予約 neta_id に保存、source=ユーザー指定（非シート）→ neta_id 空。枠割当は #1=木17時・#2=土6時（金は短文枠なしで飛ばす）を確認。
- `post_scheduled.py --dry-run`：#1 は `--neta-id noteNeta[143]`、#2 は `--neta-id postcal[2]`（フォールバック）を渡すことを確認。
- 旧スキーマ DB（neta_id なし）→ `connect()` の `ALTER TABLE` で列追加、既存行は空、create/update 動作を確認。
- 全変更ファイルの `py_compile` / `bash -n` OK。

## VPS 配備と初回取込の結果（2026-11-19 追記）

よーんが VPS で `git pull` → `sudo bash scripts/postcal_install.sh` を実行し、タイマー経由で初回取込まで進んだ。

- **初回取込は成功**：11:17 に `postcal-import` が動き、氷下水の予約ファイルを `登録 #5（2026-11-19 17時 / short→z01）` として登録した（#5 はカレンダーに既存の予約があったため。空いていた 17 時枠に入り、既存予約は上書きしていない）。以降の実行は `集計: skip=1`（取込済み・変更なし）で、タイマーは回っている。
- **`git pull --ff-only` が拒否される問題が発生**：「detected dubious ownership in repository at '/root/xClaude'」で失敗し、`send_gmail.sh` の失敗通知メールが届いた。
  - 原因：`/root/xClaude` 本体の所有者が VPS に存在しない uid（`stat` の表示は `UNKNOWN:UNKNOWN`、`.git` は `root:root`）になっており、root で動く git が「他人のリポジトリ」と判定した（git 2.35.2 以降の safe.directory チェック）。タイマーのユニットは `User=` 未指定（`systemctl show` で確認）なので root で動いている。
  - 対処：フォルダ本体だけを root の持ち物に戻す（`chown root:root /root/xClaude`、非再帰）。代替は `git config --system --add safe.directory /root/xClaude`（`--global` は systemd 経由で HOME が取れず効かない場合があるため `--system`）。ログ上、11:37 の実行に pull 失敗の記録があり、11:40 の実行からは失敗の記録が出ていない（修正の時刻はログからの推定）。
  - **この間は pull が失敗するため、クラウドから push した予約ファイルが VPS に届かない**。気付かないと新しい予約が取り込まれない状態になる点が実害。
- 検証できていないこと：17 時の cron による実投稿（X への投稿・カレンダーの「投稿済み」・outputs 記録）は未確認。

## 今後の課題

- **cron 経由の実投稿の確認**：今日 17 時の枠で予約 #5 が投稿されるかを確認する（カレンダーが「投稿済み」になる・X に載る・失敗時は `【postcal】投稿失敗 #5` のメールが届く）。postcal の予約を cron が実際に拾うのは今回が初めての想定。#5 は source が「ユーザー指定」なので neta_id は `postcal[5]` になり SS1 は更新されない（正）。**SS1「短文最終使用日」の更新（neta_id が `noteNeta[..]` のとき）は、次にシート参照つきの予約が投稿されたときに確認する**。
- **失敗通知の重複抑制**：`postcal_import.py` は失敗のたびに通知するため、pull 失敗のような継続エラーだと 10 分おきに同じメールが届く（今回実際に発生）。「同じエラーは 1 時間に 1 回」にするなどの抑制を入れる（未実装）。
- **予約方式での「無言の手直し」差分収集**（check-yohn 自己改善の教師データ）は、Gmail 下書き時代の仕組みが使えないため follow-up。予約ファイルの git 履歴（初版 Claude 原文）との差分で代替できる見込み。
- thoughts 枠は 2026-11-18 に廃止済みのため対象外。今回は z01 のみ差し替え（W001/W003 等は従来の Gmail 下書きのまま）。
