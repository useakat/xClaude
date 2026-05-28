---
title: persona シートへのペルソナ 19 件登録
date: 2026-05-22
tags: [workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260522_persona_sheet_registration_session/)

## 背景・動機

`persona/` フォルダに 19 件のペルソナ定義ファイル（01〜19）が存在していたが、Google Sheets の persona シートは空（ヘッダーのみ）だった。スキルやスクリプトが Sheets を参照してペルソナ情報を取得する設計になっているため、データを登録する必要があった。

## 実施内容

- `persona/` フォルダの 01〜19 の Markdown ファイルを全て読み込み
- 各ファイルの H1 タイトル・悩みセクションを確認
- pain シート（SS2）の pain_id と照合し、各ペルソナの primary pain_id を推論してマッピング
- mcp-gsheets の `sheets_append_values` で persona シートに 19 行を一括追加（P01〜P19）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| Google Sheets SS2 `persona` シート | 行 2〜20 に P01〜P19 の 19 件を追加 |

## 設計判断

- persona_id は `P01`〜`P19` 形式を採用（`database/persona.csv` の PE001 系と区別するため接頭辞を `P` に統一）
- pain_id は各ファイルの「抱えている悩み・葛藤」セクションを読み、pain シートの pain_id と最も近いものを 1 件割り当て
  - 科学への興味・知識取得欲求 → PR003（科学の面白い話をサクッと知りたい）
  - 「自分には無理」系の諦め・コンプレックス → PR011
  - 理想と現実のギャップ・後ろめたさ → PR006
  - 授業・発信準備コスト → PR017
  - 閉塞感・意味を求める → PR007

## 確認結果

`sheets_get_values` で persona シートを取得し、ヘッダー含む 20 行（P01〜P19）が正しく登録されていることを確認。
