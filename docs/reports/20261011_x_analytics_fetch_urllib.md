---
title: X アナリティクス取込の Drive MCP 呼び出しを urllib に変更
date: 2026-10-11
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

H5 検証用の週次 X アナリティクス CSV 取込（日曜 18:17 JST の routine）が、2026-10-11 の実行で `ModuleNotFoundError: No module named 'requests'` により失敗した。`scripts/fetch_x_analytics_csv.py` が Drive MCP の HTTP 呼び出しに `requests` を使っていたが、routine が走るリモート環境には `requests` が入っていないことがあり、外部依存のままでは毎週の取込が環境ガチャになる。

## 実施内容

- Drive MCP への JSON-RPC POST を `requests` から標準ライブラリの `urllib.request` / `urllib.error` に置き換えた（依存ゼロ化）
- HTTP エラー時は `urllib.error.HTTPError` を捕捉し、ステータスコードとレスポンス先頭200字を含む `RuntimeError` に変換（従来の `raise_for_status()` 相当の挙動を維持）
- SSE レスポンスの `data:` 行パースなど後続の処理は変更なし

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/fetch_x_analytics_csv.py` | `requests.post` を `urllib.request.urlopen` に置換、HTTPError のハンドリングを追加 |

## 設計判断

`requests` を環境にインストールする案（`sheets_pydeps_install.sh` 方式）もあるが、このスクリプトの HTTP 呼び出しは単純な POST 1種類だけで、標準ライブラリで十分に書ける。依存を増やすより依存を無くす方が routine の確実性が高いため、urllib 化を選んだ。

## 確認結果

- コミット `b5ecd4f` として master に push 済み
- 次回の週次取込 routine（日曜 18:17 JST）で実動作を確認する

## 今後の課題

- 他の routine 用スクリプトにも `requests` 依存が残っていないかの横展開チェック
