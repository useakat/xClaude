---
title: W003 output/draft ディレクトリの役割分担を spec.md に明文化
date: 2026-06-26
tags: [workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260627_20260626_writer_xshort_and_w003_roles/)

## 背景・動機

W003 投稿フォルダの `output/` に中間版の原稿や不採用の図解候補が混在し、「最終版」がどのファイルか判別しにくい状態になっていた。Drive アップロード後の確認でも最終版だけを見たいのに中間版が邪魔になるため、役割を明確に分離する必要があった。

## 実施内容

- `projects/w003/spec.md` の Naming セクションに `draft/` と `output/` の役割分担を追記
  - `draft/`: 原稿の生出力・推敲各版・図解5候補すべてを置く中間物置き場
  - `output/`: `index.md`（最終原稿）・採用図解1枚・その生成プロンプトの3種のみ
- 中間版が `output/` に残っていた場合は `draft/` へ移すルールを明記
- Verification チェックリストに「`output/` に最終版以外のファイルが無い」を追加
- 既存の `20260624_betelgeuse_siwarha` フォルダの中間版（draft_v1〜v5）を `output/` から `draft/` へ移動

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/w003/spec.md` | `draft/` / `output/` の役割定義・Verification チェックを追加 |
| `projects/w003/20260624_betelgeuse_siwarha/draft/draft_v1〜v5.md` | `output/` から `draft/` へ移動 |

## 確認結果

`spec.md` を参照した次回制作から `output/` に最終版のみが残るようになる。
