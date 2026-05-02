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

## database/ → Sheets 同期

`database/*.csv` の内容を Google Sheets に一方向同期する。

```bash
bash scripts/sync_to_sheets.sh
```

または `/sync-to-sheets` スキルで実行。

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
