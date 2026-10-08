---
title: 転送サイトのホスト直下を自動転送せず案内ページにする（スキャナ由来の note 偽到達の遮断）
date: 2026-10-08
tags: [infra, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261008_redirect_root_landing/)

## 背景・動機

10/5〜10/7 の note 導線を分析したところ、note 流入元シートの「X bio」列が 11・4・3、転送先のボイジャー記事の PV が 15・5・5 と毎日記録されているのに、Caddy ログには bio に貼ってある `usephys.net/note` への人のアクセスが1件も無かった。

原因は、ホスト直下 `usephys.net/` に来るスキャナだった。証明書の透明性ログでホスト名を知ったスキャナは1日 100〜200 件（Tencent 系 IP の zh-CN iPhone、Scaleway / GCP の headless Chrome など）が直下に来る。10/4 の設計で「直下 `/` のビーコン（`_root`）は人のクリックに数えない」としてクリック集計からは除外済みだったが、**転送ページを返す動作自体は残っていた**ため、JS を実行する型のスキャナが `location.replace()` で note まで到達し、参照元 `usephys.net` 付きの PV として note 側に数えられていた。1日あたりの `_root` ビーコン数（16・9・8）と note の「X bio」（11・4・3）が対応しており、ボイジャー記事の PV はこの期間すべてスキャナだった。

クリック側（bioクリック シート）は正しく 0 だったが、note 側の流入元・記事 PV が汚れ続けると、月次突合や記事ごとの評価が狂う。直下では転送しないようにして、ノイズの発生源を止めることにした。

## 実施内容

- `redirect/landing.html` を新規作成。名前・一言と note / X / Threads へのリンクだけの案内ページ。自動転送（meta refresh / `location.replace()`）もビーコンも無い
- `scripts/redirect_build.py` を変更
  - ホスト直下の `index.html` を転送ページ（`template.html`、キー `_root`）ではなく案内ページにした。`try_files … /index.html` のフォールバックにより、不明パス（`/.env` などスキャナが叩くパス）も案内ページになる
  - クローラ向け 302 の matcher を `@crawler { header_regexp …; not path / /index.html }` に変え、直下にはクローラにも 302 を返さない（bio に貼る URL はパス付きなので、直下に OG カードは不要）
  - docstring を新しい動作に合わせて更新
- `redirect/redirects.json` の `_comment` を更新（直下と不明キーは案内ページ。host の `target` はクローラ向け 302 と map の既定値にだけ使う）
- `--apply` で全 7 ホストに反映し、Caddy を reload

パス付きの動作は変えていない。`usephys.net/note`、`threads.usephys.net/note`、`xpost.usephys.net/<記事ID>/<投稿キー>`、`tpost.usephys.net/…` は従来どおり転送ページ＋ビーコンで、クローラには 302 を返す。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `redirect/landing.html` | 新規。ホスト直下・不明パス用の案内ページ（転送・ビーコン無し） |
| `scripts/redirect_build.py` | 直下の `index.html` を案内ページに。クローラ matcher に `not path / /index.html` を追加。docstring 更新 |
| `redirect/redirects.json` | `_comment` を更新 |
| `/var/www/redirect/*/index.html`・`/etc/caddy/Caddyfile`（生成物、git 管理外） | `--apply` で再生成 |

## 設計判断

- **直下を 404 にせず案内ページにした**: URL を手打ちで `usephys.net` とだけ入れた人が行き止まりにならないように。リンクは通常の `<a>` なので、人が辿ればそこから note に行ける
- **クローラ向け 302 も直下では止めた**: 直下は人向けリンクとして使わないため OG カードは不要。クローラが 302 で note に飛んでも PV にはならないが、動作を「直下では一切転送しない」に揃えた方が説明しやすい
- **`bio_clicks_ingest.py` は変更なし**: `_root` を除外する既存ルールのままで良い。直下にビーコンが無くなるので `_root` は今後ほぼ 0 になり、「除外（bot・スキャナ）」はページ取得の判定分だけが残る

## 確認結果

本番 URL に curl で確認（人向け UA と `Twitterbot/1.0`）：

| URL | 人 | Twitterbot |
|---|---|---|
| `usephys.net/` | 200 案内ページ（転送・ビーコン無し） | 200 案内ページ |
| `usephys.net/.env` | 200 案内ページ | 302 → note |
| `usephys.net/note/` | 200 転送ページ＋ビーコン（キー `note`） | 302 → note |
| `threads.usephys.net/note/` | 200 転送ページ＋ビーコン | 302 → note |
| `xpost.usephys.net/` | 200 案内ページ | 200 案内ページ |
| `xpost.usephys.net/n4ce6fbbf837f/test` | 200 転送ページ＋ビーコン（キー `n4ce6fbbf837f/test`） | 302 → note |
| `usephys.net/hit?k=note` | 204 | — |

確認用の curl アクセスは UA（`curl`）で集計から除外されるため、bioクリック シートには乗らない。

## 今後の課題

- 10/9 以降の note 流入元の「X bio」「Threads bio」列とボイジャー記事 PV からスキャナ分が消え、bioクリック シートの数字と一致するかを確認する
- 10/3〜10/8 の note 流入元・記事 PV にはスキャナ分が混ざったまま残る。月次突合（`x_note_mentions.py --reconcile`）で 10 月分を扱うときは、この期間の usephys.net 系の到達を bioクリック シートの値で読み替える
