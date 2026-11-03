---
title: 宇宙ダイジェスト（毎朝 7 時のメール）
description: 探査機・宇宙探査・宇宙物理・宇宙開発・素粒子物理の新着（プレスリリース・ニュース・論文）を毎朝まとめてメールする仕組み
---

毎朝 06:45 JST にローカル cron が動き、約 07:00 に `useakat@gmail.com` へ「【宇宙ダイジェスト】」メールが届く。

## 流れ

```
06:45 cron  scripts/run_space_digest.sh
  ① python3 scripts/space_digest_fetch.py      RSS/Atom と arXiv API から新着を集め、既読を除いて候補ファイルを書く（約 5 秒）
  ② claude -p --model opus "/space-digest …"   候補を読んで選別・日本語要約・★ネタ候補付け → 本文ファイルを書く（数分）
  ③ bash scripts/send_gmail.sh                  本文を送る
```

| 段階 | 入力 | 出力 |
|---|---|---|
| ① 収集 | `scripts/space_digest_sources.json`、`logs/space_digest_state.json`（既読） | `logs/space_digest/YYYY-MM-DD_candidates.md` |
| ② 要約 | 候補ファイル、`brand.md`、`plan.md` | `logs/space_digest/YYYY-MM-DD_digest.txt` |
| ③ 送信 | 本文ファイル | メール（件名 `【宇宙ダイジェスト】YYYY-MM-DD（曜）ニュース n・プレス n・論文 n`） |

収集は決定的な Python、判断（選別・要約・★）だけ Claude が行う。送信はスキルではなくラッパーが行う（本文ファイルが無ければ送らず、失敗がログに残る）。X API も Claude API も呼ばない（`claude -p` はローカルの Claude Code）。

## 候補の絞り方（①）

- **時間窓**：公開日時が直近 48 時間（`since_hours`）
- **既読**：`logs/space_digest_state.json` にある URL / arXiv ID は出さない。候補に載せたものは（Claude が採用しなくても）既読にする。30 日で間引く
- **除外語**（`exclude_titles`）：タイトルに deal / review / podcast / APOD など消費者向け・定型コンテンツの語があれば全種別で落とす。同じタイトルの重複も落とす
- **キーワード**：`keywords_strong`（探査機・ミッション・実験名、探査機・望遠鏡など。3 点）と `keywords`（一般語。1 点）
  - `keyword_filter: true` のソース（Nature・Science・Phys.org Physics・Physics World）は 1 点以上の項目だけ残す
  - arXiv はカテゴリ astro-ph.EP/IM/HE/SR/GA/CO・hep-ex/ph・physics.space-ph/ins-det の新着 300 件から、窓内 → キーワード一致 → スコア順に上位 25 件
- **上限**：ソースごと 10 件（Space.com は 12）、全体 60 件。超えたらニュースから削る
- 候補が 0 件なら候補ファイルに `NO_CANDIDATES` と書き、ラッパーが「新着なし」のメールを送る（毎日 1 通は届くので動作確認を兼ねる）

## メールの形（②）

```
【宇宙ダイジェスト】2026-11-01（土）
ニュース 6・プレスリリース 4・論文 5（候補 38 件から）

■ ★ネタ候補           発信軸（探査機の執念・直感を裏切る驚き）に合うもの最大 3 件。理由を 1 行
■ ニュース・配信       最大 8 件
■ プレスリリース       最大 6 件
■ 論文                 最大 5 件（arXiv と Nature/Science 合わせて）＋ その他の論文候補のタイトル最大 10 件
```

各項目は 2〜3 行の日本語要約と URL。要約は候補ファイルの範囲で書く（★ の 3 件だけ WebFetch で元記事を読んでよい）。★ はシートに自動登録しない。よーんが `/add-neta` で登録する。

## ソース（2026-11-01 時点）

| 種別 | 英語 | 日本語 |
|---|---|---|
| プレスリリース | NASA News Releases、NASA Science、NASA JPL News、ESA Space Science、ESA Top News、ESO、Fermilab | JAXA プレスリリース、国立天文台、KEK |
| ニュース・配信 | Space.com、Universe Today、Phys.org Space、Phys.org Physics※、SpaceNews、Quanta Magazine Physics、CERN Courier、Physics World※、Science News※ | sorae、AstroArts |
| 論文 | arXiv API、Nature※、Nature Astronomy、Nature Physics※、Science※ | — |

※ キーワード絞り込みあり。CERN（home.cern）・ISAS・理研・Webb/Hubble 単独・マイナビは RSS が無いか廃止されていたため入れていない（ISAS は JAXA プレスリリース、Webb/Hubble は NASA Science に含まれる）。

## 運用

- **ソースを足す／外す**：`scripts/space_digest_sources.json` の `sources` に `{name, url, kind, lang, max?, keyword_filter?}` を追加・削除。`python3 scripts/space_digest_fetch.py --dry-run --since-hours 72` で取得できるか確認する
- **キーワードを足す**：同ファイルの `keywords_strong`（固有名詞・ミッション名）か `keywords`（一般語）
- **件数を変える**：`per_source_max` / `max_total` / `arxiv.max_keep`（収集側）、SKILL.md の上限（メール側）
- **止める**：`crontab -e` で `run_space_digest.sh` の行をコメントアウト
- **手動で試す**：`bash scripts/run_space_digest.sh --dry-run`（状態を更新せず、メールも送らない。候補と本文は `logs/space_digest/` に残る）
- **ログ**：`logs/space_digest.log`（取得状況・claude -p の出力・送信結果）

## 失敗時

| 状況 | 動作 |
|---|---|
| 1 ソースの取得失敗 | 警告してほかのソースで続行。候補ファイル末尾の「取得状況」に残る |
| 全ソース失敗 | 「収集失敗」メールを送って終了（rc 1） |
| claude -p が本文を書けない（15 分超過など） | 「要約失敗」メールを送って終了（rc 1）。候補ファイルは残る |
| 前回がまだ動いている | `flock` で中止 |
