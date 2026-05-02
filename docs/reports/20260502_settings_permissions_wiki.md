---
title: Wiki構築で使用した操作の permissions.allow 追加
date: 2026-05-02
tags: [infra]
---

← [変更ログへ](../changelog.md#wiki構築で使用した操作をpermissionsallowに追加)

## 背景・動機

Wiki 構築作業中に Write・Edit・mkdir・cp・npm・grep を使用したが、コミット前の確認を怠り事後対応になった。ルール通りに確認・追記する。

## 実施内容

- `settings.json` の `permissions.allow` に以下を追加
  - `Write` — ファイル新規作成
  - `Edit` — ファイル編集
  - `Bash(mkdir -p *)` — ディレクトリ作成
  - `Bash(cp -r *)` — ファイルコピー
  - `Bash(npm *)` — npm install / build / ci
  - `Bash(grep *)` — ファイル内検索

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | permissions.allow に6エントリ追加 |

## 設計判断

`rm`（削除）と `sed -i`（一括置換）はリスクが高いためユーザーが除外。削除・破壊的操作は毎回確認を取る方針を維持する。
