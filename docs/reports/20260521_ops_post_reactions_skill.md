---
title: ops_post-reactions スキル新設
date: 2026-05-21
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md) ｜ [セッション履歴→](../history/20260521_ops_post_reactions_session.md)

## 背景・動機

「実は」28投稿への反応531人分析（2026-05-20）をワンオフで行ったが、これを任意条件で繰り返せる汎用スキルが必要だった。GetRepliesAndQuotes GAS によるリプライ蓄積（2026-05-21新設）と、フォロワーペルソナ LLM 分類（follower_persona_llm.json）を組み合わせることで、キーワード・HOW_ID・期間などの条件で対象投稿を絞り込み、反応者の19ペルソナ別指標を自動算出できる仕組みを整えた。

## 実施内容

- `.claude/skills/ops_post-reactions/SKILL.md` を新設（7ステップの実行フロー）
- `scripts/ops_post-reactions/fetch_target_posts.py` を新設
  - SA JWT + Google Sheets API 直接呼び出し（`fetch_x_b_col.py` 準拠）
  - `--keyword` / `--how_id` / `--days_back` フィルタを実装
  - `--how_id` は SS2 outputs シートとの照合で絞り込み
  - 出力: `/tmp/target_posts.json`（tweet_id / date / text / profile_clicks / follows）
- `scripts/ops_post-reactions/fetch_sheet_replies.py` を新設
  - 「リプ・引用一覧」シートから指定 tweet_ids の反応を抽出
  - (username, parent_tweet_id) で重複除去
  - 出力: `/tmp/sheet_replies.json`
- `scripts/ops_post-reactions/compute_metrics.py` を新設
  - Sheets アクセスなし（純粋な計算のみ）
  - total_followers を `follower_persona_llm.json` の件数から動的カウント
  - 反応感度・反応密度・F反応率をペルソナ別に算出
  - 出力: `/tmp/metrics_output.json`（反応感度降順ソート）
- `.claude/skills/metadata.yaml` に `ops_post-reactions: category: リサーチ・分析` を追記

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/ops_post-reactions/SKILL.md` | 新規作成（7ステップ実行フロー） |
| `scripts/ops_post-reactions/fetch_target_posts.py` | 新規作成（投稿フィルタ） |
| `scripts/ops_post-reactions/fetch_sheet_replies.py` | 新規作成（シートリプライ抽出） |
| `scripts/ops_post-reactions/compute_metrics.py` | 新規作成（ペルソナ別指標計算） |
| `.claude/skills/metadata.yaml` | `ops_post-reactions` エントリ追記 |

## 設計判断

- **スクリプトの事前作成**: 毎回 LLM がスクリプトを生成・実行する方式は無駄なため、再利用可能なスクリプトを `scripts/ops_post-reactions/` に事前配置。実行時のトークンコストはゼロ
- **Sheets API 直接呼び出し**: `gspread` + SA 認証ではなく `fetch_x_b_col.py` と同じ SA JWT + openssl パターンを採用。MCP プロキシを経由しないため LLM コンテキストにデータが流れ込まない
- **リプライはシート優先**: `searchPostsAll` は OAuth 1.0a 非対応（403確認済み）。`searchPostsRecent`（7日制限）と GAS 蓄積シートを組み合わせ、古い投稿のリプライもカバー
- **total_followers の動的カウント**: 固定値 4183 ではなく `len(follower_persona_llm.json)` で計算することで、フォロワー変動に自動追随

## 確認結果

スキルが `/ops_post-reactions` で呼び出せることを確認。スクリプト3本が `scripts/ops_post-reactions/` に配置され、`metadata.yaml` への追記も完了。

## 今後の課題

- 検証: 「実は」28投稿を条件に実行し、前回の531人分析と同じ結果が出るか確認
- 非フォロワー LLM 分類（STEP 5）の精度検証
- 投稿数が多い場合の `getPostsQuotedPosts` 並列5本上限の妥当性確認
