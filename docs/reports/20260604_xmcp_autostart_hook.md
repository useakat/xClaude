---
title: xmcp 自動起動 hook 追加・パスの環境非依存化
date: 2026-06-04
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

自前の X MCP サーバー（xmcp）は手動起動が必要で、起動を忘れると X 関連ツールが使えなかった。また `.claude/settings.json` の permissions・hook に `/root` と `/home/useakat` のパスがハードコードされており、環境（ローカル / リモート）が変わると動作しない問題があった。セッション開始時に自動起動し、パスを環境非依存にする。

## 実施内容

- SessionStart hook で xmcp サーバーを自動起動（`$CLAUDE_PROJECT_DIR` を使用。xmcp が存在しない環境では安全にスキップ）
- permissions / hook 内の `/root`・`/home/useakat` ハードコードを、ファイル名アンカー＋`*xClaude` のワイルドカードに統合
- `mcpServers` の `type` を `sse` から `http` に修正（サーバーの transport=http に整合）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | SessionStart hook 追加・パスの環境非依存化・mcpServers.type を http に修正 |

## 設計判断

絶対パスのハードコードをやめ、`$CLAUDE_PROJECT_DIR` と `*xClaude` ワイルドカードで吸収することで、ローカル・リモートいずれの環境でも同一設定が動くようにした。xmcp 未存在環境ではディレクトリ存在チェックで安全スキップさせ、他プロジェクトでの誤動作を防ぐ。

## 確認結果

セッション開始時に xmcp サーバーが `/tmp/xmcp.log` に起動ログを出力して立ち上がることを確認。
