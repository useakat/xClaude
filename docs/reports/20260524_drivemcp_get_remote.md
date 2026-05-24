---
title: drivemcp_get_remote.sh 追加：リモートセッション専用 Drive ダウンロード
date: 2026-05-24
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md)

## 背景・動機

リモートセッション（Claude Code remote agent / routine）では gws CLI が使えないため、`drive_get.sh` が動作しない。リモート環境から Drive ファイルを取得する手段として、Anthropic MCP プロキシ経由で Google Drive MCP サーバーにアクセスするスクリプトが必要になった。

同様の課題は X アナリティクス CSV の取得でも発生しており、`fetch_x_analytics_csv.py` もセットで追加された。

## 実施内容

- `scripts/drivemcp_get_remote.sh`（実体は Python）を追加。リモートセッション内で Drive ファイルを file-id 指定またはフォルダ検索クエリで取得し、指定パスに保存する
- `scripts/fetch_x_analytics_csv.py` を追加。X アナリティクス CSV を Drive の `Xanalytics/tmp` フォルダから取得して `/tmp/x_analytics_map.json` にパースして保存する
- いずれも `CLAUDE_CODE_REMOTE_SESSION_ID` 環境変数を利用し、ローカルでは動作しない設計（ローカルは `drive_get.sh` を使う）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/drivemcp_get_remote.sh` | リモートセッション専用 Drive ダウンロードスクリプトを新設 |
| `scripts/fetch_x_analytics_csv.py` | X アナリティクス CSV 取得・パーススクリプトを新設 |

## 設計判断

リモートセッションでは gws CLI が使えない制約があるため、Drive MCP サーバーへの直接アクセスを選択。ローカルと共用のスクリプトにせず、明示的にリモート専用と分けることで誤用を防ぐ。

## 確認結果

`update-x-analytics` エージェントのリモート実行で利用されており、CSV 取得・Sheets 更新が動作していることを確認済み。
