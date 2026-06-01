---
title: x-onepoint プロジェクト設計ドキュメント新設
date: 2026-06-01
tags: [wiki, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

`plan.md` だけでは発信軸の概要しか把握できず、実制作時に「どんな表現を使うか」「制作フローは何か」を毎回 CLAUDE.md を読み返す必要があった。また brand（口調・NG表現）と spec（制作手順・命名規則）が混在していたため、スキルから参照しにくかった。設計ドキュメントを役割ごとに分割して一元管理できる構成にする必要があった。

## 実施内容

- `plan.md` を W003 / PE01 / PR003 のコンテンツ計画に基づき具体化
- `brand.md` を新設（表現ルール・Do Not・口調ガイドライン）
- `spec.md` を新設（制作フロー・命名規則・検証項目）
- 各ファイル間で役割を分離し、相互参照で一元管理できる構成にした

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/x-onepoint/plan.md` | W003/PE01/PR003 の発信計画を具体化 |
| `projects/x-onepoint/brand.md` | 新規作成：口調・表現ルール・NG表現を定義 |
| `projects/x-onepoint/spec.md` | 新規作成：制作フロー・命名規則・品質基準を定義 |

## 設計判断

`brand.md`・`spec.md`・`plan.md` の3ファイル構成にすることで、スキル（`writer-xonepoint` 等）から必要な情報だけを選んで Read できるようになる。CLAUDE.md にすべてを詰め込む前の設計より参照効率が高い。

## 確認結果

コミット `5c4c9d9` で3ファイルが `projects/x-onepoint/` に作成済みであることを確認。
