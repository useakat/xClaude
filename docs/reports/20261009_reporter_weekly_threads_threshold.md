---
title: reporter-weekly の Threads 個別行の基準を 1,000 views 以上に変更
date: 2026-10-09
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

週報では、基準を満たす投稿だけ個別の行（タイトル・要約・数値・伸びた理由）を書き、それ以外はプロジェクトの合計行に数だけ含める。Threads の基準は 30 views 以上で、X の基準（1万インプ以上）と比べて大幅に低く、ほとんどの投稿が個別行の対象になっていた。変更時のやり取りはローカルに残っていないため、動機はコミット内容と前後の週報からの推定である。

## 実施内容

- reporter-weekly の Threads の個別行の基準を、**30 views 以上 → 1,000 views 以上** に変更した（コミット `d848c9b`、2026-10-05）。
- Wiki のスキル解説（`docs/skills/reporter-weekly.md`）も同じ内容に更新した。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/reporter-weekly/SKILL.md` | Threads の個別行の基準を 1,000views 以上に変更 |
| `docs/skills/reporter-weekly.md` | Wiki の同じ箇所を更新 |

## 確認結果

変更直後に確定した 9月28日週の週報（`docs/reports/weekly/2026-W40.md`、コミット `c9ff16d`）で、Threads の個別行が 1,000 views 以上の投稿に絞られていることを確認した。

## 備考

変更はクラウドのセッションで行われ、ローカルに会話ログが残っていないため、セッション履歴は添付していない。
