---
title: x-onepoint/outputs/ 投稿別フォルダ構造の導入
date: 2026-06-03
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260603_20260603_x_onepoint_project_claude_md_and_docs_update/)

## 背景・動機

`projects/x-onepoint/spec.md` では画像を `outputs/` に保存すると定義されていたが、ディレクトリが未作成でグローバルな `outputs/` に直置きされていた。同じ投稿のテキスト原稿と画像が別々の場所に散在していたため、1投稿 = 1フォルダとして関連成果物をまとめて管理できる構造に変更した。

## 実施内容

- `projects/x-onepoint/outputs/YYYYMMDD_[topic]/` 形式の投稿別フォルダ構造を導入
- 既存の3画像（`outputs/20260602_zukaitide_*.png`）を `projects/x-onepoint/outputs/20260602_陸のタイド/` へ移行し、ファイル名をスタイル名のみに簡略化
- `projects/x-onepoint/spec.md` の Output・Naming・Rules セクションを新構造に更新

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/x-onepoint/spec.md` | Output 保存先・Naming 規則・Rules Step 7 を投稿別フォルダ構造に更新 |
| `projects/x-onepoint/outputs/20260602_陸のタイド/bento-grid.png` | `outputs/` 直下から移行 |
| `projects/x-onepoint/outputs/20260602_陸のタイド/scientific.png` | 同上 |
| `projects/x-onepoint/outputs/20260602_陸のタイド/sketch-note.png` | 同上 |

## 設計判断

- `reports/`・`research-plans/` はグローバル `outputs/` のままにし、今回の対象外とした（投稿成果物ではないため）
- 画像ファイル名は `[style].png` に簡略化。フォルダ名に日付・トピックが含まれるため冗長な prefix が不要になった
- `visual_infographic` スキルは汎用スキルのため変更せず、spec.md の Rules Step 7 に保存先パスを明記する方針にした

## 確認結果

```
projects/x-onepoint/outputs/20260602_陸のタイド/
├── bento-grid.png
├── scientific.png
└── sketch-note.png
```

3ファイルが新フォルダに移行済みであることを確認。
