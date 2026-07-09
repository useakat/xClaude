---
title: mcp-gsheets 起動パスを上方探索化し projects/ 配下起動の -32000 退行を修正
date: 2026-07-09
tags: [infra, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260709_mcp_gsheets_launch_upward_search/)

## 背景・動機

`/mcp` で `Failed to reconnect to mcp-gsheets: -32000` が発生。当初は一過性の再接続タイムアウトを疑ったが、手動でランチャーを実行すると `initialize` ハンドシェイクが 0.8〜0.9 秒で正常応答し、認証・install・信頼設定にも異常がなかった。

Claude Code の MCP 接続ログ（`~/.cache/claude-cli-nodejs/-root-xClaude-projects-w002/mcp-logs-mcp-gsheets/`）を確認したところ、以下のエラーで確定的に失敗していることが判明した。

```
Server stderr: bash: /root/xClaude/projects/w002/scripts/mcp_gsheets_launch.sh: No such file or directory
Connection failed after 10ms: MCP error -32000: Connection closed
```

`.mcp.json` の起動コマンドは `${CLAUDE_PROJECT_DIR}/scripts/mcp_gsheets_launch.sh` を直接実行する形になっていたが、`CLAUDE_PROJECT_DIR` がリポジトリルートではなく**セッション起動時の cwd**（`projects/w002` など）に展開されるローカル環境では、存在しないパスを叩いて即座に接続断していた。

これは 2026-07-05 の対策（`$HOME` 決め打ち → `${CLAUDE_PROJECT_DIR}` 決め打ち。リモートコンテナで `$HOME` がリポジトリの親ディレクトリと一致しない問題への対応）による退行で、ローカルで `projects/` 配下から起動するケース（2026-07-03 に一度対策済みだった経路）が再び壊れていた。

## 実施内容

- `.mcp.json` の mcp-gsheets 起動コマンドを、`CLAUDE_PROJECT_DIR`（未設定なら `$PWD`）を起点に親ディレクトリを1階層ずつ辿りながら `scripts/mcp_gsheets_launch.sh` を探索し、見つかった時点で `exec` する方式に変更。
- 探索してもどこにも見つからない場合の最終フォールバックとして `$HOME/xClaude/scripts/mcp_gsheets_launch.sh` を実行する行を残した。
- `scripts/mcp_gsheets_launch.sh` 自体はパス解決が `BASH_SOURCE` 起点で健全だったため変更不要。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.mcp.json` | mcp-gsheets の起動 `args` を、`CLAUDE_PROJECT_DIR` 直下決め打ちから上方探索＋`$HOME/xClaude` フォールバック方式に変更 |

## 設計判断

`CLAUDE_PROJECT_DIR` を「リポジトリルート」ではなく「セッション起動 cwd」として扱う実行環境がある前提に立ち、特定の1経路（ルート固定 or `$HOME` 固定）に依存しない探索方式にした。これにより、過去に個別対策してきた3つのケース（ローカル・ルート起動／ローカル・`projects/` 配下起動／リモートコンテナの `$HOME` 不一致）を1つのロジックで同時に満たせる。

## 確認結果

- 修正後の起動コマンドを3パターンの環境変数で手動実行し、いずれも `initialize` リクエストに対して `serverInfo: spreadsheet` の正常応答を確認：
  - `CLAUDE_PROJECT_DIR=/root/xClaude/projects/w002`（今回のバグ再現条件）
  - `CLAUDE_PROJECT_DIR=/root/xClaude`（ルート起動・routine 相当）
  - `CLAUDE_PROJECT_DIR` 未設定・cwd=`/`（最終フォールバック経路）
- `/mcp` で mcp-gsheets を reconnect し、`Reconnected to mcp-gsheets.` を確認。

## 今後の課題

- リモート/routine コンテナでの動作は未検証（次回リモート実行時に `logs/mcp_gsheets_launch.log` と MCP 接続ログで確認する）。
