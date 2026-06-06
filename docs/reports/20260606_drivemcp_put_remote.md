---
title: リモートセッション用 Drive アップロードスクリプト追加
date: 2026-06-06
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260606_20260606_drivemcp_put_remote/)

## 背景・動機

gws CLI をリモートセッションで使えるようにするため、OAuth 認証情報をクラウド環境変数に base64 で保存する方式を検討した。しかし `.encryption_key` と `credentials.enc` をセットでクラウドに置くと暗号化が無意味になり、Gmail・Drive への OAuth トークンが事実上平文でクラウドに晒されるリスクがある。

既存のダウンロードスクリプト（`drivemcp_get_remote.sh`）と同じアーキテクチャで、Drive MCP 経由のアップロードのみを対応することにした。gws 全体のリモート対応は諦め、唯一の穴だった「Drive アップロード」だけを解決する最小限の対応。

## 実施内容

- `scripts/drivemcp_put_remote.sh` を新規作成
  - `drivemcp_get_remote.sh` と同じ Anthropic MCP プロキシ経由のアーキテクチャ
  - Drive MCP の `create_file` ツールを呼び出してアップロード
  - ローカルファイルを base64 エンコードして送信
  - デフォルトアップロード先: drafts-note フォルダ（`1j58LBOYgjiOf1RAGdwFcrQSmVKiT00BP`）
- `CLAUDE.md` に Drive アップロードのルールを追記
  - ローカル: `drive_put.sh`、リモート: `drivemcp_put_remote.sh`

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/drivemcp_put_remote.sh` | 新規作成（リモート専用 Drive アップロード） |
| `CLAUDE.md` | Drive アップロードのルールセクションを追加 |

## 設計判断

- **gws 全体リモート対応を断念**: セキュリティリスク（OAuth トークン平文保存）が対応コストに見合わない
- **Drive MCP の制約**: `create_file` のみ対応で `update_file` は非対応のため、リモートでは常に新規ファイル作成になる（既存ファイル上書きは不可）
- **ローカルと同一インターフェース**: `<local-file> [folder-id]` の引数形式を `drive_put.sh` に合わせた

## 確認結果

スクリプトファイル作成・実行権限付与を確認。実際のリモートセッションでの動作確認は次回リモート実行時に行う。

## 今後の課題

- Drive MCP に `update_file` 相当の API が追加された場合、既存ファイル更新にも対応できる
- `gws_remote_support.md` に記載の代替案（refresh_token 直接利用）は難易度が高いため保留
