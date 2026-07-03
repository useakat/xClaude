---
title: mcp-gsheets 起動を prefer-offline → ローカルインストール方式に変更（フレッシュコンテナの ETARGET 回避）
date: 2026-07-03
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260703_mcp_gsheets_local_install/)

## 背景・動機

同日先行の変更（[prefer-offline + 版固定化](./20260703_mcp_gsheets_prefer_offline_pin/)）で、起動ラッパーを `npx --prefer-offline -y mcp-gsheets@1.8.1` にしていた。これはレジストリ不通時の再接続ハング（-32000）対策としては有効だったが、**フレッシュなクラウドコンテナ**（routine / agent 実行環境）で別の障害を引き起こした。

- クラウドコンテナは構築時に npm メタデータキャッシュがシードされるが、その内容が陳腐化していることがある。
- `mcp-gsheets@1.8.1` の transitive 依存が新しい版（例: `qs@^6.15.2`）を要求すると、`--prefer-offline` は**古いキャッシュのメタデータを再検証せず優先**するため「該当バージョンなし」と判断する。
- 結果、`npm error code ETARGET / No matching version found for qs@^6.15.2` で install ごと失敗 → サーバプロセスが起動せず → MCP が **"still connecting" のまま接続不能**。

実際に routine 実行中に mcp-gsheets が接続できず、代替としてサービスアカウント JWT を自前で発行して Sheets REST API を直叩きする必要が生じた。原因調査で、`--prefer-offline` × 陳腐キャッシュ × transitive 依存のバージョン更新という組み合わせが確定した（`--prefer-online` では `Google Sheets MCP server running on stdio` で正常起動することを再現確認）。

`--prefer-offline` は「キャッシュは常に十分新しい」という前提を無条件に置いており、その前提はフレッシュコンテナでは保証されない。前提そのものをラッパー内で解消する方式（案2）に変更した。

## 実施内容

- `scripts/mcp_gsheets_launch.sh` の起動方式を、**バージョン固定のローカル prefix install ＋ `node` 直接起動**に変更。
  - `~/.cache/mcp-gsheets/<VERSION>` にワンショット `npm install --prefix` し、`.installed` マーカーで完了管理。
  - マーカー未達（＝キャッシュミス / 新バージョン / 中断された部分インストール）のときだけ、丸ごと入れ直して online 取得。
  - 以降の spawn/reconnect は npm/レジストリを一切介さず `exec node .../dist/index.js` で即起動。
  - install の進捗ログは stderr へ隔離し、JSON-RPC 用の stdout を汚さない。
- 認証ロジック（`GOOGLE_APPLICATION_CREDENTIALS` の unset ＋ `GOOGLE_SERVICE_ACCOUNT_KEY` 補完）は変更なし。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/mcp_gsheets_launch.sh` | 末尾の `exec npx --prefer-offline -y mcp-gsheets@1.8.1` を、バージョン固定ローカルインストール（初回のみ online）＋ `exec node <entry>` に置換。認証整備部は不変。 |

## 設計判断

案1（環境側で npm キャッシュを事前ウォーム）と案2（ラッパー内で前提を解消）を比較し、案2を採用。

- 案1は「setup/フックが Claude 起動より前に、毎回、全環境で確実に走る」という**外部の隠れ前提**を新設する対症療法で、環境が変わると再発する。
- 案2は壊れやすい前提（キャッシュは新しい）を**ラッパー自身の中で無効化**する。どの起動経路・環境でも自己完結し、コールドキャッシュなら自動で online 解決へ落ちる。
- ローカル prefix install 方式にしたのは、npx のキャッシュキー内部仕様に依存せず**決定論的**で、2回目以降は npm を全く介さないため旧 `--prefer-offline` の狙い（レジストリ非依存の高速・堅牢な再接続）も同時に満たせるため。

## 確認結果

- `bash -n` 構文チェック: OK。
- コールド起動（`~/.cache/mcp-gsheets/1.8.1` 削除後）: `added 157 packages` の後 `Google Sheets MCP server running on stdio`、stdout はクリーン、`.installed` マーカー生成を確認。
- ウォーム起動: npm 出力なしで即 `running on stdio`、stdout クリーンを確認。
- 認証は現行サーバで疎通済み・env も同一のため、新ランチャでも同一認証で動作。

## 今後の課題

- 新方式が実際の MCP 再接続で効くのは次セッション以降。既存の稼働中プロセスには反映されない（想定内）。
- `qs` のような transitive 依存の版ずれは他パッケージでも起こり得るが、本方式はローカルインストールで都度解決するため個別対応は不要。
