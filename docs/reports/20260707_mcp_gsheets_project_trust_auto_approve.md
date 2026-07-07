---
title: プロジェクトMCPサーバーの信頼確認を自動承認し、リモート実行でのgsheets切断を解消
date: 2026-07-07
tags: [infra, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260707_mcp_gsheets_project_trust_auto_approve/)

## 背景・動機

reporter-daily routine の実行中に `mcp__mcp-gsheets__sheets_get_values` の呼び出しが断続的に失敗し（`Tool permission request failed: stream closed`）、直後に mcp-gsheets サーバーが切断・再接続するという事象が発生していた。

当初は mcp-gsheets サーバー自体の起動不安定（過去に繰り返し発生していたコールドインストールタイムアウトやパス解決の問題）を疑ったが、`logs/mcp_gsheets_launch.log` を確認するとサーバーは正常に起動しており、install 自体は瞬時に完了していた。

原因を切り分けたところ、コンテナ固有のグローバル設定ファイル `~/.claude.json` の当該プロジェクトエントリで以下が空のままだった：

```json
"mcpServers": {},
"enabledMcpjsonServers": [],
"disabledMcpjsonServers": [],
"hasTrustDialogAccepted": false
```

`.claude/settings.json` の `permissions.allow` に `mcp__mcp-gsheets__*` を登録していたのは「ツール単位の実行許可」であり、`.mcp.json` で定義した MCP サーバー自体を起動してよいかという「サーバー単位の信頼確認」は別の仕組み（`~/.claude.json` の `enabledMcpjsonServers`）で管理されていた。このファイルはリポジトリ管理外・コンテナ固有の状態のため、リモート/routine実行（毎回まっさらなコンテナ）では常に未承認状態から始まり、無人実行中に信頼確認の応答待ちでタイムアウトし、サーバー接続が切れていたと考えられる。

## 実施内容

- `.claude/settings.json` に `"enableAllProjectMcpServers": true` を追加し、`.mcp.json` に定義された全MCPサーバー（`mcp-gsheets`・`xmcp`）をリポジトリ側から恒久的に信頼済みとした。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | トップレベルに `enableAllProjectMcpServers: true` を追加 |

## 設計判断

- `~/.claude.json` の `enabledMcpjsonServers` に個別追記する方法もあるが、このファイルはコンテナ固有でリポジトリに含まれず、リモート環境ではセッションごとにリセットされ得るため恒久対策にならない。`enableAllProjectMcpServers` はリポジトリ管理下の `.claude/settings.json` に置けるため、全環境（ローカル・リモート）で確実に反映される。

## 確認結果

`/root/.claude.json` の該当プロジェクトエントリで `enabledMcpjsonServers` が空・`hasTrustDialogAccepted: false` であることを確認し、これが信頼確認待ちの原因であると特定した。設定追加後の実挙動（次回リモートセッションでの切断再発有無）は今後の routine 実行で継続確認する。

## 今後の課題

- 次回以降の reporter-daily 等の routine 実行で、mcp-gsheets の切断が再発しないか経過観察する。
