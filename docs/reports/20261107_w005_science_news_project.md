---
title: W005（科学ニュース解説 X長文ポスト）プロジェクトを新設
date: 2026-11-07
tags: [workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20261107_w005_science_news_project/)

## 背景・動機

科学ニュース（最新の探査機・天文イベント）を、W001 と同じ X 長文の型（約 500〜700 字）で出す枠が必要になった。最初の題材は、双子の火星探査機 ESCAPADE が約 1 年待機したのち 2026-11-07 に地球フライバイする話。W001 は note 導線のある長文ストーリーなので、導線を持たず速報性を優先するニュース解説は別プロジェクトにした。

## 実施内容

- `projects/w005/` を W001 を雛形に新設（`CLAUDE.md` / `plan.md` / `brand.md` / `spec.md`）。
  - ネタのモード: A = newsTopics シート（G 列「未使用」）、B = ユーザーが渡す原稿・URL
  - 制作フロー: `/writer-xpost` → check-reader → check-fact-lim → check-critic → check-yohn → ユーザー確認 → `/check-brand ../w001/brand.md` → 最終 check-reader（指摘提示のみ・修正ループなし）
  - セルフリプは空の `[リプ][/リプ]` タグのみ。画像は公式素材を Web 検索で選び、出典を `output/image-source.md` に残す
  - `brand.md` は W001 を継承
- 初回投稿 `projects/w005/20261107_ESCAPADE/` を制作（本文 551 字）。
  - 冒頭フックはユーザー案。折り返し（280 weight）は「なぜ、火星へ直行しなかったのか。」の直後に置いた
  - 事実は NASA ブログ・Space.com・Eos で Web 照合（NotebookLM 未接続のため check-fact-lim・check-critic・check-yohn は未実施）
- `logs/hook_records.csv` に W005 の 1 行を追記（⑤口火+①逆説・モード B）。
- `.gitignore` に `/projects/w005/**/*.png` と `*.jpg` を追加。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/w005/CLAUDE.md` `plan.md` `brand.md` `spec.md` | W005 の仕様一式を新設 |
| `projects/w005/20261107_ESCAPADE/draft/` | 本文・初稿・フォーカス/フック候補・チェック結果 |
| `projects/w005/20261107_ESCAPADE/output/` | `index.md`・`image-source.md`（画像本体は gitignore） |
| `logs/hook_records.csv` | W005 のフック型を 1 行追記 |
| `.gitignore` | W005 配下の画像を除外 |

## 設計判断

- **cron 配線は一度実装して取り消した。** `run_xlong_post.sh`（17:00 枠）と `post_by_label.sh` に件名 `【X科学ニュース】` を足したが、まず手動投稿で運用を確かめるため、コミット前に元へ戻した。`spec.md` に未配線である旨と再配線の手順を記載している。
- **ネタは W001 と同じ newsTopics シートを共有する。** 専用シートは作らず、まずは現状のまま運用する。

## 確認結果

- 折り返し位置は `scripts/x_fold_split.py` で確認した（可視ブロックが問いで終わる）。
- 投稿は 2026-11-07 にユーザーが手動で実施した。

## 今後の課題

- outputs シートへの記録、Drive へのアップロード（Sheets・gws の認証待ち）
- check-fact-lim・check-critic・check-yohn は NotebookLM ブリッジの接続後に実施
- 自動投稿の cron 配線（手動運用で問題がなければ）
