---
title: reporter-daily に threads/note 投稿の種類判定と x_url 連携を追加
date: 2026-07-15
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

Threads への投稿は X 投稿の転載が中心だが、日報では threads 投稿の種類（長文ストーリー／ワンポイント解説など）を判定する手段がなく、すべて「その他」扱いになっていた。outputs シートには媒体列も無く、threads 投稿と元の X 投稿を紐付ける情報が記録されていなかった。日報で媒体別・種類別に実績を把握できるようにするため、記録と判定の両側を拡張した（実装コミットは 7/12 `9be5617`）。

## 実施内容

- **outputs シートに H列 `x_url` を追加**：threads 投稿の行に、転載元の X 投稿 URL を記録する。媒体は専用列を持たず URL 列（twitter.com/x.com・note.com・threads.com）から判別する方針とし、threads 投稿は what_id を空のままにする。
- **`scripts/record_output.py` を拡張**：`--x-url` オプションを追加し、`how_id` を省略可能にした（threads 投稿用）。合わせて IPv4 固定処理を削除（threads 系スクリプトと重複していたため整理）。
- **`scripts/post_threads_from_email.sh` を拡張**：メール本文の `[XURL]` タグを抽出し、outputs 記録時に `--x-url` として渡すようにした。従来の固定 `how_id=threads` 記録を廃止。
- **reporter-daily スキルに STEP 5（Threads投稿一覧の取得・分類）を追加**：threads 投稿の種類を「outputs の x_url → 元 X 投稿の what_id」の優先順位で判定し、x_url が無い場合は X投稿一覧シート全体から本文一致でフォールバック照合する。日報フォーマットにも threads 投稿セクション（views・いいね・リポスト・引用・リプ）を追加。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/reporter-daily/SKILL.md` | STEP 5（threads 取得・分類）追加、outputs の x_url 照合ロジック、日報フォーマットに threads セクション追加 |
| `scripts/record_output.py` | `--x-url` オプション追加・`how_id` 省略可・outputs H列書き込み対応 |
| `scripts/post_threads_from_email.sh` | `[XURL]` タグ抽出と record_output への引き渡しを追加 |

## 設計判断

- 媒体列を outputs に追加する案もあったが、URL から一意に判別できるため列は増やさなかった。
- threads 投稿の種類はコピー先で二重管理せず、元 X 投稿の what_id を参照する形にした（1つの投稿の種類情報は X 側の記録に一本化）。
- 過去の threads 投稿（x_url 未記録）に対応するため、本文一致のフォールバック照合を入れた。threads 転載は元 X 投稿と同日とは限らないため、照合は日付を絞らずシート全体を対象とする。

## 確認結果

- 7/15 の threads 自動投稿3件で outputs H列に x_url が記録されることを確認。
- 7/14 日報の作成時に STEP 5 の分類ロジックが動作することを確認（当日は threads 投稿0件のためセクション省略の分岐を通過）。

## 今後の課題

- Gmail 下書きを自動作成する `make_threads_draft.py` 側にも `[XURL]` タグの出力が必要（7/14 の別コミット `98556e8` で対応済み）。
