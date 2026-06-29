---
title: X短文投稿(z01)の outputs 記録に neta_id / thought_id を追加
date: 2026-06-29
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260629_outputs_neta_thought_id/)

## 背景・動機

z01 短文を X 投稿して outputs シートへ記録する際、どのネタ由来かを追えるよう neta_id / thought_id も残したい。outputs シートには `neta_id`(D)・`thought_id`(E) 列が既にあるが、`record_output.py` は `[日時, URL, what_id]` の3列しか書いておらず空のままだった（2026-05-25 の neta_id 記録は統合版 `post_from_email.sh` への移行で失われていた）。

z01 の Gmail 下書きは冒頭に `ソース: {シート}[{番号}]`（例 `noteNeta[33]` / `newsTopics[5]` / `thoughts[T007]`）を持つため、これを投稿時に抽出して記録する。

## 実施内容

- `record_output.py` を argparse 化し、任意引数 `--neta-id` / `--thought-id` を追加。後方互換（`<url> <how_id>` のみなら従来どおり3列追記）。
- `post_from_email.sh` の投稿成功後、本文 `$BODY` から正規表現 `ソース[:：]\s*([A-Za-z]+)\[([^\]]+)\]` でシート名と ID を抽出し、`record_output.py` に渡す（`eval` で引数展開）。

## 記録方式（ユーザー決定）

- `thoughts` → **thought_id 列**に **ID のみ**（例 `T007`）。
- `noteNeta` / `newsTopics`（thoughts 以外）→ **neta_id 列**に **シート名付きトークン**（例 `noteNeta[33]`）。これで neta_id 列だけでシート由来も判別できる。
- `ソース:` 行が無いフロー（W001/W003/W006 等）→ 従来どおり3列のみ（影響なし）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/record_output.py` | argparse 化。`--neta-id`(D列)/`--thought-id`(E列) を追加し追記行を可変構築 |
| `scripts/post_from_email.sh` | 投稿成功後に本文の `ソース:` 行を抽出し、シート種別で neta_id/thought_id を振り分けて record_output に渡す |

## 設計判断

- **z01 専用分岐にせず「`ソース:` 行があれば記録」の汎用処理**にした（z01 にだけ効き、他フローは `ソース:` 行が無いので無害）。spec.md の下書きフォーマットは既存のため変更不要。
- neta_id はシート名付きトークン（`noteNeta[33]`）で記録し、noteNeta と newsTopics を1列でも区別可能に（ユーザー方針）。

## 確認結果

- 抽出ロジック単体テスト：`noteNeta[33]`→`--neta-id 'noteNeta[33]'` / `thoughts[T007]`→`--thought-id T007` / `newsTopics[5]`→`--neta-id 'newsTopics[5]'` / ソース無し→引数なし、を確認。
- `record_output.py --help` で引数パース確認（2引数のみでも動作＝後方互換）。
- `bash -n scripts/post_from_email.sh` 構文 OK。
- 実シートへの追記は汚染回避のためテスト投稿せず、次回 z01 実投稿（cron）で記録される（投稿後に outputs 最終行 D/E 列で確認）。

## 今後の課題

- 実記録の確認は次回 z01 投稿後に outputs シートで行う。
