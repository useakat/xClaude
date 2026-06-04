---
title: mcp-gsheets 認証を GOOGLE_APPLICATION_CREDENTIALS に統一
date: 2026-06-04
tags: [infra, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

mcp-gsheets の認証は当初 `GOOGLE_SERVICE_ACCOUNT_KEY` 環境変数を参照していたが、他の Google 連携（Drive/Sheets を使う Python スクリプト）が Google 標準の `GOOGLE_APPLICATION_CREDENTIALS` を前提としており、認証情報の参照先が二重化していた。環境変数が片方しか設定されていないと mcp-gsheets が接続できない状態が起こり得たため、Google 標準の `GOOGLE_APPLICATION_CREDENTIALS` に一本化する。

## 実施内容

- `.mcp.json` の mcp-gsheets の env を `GOOGLE_SERVICE_ACCOUNT_KEY` から `GOOGLE_APPLICATION_CREDENTIALS` ＋ `GOOGLE_PROJECT_ID` に変更
- `.claude/settings.json` に `env` ブロックを追加し、`GOOGLE_APPLICATION_CREDENTIALS`（`${HOME}/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json`）と `GOOGLE_PROJECT_ID` を定義
- `~/.bashrc` にも同じ環境変数を追加し、シェル経由の実行でも認証が通るようにした

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.mcp.json` | mcp-gsheets の env を `GOOGLE_APPLICATION_CREDENTIALS` ＋ `GOOGLE_PROJECT_ID` 参照に変更 |
| `.claude/settings.json` | `env` ブロックを新設し認証情報パスとプロジェクト ID を定義 |
| `~/.bashrc` | 同じ環境変数を追加（シェル実行時の認証用） |

## 設計判断

Google の各種 SDK が標準で参照する `GOOGLE_APPLICATION_CREDENTIALS` に揃えることで、mcp-gsheets と他の Python スクリプトの認証情報を 1 ファイルに集約。独自命名の `GOOGLE_SERVICE_ACCOUNT_KEY` を残すより環境構築・トラブルシュートが容易になる。

## 確認結果

`sheets_get_metadata` でスプレッドシート「postNeta」のシート一覧を正常に取得でき、mcp-gsheets が接続できることを確認した。
