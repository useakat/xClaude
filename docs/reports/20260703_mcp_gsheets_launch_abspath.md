---
title: mcp-gsheets 起動スクリプトのパスを cwd 非依存の絶対パス化して -32000 を解消
date: 2026-07-03
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md) ｜ [セッション履歴→](../../history/20260703_mcp_gsheets_launch_abspath/)

## 背景・動機

`/mcp` 実行時に `Failed to reconnect to mcp-gsheets: -32000` が繰り返し発生し、再起動しても解消しなかった。

原因は `.mcp.json`（`/root/xClaude/.mcp.json`）の起動指定が**相対パス**だったこと：

```json
"args": ["scripts/mcp_gsheets_launch.sh"]
```

Claude Code は MCP サーバーを**セッションの作業ディレクトリを cwd として起動**する。従来はルート `/root/xClaude` からセッションを開いていたため相対パスで解決できていたが、`projects/w001` などサブプロジェクトを作業ディレクトリにすると `projects/w001/scripts/mcp_gsheets_launch.sh` を探して見つからず、プロセスが即終了 → 再接続タイムアウト(-32000) を招いていた。再起動で直らなかったのは cwd が変わらないため。

前回の prefer-offline + 版固定対処（[→報告書](./20260703_mcp_gsheets_prefer_offline_pin/)）は起動の速さ・堅牢性を上げたが、相対パス問題は別要因として残っていた。

## 実施内容

- `.mcp.json` の起動指定を、cwd に依存しない `$HOME` 基準の絶対パス起動に変更
- `bash -c 'exec bash "$HOME/xClaude/scripts/mcp_gsheets_launch.sh"'` 形式にし、bash が cwd に関係なく `$HOME` を展開してラッパーを起動するようにした
- `exec bash <path>` とすることで、ラッパーに実行ビットが無くても起動でき、かつプロセスを差し替えて余分な中間シェルを残さない

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.mcp.json` | mcp-gsheets の args を `["scripts/mcp_gsheets_launch.sh"]` → `["-c", "exec bash \"$HOME/xClaude/scripts/mcp_gsheets_launch.sh\""]` に変更 |

## 設計判断

- **絶対パスをハードコード（`/root/xClaude/...`）せず `$HOME/xClaude/...` にした**：本リポジトリはローカル・リモート含め `$HOME/xClaude` 配置を前提としており（ラッパー内も同じ前提）、`$HOME` 展開なら環境間の移植性を保てる。
- **`exec <path>`（ファイル直接実行）ではなく `exec bash <path>`**：ラッパーに実行ビットが無く `Permission denied` になったため、明示的に `bash` で実行する形にした。

## 確認結果

- 作業ディレクトリ `projects/w001` のまま `bash -c 'exec bash "$HOME/xClaude/scripts/mcp_gsheets_launch.sh"'` を実行し、`Google Sheets MCP server running on stdio` が出て正常起動することを確認。
- 併せて initialize / tools/list を投げ、認証が通って `sheets_get_values` 等のツール一覧が返ることを確認済み。
- 反映には Claude Code の再起動が必要（`.mcp.json` 変更は再接続では読み直されないため）。

## 今後の課題

- 反映（再起動）後に実セッションで `/mcp` が繋がることの最終確認。
