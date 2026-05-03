---
title: Drive 同期フロー
description: ローカルファイルと Google Drive の同期フロー
---

## outputs/ → Drive 同期

note 記事原稿など `outputs/` の成果物を Google Drive に同期する。

```bash
bash scripts/sync_to_drive.sh
```

または `/sync-to-drive` スキルで実行。

## database/ → Sheets 同期（廃止済み）

Google Sheets が唯一のデータストアになったため、database/ → Sheets の同期は不要。
各スキルは mcp-gsheets ツールを直接使用して Sheets を読み書きする。
`/sync-to-sheets` スキルも廃止済み。

## 個別ファイルの操作

```bash
# ローカル md を Drive にアップロード
bash scripts/drive_put.sh <ファイルパス>

# Drive からファイルをダウンロード
bash scripts/drive_get.sh <Drive ファイル ID>
```

## 注意事項

- `drive_put.sh` はローカルファイル名と同名の Drive ファイルがあれば更新する
- すべて gws CLI 経由で実行する（Python SDK は使わない）
- 認証情報は `~/.config/gws/` に統一
