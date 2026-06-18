---
title: gws 認証フロー標準化・check_auth.sh 強化
date: 2026-06-18
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260618_gws_auth_flow_standardization/)

## 背景・動機

6:00 AM の X 投稿 cron が失敗し調査したところ、gws の OAuth トークンに `gmail.modify` スコープが含まれていないことが判明した（13日間気付かなかった）。

原因は、直近の gws 再認証時にスコープ指定を省略したため、デフォルトのみ（email/profile/openid）で認証されていたこと。

この問題の再発を防ぐために2点改善した：

1. **`check_auth.sh` の強化** — gws チェックが `gws auth status`（トークン有効性のみ）だったため、スコープ不足を検知できなかった。Gmail API の実呼び出しに変更してスコープ不足も検出可能にした。

2. **ブラウザ認証フローの標準化** — gws 再認証は「ランダムポートで localhost にコールバック」という仕様上、VPS 環境では SSH トンネルが必要。毎回よーんが手順を説明しなければならなかったのを、Claude Code が自律的にできるようスクリプト化した。

## 実施内容

- `scripts/gws_auth.sh` を新設。gws auth login のラッパー
  - gws をバックグラウンド起動し、stdout から認証 URL とポート番号を抽出
  - `curl ifconfig.me` で VPS 公開 IP を動的取得
  - SSH トンネルコマンドと認証 URL を整形してよーんに提示
  - 認証完了後に `token_cache.json` を自動クリア
- `scripts/check_auth.sh` の gws チェックを強化
  - `gws auth status` → `gws gmail users threads list` による Gmail API 実呼び出しに変更
  - スコープ不足・トークン切れの両方を検知可能に
- `CLAUDE.md` に追記
  - `gws 再認証` セクション：正式なスコープ付き再認証コマンド、キャッシュクリア、コミット手順
  - `ブラウザ認証の実施手順（Claude Code 向け）` セクション：`gws_auth.sh` の使い方

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/gws_auth.sh` | 新規作成。gws auth login ラッパー（URL抽出・SSH トンネル指示・IP 自動取得） |
| `scripts/check_auth.sh` | gws チェックを `gws auth status` から Gmail API 実呼び出しに変更（L15-23） |
| `CLAUDE.md` | gws 再認証手順・ブラウザ認証フロー標準化の手順を追記 |

## 設計判断

**gws_auth.sh のポーリング方式**: `gws auth login` が出力する URL を stdout から取得するため、バックグラウンド起動＋一時ファイルへのリダイレクト＋ポーリング（0.5秒×30回）方式とした。`timeout` コマンドで包む方法は認証完了前にプロセスが終了するため不適。

**IP 動的取得**: VPS IP はスクリプト実行時に `curl ifconfig.me` で取得する。ハードコードすると IP 変更時に壊れるため。

## 確認結果

gws 再認証後、`gws gmail users threads list` で Gmail API が正常に応答することを確認。`check_auth.sh` が `✅ gws: OK` を出力することを確認。
