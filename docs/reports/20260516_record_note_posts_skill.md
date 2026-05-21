---
title: record-note-posts スキル新設
date: 2026-05-16
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

note.com の投稿統計（ビュー・スキ数）を手動で確認・記録していたため、定期的な振り返りが難しかった。また、note 投稿の文字数はスプレッドシートに「空欄」で放置されていた。これらを自動取得して Google Sheets「note投稿一覧」に記録・更新することで、X投稿一覧と同様に分析できる状態にする。

## 実施内容

- `scripts/fetch_note_stats.py` を新規作成
  - note 非公式 API（`v2/creators/{urlname}/contents`）で記事一覧・ハッシュタグ・サムネを取得
  - `v1/stats/pv?filter=all` で累積ビュー数・スキ数を取得
  - `v3/notes/{key}` で本文 HTML を取得し、タグ除去・空白除去後の文字数をカウント
  - `--all` / `--months N` オプションで取得期間を切り替え可能
- `.claude/skills/record-note-posts/SKILL.md` を新規作成
  - 5ステップ構成（データ取得→既存URL確認→振り分け→更新→新規追加）
  - 列構成: A=投稿日時, B=記事URL, C=タイトル, D=文字数, E=ハッシュタグ, F=サムネURL, G=サムネプレビュー, H=ビュー, I=スキ, J=スキ率
- `.claude/skills/metadata.yaml` に `record-note-posts: category: 運用・記録` を追記

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/fetch_note_stats.py` | 新規作成。note API から記事統計を取得し JSON 出力 |
| `.claude/skills/record-note-posts/SKILL.md` | 新規作成。note投稿一覧シートへの記録・更新スキル |
| `.claude/skills/metadata.yaml` | `record-note-posts` を運用・記録カテゴリで追記 |

## 設計判断

- **文字数取得**: `v3/notes/{key}` エンドポイントが本文 HTML を返すと確認。`v2/notes/{key}` は 404、`v1/notes/{key}` は 405 だったため `v3` を採用。記事1件につき1リクエスト追加となるが、取得精度を優先。
- **累積ビュー数**: `filter=all` で投稿開始〜調査日時点の累積 `read_count` が取得できることを確認。`filter=month` は月次増分のため不採用。

## 確認結果

- `python3 scripts/fetch_note_stats.py --all` で24件の記事データが取得でき、文字数も正常にカウントされることを確認（例: 7993字、8280字など）。
- `/record-note-posts all` を実行し、note投稿一覧シートに24件が正しい列構成で記録されることを確認。
