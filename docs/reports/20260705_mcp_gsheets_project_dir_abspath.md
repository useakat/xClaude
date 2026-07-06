---
title: mcp-gsheets 起動コマンドを $HOME 決め打ちから ${CLAUDE_PROJECT_DIR} に変更し、routine 未接続を解消
date: 2026-07-05
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

`/reporter-daily` routine 実行時、mcp-gsheets が「接続中」リストにすら現れず `sheets_get_values` 系ツールが一切使えない事象が発生した。

`logs/mcp_gsheets_launch.log` を確認すると、SessionStart hook による事前インストール（`install:` ログ）は正常に完了していたが、`mcp_gsheets_launch.sh` 自身のログ（`launch:` プレフィックス）が一切記録されていなかった。これは `.mcp.json` が指定する起動コマンド自体が実行されていないことを意味する。

`.mcp.json` の起動コマンドを実際にこのセッションで再現したところ、原因が判明した：

```
$ echo $HOME
/root
$ bash -c 'exec bash "$HOME/xClaude/scripts/mcp_gsheets_launch.sh"'
bash: /root/xClaude/scripts/mcp_gsheets_launch.sh: No such file or directory
```

7/3 の abspath 対策（[→報告書](../20260703_mcp_gsheets_launch_abspath/)）で `.mcp.json` の起動コマンドを `$HOME/xClaude/...` の絶対パスに変更した際、「本リポジトリはローカル・リモート含め `$HOME/xClaude` 配置を前提とする」という設計判断を置いていた。しかし今回のコンテナでは `$HOME=/root` である一方、実際のリポジトリは `/home/user/xClaude` に clone されており、この前提が成立していなかった。

この不一致はコンテナごとに発生したりしなかったりする（6月中や当日朝6:13の実行では `$HOME` とリポジトリ位置がたまたま一致し正常動作していた）ため、断続的な「繋がる日と繋がらない日がある」という症状として現れていた。

## 実施内容

- `.mcp.json` の mcp-gsheets 起動コマンドを `$HOME/xClaude/...` から `${CLAUDE_PROJECT_DIR}/...`（Claude Code がリポジトリルートを指して渡す環境変数）に変更。
- `mcp_gsheets_launch.sh` / `mcp_gsheets_install.sh` 内部は 7/4 対策で既に `BASH_SOURCE` 起点のパス解決に変更済みのため、変更不要。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.mcp.json` | mcp-gsheets の起動コマンドを `$HOME/xClaude/scripts/mcp_gsheets_launch.sh` → `${CLAUDE_PROJECT_DIR}/scripts/mcp_gsheets_launch.sh` に変更 |

## 設計判断

- **`$HOME` ではなく `${CLAUDE_PROJECT_DIR}` を採用**：`$HOME` はコンテナの構成によってリポジトリの置き場所と一致するとは限らないが、`${CLAUDE_PROJECT_DIR}` は Claude Code が MCP サーバー起動時・hook 実行時のいずれにも渡す、リポジトリルートを直接指す変数であり、環境間の可搬性が高い。SessionStart hook 側は元々この変数を使っており、既に安定して動作していたことも採用の裏付けとした。

## 確認結果

- `.mcp.json` の JSON バリデーション：OK。
- 新コマンドを、今回の不具合と同じ `$HOME=/root`（リポジトリ実体と不一致）の状態で `CLAUDE_PROJECT_DIR=/home/user/xClaude` を指定して実行 → `Google Sheets MCP server running on stdio` 相当の起動状態（プロセス常駐）を確認。`logs/mcp_gsheets_launch.log` に `launch: ensure install` → `launch: node exec: ...` の記録が新たに出力されることを確認（旧コマンドでは一度もこのログが出ていなかった）。
- 同条件で旧コマンド（`$HOME` 決め打ち）を実行すると `No such file or directory`（exit 127）で即失敗することを対比確認。

## 今後の課題

- `.mcp.json` の変更はセッション再接続では読み込まれないため、実際に mcp-gsheets がツールとして接続されるかは次回セッション／次回 routine 実行でしか最終確認できない。次回失敗した場合は `logs/mcp_gsheets_launch.log` に `launch:` 行が出ているかどうかで、今回とは別要因であることを切り分けられる。
