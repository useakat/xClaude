---
title: 競合投稿の毎日メール（X競合分析シート）
description: 競合アカウントの投稿を 1 か月分シートに記録し、毎朝 1 件ずつ古い順にメールで読む仕組み
---

競合アカウントの投稿を「書いた順に 1 日 1 件」読んで、構成や切り口を観察するための仕組み。2026-11-01 に @ossanworld（2026-05 の 1 か月分）で開始。

## 流れ

```
（1 回）python3 scripts/fetch_x_user_posts.py --username ossanworld --start 2026-05-01 --end 2026-05-31
          X API で期間内の投稿を取得 → 「X競合分析」に新シート "ossanworld 2026-05" を作成（古い順）
（毎日 07:15）cron  scripts/run_x_competitor_daily_mail.sh
          未送信で最古の投稿を 1 件メール → N 列「送信済み」に送信日を記入
```

| 段階 | 入力 | 出力 |
|---|---|---|
| 取得 | X API（`.env` の `X_BEARER_TOKEN`、従量課金） | シート `<username> YYYY-MM`、生データ `logs/x_user_posts/*.json` |
| メール | シート | メール 1 通（件名 `【競合投稿】@ossanworld 2026-05-01（1/154）`）、N 列に送信日 |

## シートの形

[X競合分析](https://docs.google.com/spreadsheets/d/1OKQ6zoryoDAQvvKu5kWr9bJD20dO-zfnfrkufLl00tw/edit) の 1 アカウント・1 期間 ＝ 1 シート。galileo_fun 2026-08 シートの列に URL・本文全文・送信済みを足した 14 列。

| 列 | 内容 |
|---|---|
| A〜C | 投稿日時（JST）、ツイートID、URL |
| D〜I | IMP、いいね、RT、リプライ、引用RT、ブックマーク（取得時点の値） |
| J | ツリー：単独／ツリー先頭／ツリー続き（自分の投稿への返信） |
| K | 会話ID（ツリー先頭と続きを結ぶ） |
| L〜M | 冒頭 1 文、本文（全文。長文投稿は note_tweet の全文） |
| N | 送信済み（メールした日。空＝未送信） |

**入れないもの**：リポスト、他人へのリプライ、本文が「@相手」で始まる投稿（他人との会話の中の自己返信。参照先が消えた返信は API が返信扱いにしないため本文で判定）。

## メール

- 1 通 ＝ 単独 1 件、またはツリー先頭＋続き全部（続きは「── 続き 2/5 ──」で区切る）。本文は全文、反応数と URL 付き
- 古い順。件名の `（n/N）` は単独・ツリー先頭の通し番号
- 全件送り終えたら「全 N 件を送り終えました」を 1 回だけ送り、以後は何もしない（`logs/x_competitor_mail_state.json`）

## 運用

- **次のアカウント・期間に切り替える**：`fetch_x_user_posts.py` で新シートを作り、`run_x_competitor_daily_mail.sh` 冒頭の `SHEET` を書き換える
- **送り直す**：N 列を空にすれば再び対象になる
- **取り直す**：`--overwrite` で同名シートを書き直せる（送信済み列も消える）。X API を呼ばずに `--from-json logs/x_user_posts/<file>.json` で作り直せる
- **試す**：`bash scripts/run_x_competitor_daily_mail.sh --dry-run`（送らず・書かず、本文を標準出力に出す）
- **止める**：`crontab -e` で `run_x_competitor_daily_mail.sh` の行をコメントアウト
- ログ：`logs/x_competitor_mail.log`
