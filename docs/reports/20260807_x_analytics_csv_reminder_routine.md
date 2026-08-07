---
title: X アナリティクス月次CSVアップロードの月次リマインド routine を新設
date: 2026-08-07
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

マネタイズ月報（`reporter-monetization`）の note 導線（CTR/CVR）は、X投稿一覧のリンククリック列に依存する。この列は X アナリティクスの月次CSVを Drive にアップし `update-x-analytics` で取り込んで初めて埋まる。2026-07 の試作時、7月CSVのアップ忘れで導線が測れず手動対応が必要になった。アップロードを忘れないよう、毎月リマインドする仕組みを作った。

## 実施内容

- **cloud routine を新設**（RemoteTrigger / claude.ai code routines）。リポジトリのコード変更は無し（API 側のスケジュール登録）。
  - 名前: `Xアナリティクス月次CSVアップロード リマインド`
  - スケジュール: 毎月1日 09:00 JST（cron `0 0 1 * *`＝UTC 0:00）
  - 動作: Google Drive を検索し**前月分の X アナリティクスCSV**（ファイル名に `account_analytics_content_{前月YYYY-MM}` を含む・trashed=false）があるか確認。**無ければ** useakat@gmail.com にリマインドメールを送信、**あれば**何もしない（ナガらない設計）。
  - 環境: Default（`env_01TNPFtqE8u1RSFCsNSTn53x`）／モデル: claude-sonnet-5
  - コネクタ: Google-Drive（検索）＋ Gmail（送信）
  - routine ID: `trig_01WhHLFmPuok7f4idXnbaPdY`（初回実行 2026-09-01）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| （リポジトリ変更なし） | cloud routine を API で登録。実体は claude.ai 側 |

## 確認結果

- RemoteTrigger create が HTTP 200、`next_run_at=2026-09-01T00:05Z`（＝9/1 09:05 JST）を確認。
- ロジック上、前月CSVが既にある月はメールを送らず「アップ済み」で終了、無い月のみ送信。

## 今後の課題

- リマインドの実効性は初回（9/1）の動作で確認する。もし Drive 検索が別フォルダを拾えない等あれば routine プロンプトを調整する。
- 恒久的には、X アナリティクスCSVのエクスポート自体を自動化できると理想（現状はよーんの手動エクスポートが必要）。
