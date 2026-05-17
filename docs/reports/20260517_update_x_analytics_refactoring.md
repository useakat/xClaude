---
title: update-x-analytics 高速化リファクタリング
date: 2026-05-17
tags: [workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md)

## 背景・動機

`update-x-analytics` エージェントの初期実装では実行に約 387 秒・ツール呼び出し 59 回を要していた。ボトルネックは2つ：

1. **ToolSearch による Drive ツール名探索**：claude.ai MCP コネクタは UUID ベースのツール名（`mcp__960819bd-...`）を使うため、エージェントが毎回 ToolSearch でツール名を探す必要があった。
2. **LLM による大量データ処理**：CSV 全行・B列全行をエージェントのコンテキストに載せてマッチング → トークン消費が膨大。

また、フォルダパスが `analytics_tmp` のままで `Xanalytics/tmp` への変更も必要だった。

## 実施内容

- **Drive CSV 取得をスクリプト化**（`scripts/fetch_x_analytics_csv.py`）
  - Anthropic プロキシ（ingress token + `mcp-config-{SESSION_ID}.json`）を直接 HTTP 呼び出し
  - フォルダ ID を `Xanalytics/tmp`（`1J45co5hN74gzxNateNRyeDtswZu0lMr3`）に変更
  - CSV を base64 デコード → csv モジュールでパース → `/tmp/x_analytics_map.json` に保存
  - ToolSearch 不要・Drive 操作をスクリプトが完結

- **マッチングをスクリプト化**（`scripts/match_x_analytics.py`）
  - `/tmp/x_analytics_map.json`（CSV データ）と `/tmp/x_analytics_b_col.json`（Sheets B列）をファイルで受け取る
  - status ID（`/status/(\d+)` regex）で突き合わせ
  - `sheets_batch_update_values` 用の `update_data` JSON を stdout に出力

- **Sheets 操作はエージェント（mcp-gsheets）が担当**
  - B列取得：`sheets_get_values` → `/tmp/x_analytics_b_col.json` に保存
  - 一括書き込み：`sheets_batch_update_values` を 1 回のみ呼び出し（AA:AC 列）

- **エージェント定義 `.claude/agents/update-x-analytics.md` を整理**
  - モデルを `claude-sonnet-4-6`（Haiku は ToolSearch 非対応のため）
  - 5ステップの明確なフロー定義

- **`settings.json` に `sheets_batch_update_values` を許可追加**

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/agents/update-x-analytics.md` | エージェント定義を全面改訂（5ステップフロー、スクリプト分離） |
| `scripts/fetch_x_analytics_csv.py` | 新規作成：Drive CSV 取得・パース・保存 |
| `scripts/match_x_analytics.py` | 新規作成：status ID マッチング・update_data 生成 |
| `.claude/settings.json` | `mcp__mcp-gsheets__sheets_batch_update_values` を allow に追加 |

## 設計判断

**Drive 操作をスクリプト化、Sheets 操作を mcp-gsheets に分離した理由**：

- Drive MCP は UUID ベースのツール名で LLM が毎回 ToolSearch → 遅い。スクリプトが直接 HTTP 呼び出しすれば定数時間。
- Sheets は mcp-gsheets（stdio）が安定して動いており、LLM が直接呼ぶ方がシンプル。スクリプト化するとサービスアカウント認証の管理が必要になる。
- マッチング（大量データの突き合わせ）は LLM のコンテキストを消費するため、Python で実行する方が高速・確実。

## 確認結果

リファクタリング後の実行結果：
- 実行時間：約 46 秒（387 秒 → 88% 削減）
- ツール呼び出し：4 回（59 回 → 93% 削減）
- マッチ件数・更新列（AA:AC）は正常に動作を確認

## 今後の課題

- Drive MCP の UUID がセッション固有のため、スクリプトは毎回 `mcp-config-{SESSION_ID}.json` を参照する必要がある。セッション外では動作しない設計（想定内）。
- `fetch_x_analytics_csv.py` の Drive 認証方式は Anthropic プロキシ依存のため、プロキシ仕様変更時に要メンテ。
