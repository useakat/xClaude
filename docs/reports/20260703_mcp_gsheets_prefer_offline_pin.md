---
title: mcp-gsheets 起動を prefer-offline + 版固定にして再接続タイムアウト(-32000)を解消
date: 2026-07-03
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260703_mcp_gsheets_prefer_offline_pin/)

## 背景・動機

`/mcp` で `Failed to reconnect to mcp-gsheets: -32000` が発生した。調査したところ、`.mcp.json`・`settings.json`・サービスアカウント認証・起動ラッパーの env 処理はすべて正常で、手動起動では initialize → tools/list → 認証まで問題なく通った。

原因は起動ラッパー `scripts/mcp_gsheets_launch.sh` 最終行の `npx -y mcp-gsheets@latest` にあった。`@latest` タグは spawn/reconnect のたびに npm レジストリへの問い合わせを強制し、この解決がオフライン耐性を持たない。レジストリが一時的に到達不能・低速になると npx がハングし、Claude Code 側の初期化ハンドシェイクがタイムアウトして `-32000` を返す。ネットワーク正常時は 1.7 秒で起動するため、**間欠的**な失敗に見えていた。

加えて `latest` は 1.8.1 を指すが npx キャッシュには 1.8.0 があり、バージョンズレによる再ダウンロードも遅延要因になっていた。

## 実施内容

- レジストリ遮断下での起動を計測し、`@latest` が 60 秒フルにハングして起動しないことを再現・確認。
- `npx --prefer-offline -y mcp-gsheets@1.8.1`（版固定 + prefer-offline）に変更。レジストリ遮断下でも 1.3 秒でキャッシュから起動することを検証。
- ラッパーの他の処理（`GOOGLE_APPLICATION_CREDENTIALS` の unset、KEY 補完のフォールバック）は正常のため変更なし。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/mcp_gsheets_launch.sh` | 最終行を `npx -y mcp-gsheets@latest` → `npx --prefer-offline -y mcp-gsheets@1.8.1` に変更。理由をコメントで明記。 |

## 設計判断

- **版固定のみでは不十分**：`npx -y mcp-gsheets@1.8.0`（版固定だけ）でもレジストリ遮断下でハングした。`-y` は固定版でもレジストリ検証に行くため。
- **`--prefer-offline` を採用**：キャッシュにあればレジストリ round-trip を省く。初回（コールドキャッシュ）だけダウンロードするので導入は従来どおり動く。`--offline` は cache-only で厳格すぎる（初回や別環境で失敗リスク）ため不採用。
- 版固定で自動更新は止まるが、その分再接続が高速・堅牢になる方を優先。更新は手動で `@1.8.x` を上げる運用とする。

## 確認結果

`scripts/mcp_gsheets_launch.sh` を JSON-RPC initialize で叩いて検証：

- 通常起動：1.29 秒で `serverInfo` を含む result を返却 ✅
- レジストリ遮断下（`HTTPS_PROXY=http://127.0.0.1:9`／-32000 の再現条件）：1.28 秒で起動 ✅（従来は 60 秒ハングして失敗）

反映には Claude Code の再起動（または `/mcp` での再接続）が必要。

## 今後の課題

- mcp-gsheets の新バージョンに追従する際は、手動で `@1.8.x` を更新し、キャッシュに載せてから固定版を上げる。
