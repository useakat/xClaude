---
title: daily-xonepoint 下書きにネタ番号・分野タグ追加、outputs に neta_id 記録
date: 2026-05-25
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260526_xonepoint_neta_tags_and_neta_id_record/)

## 背景・動機

daily-xonepoint が作る下書きメールには、使ったネタの情報（ネタ番号・分野）が含まれていなかった。
そのため cron で X に投稿しても、`outputs` シート側にどのネタ由来かの記録が残らず、投稿実績とネタを後から突き合わせられなかった（`neta_id` 列は存在するが常に空だった）。

投稿とネタを紐付けて辿れるようにするため、下書きメールにネタ情報のタグを埋め込み、投稿記録時にそれを `outputs` シートへ転記する経路を整備した。

## 実施内容

- daily-xonepoint の下書きメールに 2 つのタグを追加：
  - `[分野]`：使ったネタの分野（onePointNeta K列）。`[最終原稿]` の前に配置。
  - `[ネタ番号]`：`onePointNeta[番号]` 形式。メール本文の冒頭に配置。
- STEP 2 で writer-xonepoint が返すネタ番号から、STEP 1 で取得済みの onePointNeta データの K列（分野）を読み取り記憶する手順を追加（K列が空なら「その他」）。
- cron 投稿経路（`post_from_email.sh`）で `[ネタ番号]` タグを `extract_tag.py` で抽出し、`record_output.py` へ 4 つ目の引数として渡すようにした。
- `record_output.py` を 4 引数（任意の `neta_id`）対応にし、`outputs` シートへ `[日時, URL, what_id, neta_id]` を追記するよう変更。neta_id 列（D列）へ書き込まれる。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/daily-xonepoint/SKILL.md` | STEP 2 にネタ番号・分野の記憶を追加。STEP 4 のメール本文組み立てに `[ネタ番号]`（冒頭）・`[分野]`（`[最終原稿]` 前）タグを追加 |
| `scripts/post_from_email.sh` | `[ネタ番号]` タグを抽出する `NETA_ID` を追加し、`record_output.py` 呼び出しに 4 つ目の引数として渡す |
| `scripts/record_output.py` | 任意の `neta_id` 引数（3 or 4 引数許容）を追加し、`append_row` を `[dt, url, how_id, neta_id]` に変更 |

## 設計判断

- neta_id に書き込む値は **タグ全文（`onePointNeta[3]`）** を採用。番号だけだとどのシート由来か判別できないため、シート名＋番号で一意に特定できる形式にした。
- `[ネタ番号]` タグの抽出は `[投稿文]`/`[リプ]` と同じ `extract_tag.py` 方式に統一。タグの無い投稿タイプ（W006 等）では未検出→空文字となり、`record_output.py` の 3 引数互換も保つため後方互換性が崩れない。

## 確認結果

- `extract_tag.py ネタ番号` をローカルで確認：タグありで `onePointNeta[3]` を出力（exit 0）、タグなしで空（exit 1）。想定どおり。
- `record_output.py`（Python 構文）・`post_from_email.sh`（`bash -n`）ともに構文チェック OK。
- 実際の neta_id 列書き込みは次回 cron（6:00）の投稿成功時に `outputs` シートで確認する。

## 今後の課題

- thoughts シートの `thought_id` 列（E列）は今回未対応。思想を紐付ける場合は同様にタグ＋記録の経路を追加する必要がある。
