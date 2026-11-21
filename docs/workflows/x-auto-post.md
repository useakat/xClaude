---
title: X 自動投稿フロー
description: cron → Gmail → X 投稿 の自動化フロー解説
---

## フロー全体図

```
各プロジェクト（W003 / W006 / W001 / z01 / W004 / W007）が Gmail 下書きを作る
    ↓
よーんが下書きを確認・手直しし、自分宛に送信（受信箱に届く）
    ↓（任意）投稿時間帯ラベル（6時投稿 / 12時投稿 / 17時投稿 / 20時投稿）を付ける
    ↓
cron の 4 枠（6:00 / 12:00 / 17:00 / 20:00 JST）が受信箱を検索
    ↓
[投稿文] タグを抽出 → X に投稿（[リプ] があればセルフリプ、Threads にも転載）
    ↓
投稿済みラベルを付けて受信箱から外す → outputs シートに記録
```

## cron の 4 枠と件名

| 時刻 | ラッパー | 本命の件名 | howID | 本命が無いとき |
|---|---|---|---|---|
| 6:00 | `run_xonepoint_post.sh` | 【ワンポイント解説】 | W003 | 【X短文投稿】→ Threads 下書き |
| 12:00 | `run_question_post.sh` | 【質問回答】 | W006 | 【X短文投稿】→ Threads 下書き |
| 17:00 | `run_xlong_post.sh` | 【X長文】 | W001 | 【X短文投稿】→ Threads 下書き |
| 20:00 | `run_xshort_post.sh` | 【自己開示】→【note販促】→【X短文投稿】 | W004 → W007 → z01 | Threads 下書き |
| （ラベル付きのみ） | `post_by_label.sh` | 【自己開示】・【note販促】 | W004・W007 | — |

1 枠で投稿するのは 1 件だけ（古いメールから）。投稿に失敗したとき（rc=1）はフォールバックしない。

## 投稿時間帯ラベル（2026-10-23〜）

メールごとに投稿する枠を指定できる。Gmail のラベル `6時投稿` `12時投稿` `17時投稿` `20時投稿` を、下書きを送る前（または受信箱に届いた後）に付ける。

- **ラベル付きのメールは、件名に関わらずその枠の cron が先に拾う**。例：【X長文】に `20時投稿` を付けると 17:00 では触られず、20:00 に投稿される。howID・ログ・記録は件名で決まる
- 複数付ければ、どちらの枠でも可（先に来た枠で投稿される）
- **ラベルが無いメールは従来どおり**、件名の枠で投稿される
- 他の枠のラベルだけが付いたメールは、その枠まで受信箱に残る

各枠の処理順：

1. `scripts/post_scheduled.py <時>` — **postcal（予約カレンダー `https://post.usephys.net/`）** にその日・その枠の予約があれば最優先で投稿する（画像最大 4 枚または動画 1 本、セルフリプは `=====` 区切りで返信チェーン、Threads 転載、outputs 記録まで）。予約が無ければ rc=20 で次へ（2026-11-15）
2. `scripts/post_by_label.sh <時>` — `label:<時>時投稿 in:inbox -label:投稿済み` を件名 6 種（ワンポイント解説 → 質問回答 → X長文 → note販促 → X短文投稿 → 自己開示）の順に探し、最初の 1 件を投稿する
3. 無ければ従来の件名検索。`post_from_email.sh` は `--label` 無しのとき、時刻ラベル付きのメールをすべて除外して探す

## z01 短文は予約ファイル経由（2026-11-19〜）

z01（短文）は **Gmail 下書きを作らず、予約ファイル → postcal** に一本化した（`projects/z01/spec.md` STEP 6）。

```
z01 フローが確定稿を outputs/scheduled-posts/z01/<日時>_<topic>.md に書く（## 投稿文＋## セルフリプ＋## 記録、front-matter に uid）
    ↓ git push（master）
VPS の scripts/postcal_import.py（systemd timer postcal-import.timer・10 分ごと）が git pull → 読み取り
    ↓ 下書き（status=draft）として db.create()（仮の日時＝今日以降の最も近い空き短文枠。uid で upsert）
postcal.db に登録 → post.usephys.net のカレンダーに「下書き（未予約）」と表示（この時点では投稿されない）
    ↓ よーんが画面で本文を確認・修正し「投稿予約」を押す（draft → queued。枠が過去・埋まっていればエラー→日時を直す）
    ↓ 既存の 4 枠 cron（post_scheduled.py <枠>。queued しか拾わない）がその枠で X / Threads に投稿
```

