---
title: mcp-gsheets 切断再発の修正（enableAllProjectMcpServers の実装未コミットを反映）
date: 2026-07-14
tags: [infra, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260714_mcp_gsheets_trust_setting_recommit/)

## 背景・動機

7/14 朝の日報 routine（reporter-daily）で、mcp-gsheets の `sheets_get_values` 呼び出しが全て `Tool permission request failed: Error: Tool permission stream closed before response received` で失敗し、日報を作成できなかった。セッション中は mcp-gsheets を含む MCP サーバー群が接続→切断を繰り返しているように見えた。

調査の結果、以下が判明した：

- サーバープロセス自体は正常起動していた（`logs/mcp_gsheets_launch.log` に当日 11:46 の `node exec` 記録あり。再スポーンの繰り返しも無し）。
- 失敗していたのはツール呼び出し時の**サーバー信頼確認**の層。無人実行の routine では確認プロンプトに誰も応答できず、ストリームが閉じて切断扱いになっていた。
- この事象は 7/7 の報告書「[プロジェクトMCPサーバーの信頼確認を自動承認し、リモート実行でのgsheets切断を解消](./20260707_mcp_gsheets_project_trust_auto_approve/)」で原因特定・対策済みのはずだった。
- しかし git 履歴を確認すると、7/7 のコミット `13712d7` は**報告書・変更ログの docs 3ファイルのみ**で、肝心の `.claude/settings.json` への `enableAllProjectMcpServers: true` 追加が未コミットだった（`git log -S "enableAllProjectMcpServers"` で全履歴を検索しても settings.json を変更したコミットは存在しない）。
- 実際に当日のリモートコンテナの `~/.claude.json` は `enabledMcpjsonServers: []`（未承認状態）で、7/7 報告書が特定した原因状態と完全一致していた。

つまり「docs だけコミットして実装が未コミット」パターンの再発である（7/4 の事前ウォーム実装でも同じことが起きており、変更ログにその旨の注記がある）。

## 実施内容

- `.claude/settings.json` のトップレベルに `"enableAllProjectMcpServers": true` を追加（7/7 に設計・承認済みだった変更の再適用）。
- 作業ブランチ `claude/zealous-fermi-rf1zww` に push 後、routine が参照する master にも cherry-pick で反映（コミット `cc0170f`）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | トップレベルに `enableAllProjectMcpServers: true` を1行追加 |

## 設計判断

- 対策内容自体は 7/7 報告書の設計判断に従った（コンテナ固有の `~/.claude.json` ではなくリポジトリ管理下の `settings.json` に置くことで全環境に恒久反映）。今回は新規設計ではなく、未コミットだった実装の反映。

## 確認結果

- `git show --stat 13712d7` で 7/7 コミットが docs のみだったことを確認。
- 追加後の `settings.json` が有効な JSON であることを確認し、master へ push 済み。
- 実挙動（次回リモート routine で信頼確認タイムアウトが解消されるか）は次回の日報 routine 実行で確認する。

## 今後の課題

- 「docs のみコミットで実装が未コミット」の再発が2回目。/record 実行時に、報告書の「変更ファイル」表に挙がったファイルが実際に直近コミットに含まれているかを照合するチェックを入れると再発を防げる。
