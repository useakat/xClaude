---
title: UpdateXAnalytics GAS 実装
date: 2026-05-18
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md)

## 背景・動機

X アナリティクスの CSV（詳細表示・リンククリック・フォロー増）を X投稿一覧シートに反映する処理は、これまで Claude エージェント（`update-x-analytics`）が手動トリガーで実行していた。
定期自動実行には GAS トリガーが適しているため、同処理を GAS 関数として実装し clasp でデプロイした。
あわせて GAS プロジェクトをローカルで編集できるよう clasp でクローンし、バージョン管理下（`gas/`）に置いた。

## 実施内容

- `gas/UpdateXAnalytics.js` を新規作成
  - `updateXAnalytics()` — Drive の Xanalytics/tmp フォルダから最新 CSV を取得し、X投稿一覧 AA:AC 列（詳細表示・リンククリック・フォロー増）を更新するメイン関数
  - `getLatestAnalyticsCsv_()` — 更新日時が最も新しい CSV ファイルを返す
  - `parseAnalyticsCsv_()` — `Utilities.parseCsv` で CSV をパースし `{statusId: metrics}` マップを生成（Post Link 列インデックス 3、New follows 9、Detail Expands 13、URL Clicks 14）
  - `getSheetStatusIdMap_()` — B 列の URL から `{statusId: 行番号}` マップを作成
  - `batchWriteUpdates_()` — 連続する行をまとめて `setValues` し API 呼び出しを最小化
  - `ensureAnalyticsHeaders_()` — AA1:AC1 にヘッダーがなければ自動設定
  - `setWeeklyAnalyticsTrigger()` — 毎週月曜 7:00 のトリガーを設定するヘルパー
- `clasp push` で既存 GAS プロジェクト（Script ID: `1tm5Zx93MQ9n8n02hN5t46pJIdPE5MoOTGSudYpTuR5z2EOJYVQ5CCSdU`）にデプロイ

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `gas/UpdateXAnalytics.js` | GAS 関数新規作成 |
| `gas/` | clasp クローンで取得した既存 GAS プロジェクト全体 |

## 設計判断

- **フォルダ指定**: Drive フォルダ ID `1J45co5hN74gzxNateNRyeDtswZu0lMr3`（Xanalytics/tmp）を直接使用。MimeType.CSV でフィルタし更新日時で最新を選択。
- **CSV 列マッチ**: シートの URL は `twitter.com/i/web/status/{ID}`、CSV は `x.com/usephys/status/{ID}` と形式が異なるため、正規表現で数値 ID のみ抽出して照合。
- **バッチ書き込み**: 連続する行は1回の `setValues` にまとめ、飛び行は分割して書き込む。API 呼び出し回数を最小化しつつ実装をシンプルに保った。

## 確認結果

`clasp push` が 8 ファイル正常にプッシュされたことを確認。Apps Script エディタから `updateXAnalytics` を手動実行して動作を確認すること。

## 今後の課題

- `setWeeklyAnalyticsTrigger()` を手動実行して週次自動実行トリガーを設定する
- CSV のアップロード運用（Xanalytics/tmp フォルダへの配置）とトリガー実行タイミングの調整