- 週間短文枠（よーん決定 2026-11-19）：1 短文の日は 6:00、2 短文の日は 6:00→17:00。月[6] 火[6,17] 水[6] 木[6,17] 金[なし] 土[6] 日[6]。仮の日時の割当は `postcal_import.py` が行う（z01 フローは枠を指定しない）。下書きは枠を占有しない（他の下書きの仮枠とは重ならないよう選ぶ）。
- **下書き方式（2026-11-21〜）**：確認前の本文が自動投稿されないよう、取り込みは必ず下書き。予約ファイルを上書き更新して再 push してよいのは下書きの間だけで、**画面で編集した下書きは上書きされない**（画面の編集が正）。「投稿予約」後（queued）・投稿済みはファイルを変えても反映されない。「下書きに戻す」ボタンで queued → draft に戻せる。
- 画面（`/new`）から手で登録した予約は従来どおり即 queued（よーん自身が書いたもの）。

## リライト（writer-xrewrite）も予約ファイル経由（2026-11-21〜）

リライトも **Gmail 下書き（【リライト】）をやめ、予約ファイル → postcal の下書き → 「投稿予約」** に変更した（`.claude/skills/writer-xrewrite/SKILL.md` STEP 7）。

- 予約ファイル: `outputs/scheduled-posts/rewrite/<日時>_<topic>.md`。front-matter は `kind: rewrite_short|rewrite_onepoint|rewrite_long`（= what_id `z01r`/`W003r`/`W001r`）、`source: "rewrite[<元ツイートID>]"`。メモ・チェック証跡・不採用案は `## 記録` に入れる。
- 仮の日時は**毎日 20:00 の最寄りの空き枠**（従来の 20 時枠運用を踏襲。インポーターの `REWRITE_SLOTS`）。別の日・時刻にしたいときは、画面で日時を直してから「投稿予約」を押す。
- `source` の `rewrite[ID]` は予約の `neta_id` に引き継がれ、投稿時に outputs の neta_id 列へ入る（`rewrite_pool.py` の「リライト済み」判定がこれを見る）。
- 20 時枠の cron（`run_xshort_post.sh`）は postcal の予約を最優先で拾う。**Gmail の【リライト】の経路は廃止した**（`run_xshort_post.sh` と `post_by_label.sh` から件名【リライト】の検索を削除）。リライトは postcal 経由のみ。
- 取込状態は `postcal/data/import_state.json`（git 管理外）で uid→予約 id を管理。導入手順は `scripts/postcal_install.sh`（`postcal-import.timer` を設置・有効化）。

## Gmail → X 投稿の仕組み

`scripts/post_from_email.sh` が、件名キーワードで受信箱の未処理メール（`in:inbox -label:投稿済み`）を検索し、本文の `[投稿文]...[/投稿文]` タグ内のテキストを X に投稿する。添付画像があれば画像付き、`[リプ]` があればセルフリプ、`[note_url]` は outputs シートに記録する。

```bash
bash scripts/post_from_email.sh "【ワンポイント解説】" W003 x_post_xonepoint.log
bash scripts/post_from_email.sh --label 17時投稿 "【X長文】" W001 x_post_xlong.log
bash scripts/post_from_email.sh --dry-run "【X短文投稿】" z01 x_post_short.log   # 投稿もラベル付与もしない
bash scripts/post_by_label.sh --dry-run 20
```

終了コード：0 ＝ 投稿成功、20 ＝ 投稿対象なし（フォールバックの合図）、1 ＝ 投稿失敗。

## 投稿済み判定

投稿後、対象メールに `投稿済み` ラベル（Label_103）を付けて受信箱から外す。検索が `in:inbox -label:投稿済み` なので、次回以降は拾われない。`[投稿文]` が無い／空のメールもラベルだけ付けて飛ばす。
