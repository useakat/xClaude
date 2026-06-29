---
title: mcp-gsheets 認証をラッパーで両対応化＋mcp__* 無効ルール整理
date: 2026-06-29
tags: [infra, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260629_mcp_gsheets_launcher_both_envs/)

## 背景・動機

対話セッションで mcp-gsheets が認証失敗した。エラーは `ENOENT: open '/root/xClaude/${HOME}/xClaude/gcp/charming-well-...json'`（未展開の `${HOME}` 付きパス）。

調査の結果、根本原因は **Google Auth Library が `GOOGLE_APPLICATION_CREDENTIALS`（ファイルパス）を最優先で参照する**こと。今回 MCP 子プロセスの環境に `GOOGLE_APPLICATION_CREDENTIALS` が `${HOME}` 未展開で混入しており、`GOOGLE_SERVICE_ACCOUNT_KEY`（JSON文字列）より先に開こうとして失敗していた。混入元はリポジトリ設定・各シェル初期化ファイルのいずれにも無く（grep 0 件）、Claude 起動時の親プロセス環境から注入されていた（リポジトリ側では断てない）。

この症状は過去に複数回再発しており（報告書 `20260604` / `20260607` / `20260618`）、`20260618` の「今後の課題」で CLAUDE.md への明記が提案されていたが未実施だった。

あわせて `/doctor` が `.claude/settings.json` の `permissions.allow` の `"mcp__*"` を「無効なワイルドカード（スキップ）」と指摘した。これは「mcp-gsheets が headless で権限承認待ちになる」現象の正体でもあった。

## 実施内容

- `scripts/mcp_gsheets_launch.sh`（新規）: 起動時に `unset GOOGLE_APPLICATION_CREDENTIALS` で混入値を確実に除去し、`GOOGLE_SERVICE_ACCOUNT_KEY` が空ならローカル gcp JSON から補完してから `npx -y mcp-gsheets@latest` を exec。`.mcp.json` の env は「set」しかできず `unset` できないため、ラッパーで対応。
- `.mcp.json`: mcp-gsheets を `command: bash` / `args: ["scripts/mcp_gsheets_launch.sh"]` に変更（env の KEY/PROJECT_ID 受け渡しは維持）。
- `CLAUDE.md`: 「env に `GOOGLE_APPLICATION_CREDENTIALS` を書かない・混入させない／ラッパーで unset」を実装ルールに明記（再発防止）。
- `.claude/settings.json`: 無効な `"mcp__*"` を削除し、有効形式 `mcp__<server>__*` に置換（`mcp-gsheets` / `claude_ai_Gmail` / `claude_ai_Google_Drive` / `github` / `xmcp`。Calendar は除外）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/mcp_gsheets_launch.sh` | 新規。`GOOGLE_APPLICATION_CREDENTIALS` を unset＋KEY 補完して mcp-gsheets 起動 |
| `.mcp.json` | mcp-gsheets を起動ラッパー経由に変更 |
| `CLAUDE.md` | mcp-gsheets 認証ルール（GOOGLE_APPLICATION_CREDENTIALS 禁止・ラッパー unset）を明記 |
| `.claude/settings.json` | `mcp__*`（無効）→ `mcp__<server>__*`（有効）5件へ置換 |

## 設計判断

- **ラッパーで `unset`**：`.mcp.json` の env は値を set するだけで unset できない。親プロセスからの混入を断つには起動シェルで `unset` するのが最も確実（起動環境に依存しない）。
- **ローカル/リモート両対応**：ローカルは gcp JSON ファイルから KEY を補完、リモート（routine/agent）は継承 env の KEY をそのまま使用（gcp/ が無くても動く）。
- **`mcp__<server>__*` へ置換**：`mcp__*` は仕様上無効。実際に使うサーバーのみ有効ワイルドカードで許可し、cron/routine の無人実行でも MCP ツールが承認待ちにならないようにした。

## 確認結果

- `bash -n scripts/mcp_gsheets_launch.sh` 構文 OK、`.mcp.json` valid JSON。
- ラッパー単体検証：混入させた `GOOGLE_APPLICATION_CREDENTIALS` が unset 後に未設定、`GOOGLE_SERVICE_ACCOUNT_KEY` がファイルから補完（length 2398）されることを確認。
- `npx` は `/usr/bin/npx` で解決可能。
- settings.json：`mcp__*` 消去・5ルール追加を確認、valid JSON。
- **MCP 再読み込み後の `sheets_get_values` 疎通確認は次セッション（MCP 再接続後）で実施予定**。

## 今後の課題

- `.mcp.json` の `args` は相対パス（cwd＝プロジェクトルート前提）。リモートで解決できない場合は絶対パス／`$CLAUDE_PROJECT_DIR` への変更を検討。
- 親プロセスへの `GOOGLE_APPLICATION_CREDENTIALS` 注入元の特定（option C）は未実施。ラッパーの unset で実害は無いが、根本の注入を断てればより綺麗。
