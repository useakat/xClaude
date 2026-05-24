---
title: drive_put.sh 汎用化：任意フォルダ対応・MIME 自動判定
date: 2026-05-24
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md) ｜ [セッション履歴→](../history/20260524_20260524_drive_put_generalization/)

## 背景・動機

`drive_put.sh` は drafts-note フォルダ固定のアップローダーで、任意フォルダへのアップロードに使えなかった。また更新時の MIME タイプが `text/markdown` にハードコードされており、PDF や JSON など他の形式に対応できていなかった。

当初は OAuth ユーザー認証の Python スクリプト（`drive_upload.py`）を作成したが、CLAUDE.md の「Gmail・Drive の連携は gws CLI を使って実装する」という方針に反するため、`drive_put.sh` の拡張に切り替えた。

## 実施内容

- `drive_put.sh` に第2引数 `[folder-id]` を追加。省略時は従来の drafts-note フォルダ（後方互換）
- 更新時の `--upload-content-type` を `file --mime-type -b` コマンドで自動判定に変更（旧: `text/markdown` 固定）
- 一時追加した `scripts/drive_upload.py`（Python OAuth 版）を削除
- `docs/scripts/index.md` および `CLAUDE.md` の説明文を「フォルダ指定可」に更新
- gws の空レスポンスで JSON 例外が発生する不具合を修正（stdin が空なら空文字扱い）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/drive_put.sh` | 第2引数追加・MIME 自動判定・JSON 例外修正 |
| `scripts/drive_upload.py` | 削除（gws CLI 統一方針のため） |
| `docs/scripts/index.md` | drive_put.sh の説明を更新 |
| `CLAUDE.md` | drive_put.sh の説明を更新 |

## 設計判断

gws CLI を使う方針は CLAUDE.md で明文化されており、Python + google-api-python-client での実装は方針違反になる。`drive_put.sh` の既存スキルからの呼び出し（writer-note・hashtag-note・check-fact）はすべて引数1つで drafts-note を対象としており、第2引数を省略時デフォルトにすることで後方互換を維持した。

## 確認結果

`bash scripts/drive_put.sh ~/.notebooklm/storage_state.json <FOLDER_ID>` でエラーなく実行できることを確認（gws 認証の設定が残タスク）。

## 今後の課題

- gws の認証設定（`gws auth login -s drive`）を完了させる必要がある。client_secret.json は `~/.config/gws/` に配置済み
- gws バイナリは `@googleworkspace/cli@0.11.1`（glibc 2.36 対応版）を npm でインストール済み
