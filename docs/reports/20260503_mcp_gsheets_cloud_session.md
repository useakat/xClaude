---
title: mcp-gsheets の cloud session 対応
date: 2026-05-03
tags: [infra]
---

← [変更ログへ](../changelog/)

## 背景・動機

remote session（Anthropic の cloud VM）で Google Sheets を読み書きしたいという要件が発生。当初 `settings.json` に command 型で `mcp-gsheets` を登録したが、cloud session は `command` 型 MCP を起動できないことが判明。試行錯誤を経て `.mcp.json` による command 型で統一する構成に落ち着いた。

## 実施内容

- `settings.json` に command 型 `mcp-gsheets` を追加（初期対応）
- cloud session が `command` 型を起動できないと判明 → supergateway で stdio→HTTP 変換する http 型に変更
- cloud session は `localhost` に届かないと判明 → supergateway も不使用に
- `.mcp.json` を新設し command 型で定義（repo に含まれるため cloud session でも clone される）
- 認証は `GOOGLE_SERVICE_ACCOUNT_KEY`（サービスアカウント JSON 文字列）を cloud environment の環境変数に設定
- `settings.json` の supergateway エントリ・SessionStart フックを削除して `.mcp.json` に一本化

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.mcp.json` | 新規作成。command 型 mcp-gsheets を定義、`GOOGLE_SERVICE_ACCOUNT_KEY` 環境変数を参照 |
| `.claude/settings.json` | mcp-gsheets の http 型エントリと supergateway SessionStart フックを削除 |

## 設計判断

- **`.mcp.json` vs `settings.json`**：`settings.json` の `mcpServers` は local session 専用（http 型のみ有効）。`.mcp.json` は repo に含まれるため cloud session でも有効で、command 型も動作する。
- **認証方式**：ファイルパス（`GOOGLE_APPLICATION_CREDENTIALS`）は cloud VM に存在しないため環境変数方式を採用。フル JSON を1行で渡す `GOOGLE_SERVICE_ACCOUNT_KEY` を選択。

## 確認結果

cloud session で `sheets_get_values` ツールが認識されることを確認。

## 今後の課題

- `GOOGLE_SERVICE_ACCOUNT_KEY` は cloud environment の UI に手動で設定が必要。secrets store が整備されたら移行を検討。
