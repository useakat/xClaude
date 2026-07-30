---
title: GAS の 3M累計インプ記入先を AA列に修正し、clasp を useakat 再認証で本番デプロイ
date: 2026-07-30
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260730_gas_3m_column_fix_clasp_deploy/)

## 背景・動機

「日次記録」シート（発信記録スプレッドシートのタブ）に「週間インプ」列が挿入され、「3M累計インプ」の記入先が Z(26) から AA(27) にシフトした。GAS `gas/DailyMetricsRecord.js` の `recordDailyMetrics` は `IMPRESSIONS_3M: 26`（Z列）に数式を書いていたため、このままでは新設の「週間インプ」列を上書きし、3M累計インプが正しい列に入らない。列位置を修正し、本番の Apps Script に反映する必要があった。

## 実施内容

- **`gas/DailyMetricsRecord.js` の修正**: `DAILY_METRICS_CONFIG.COLUMNS.IMPRESSIONS_3M` を `26`（Z）→ `27`（AA）に変更。3M累計インプの数式は `SUMIFS(R:R, A:A, …)` で R列（インプ）と A列を参照するため、記入先の列変更による数式側の影響はなし。
- **clasp 本番デプロイ（アカウント切替）**: `clasp push` が「The caller does not have permission」で失敗。原因は clasp が別アカウント **kitanagasekids.sys@gmail.com** でログインされており、useakat 所有の GAS を編集する権限が無かったこと（id_token のメールクレームで特定）。
  - 現在の global 認証 `~/.clasprc.json` を `~/.clasprc.kitanagasekids.bak` にバックアップ。
  - `clasp login --redirect-port <port>`（SSH トンネル経由）で **useakat@gmail.com** に再ログイン → `clasp push` 成功（9ファイル反映、`DailyMetricsRecord.js` 本番反映）。
  - useakat 認証を `gas/.clasprc.json`（プロジェクトローカル）に保存し、global は kitanagasekids に復元（他プロジェクトの clasp 認証を温存）。
- **秘密ファイル保護**: プロジェクトローカルの `gas/.clasprc.json`（OAuth トークン）が git 追跡対象だったため、`.gitignore` に `.clasprc.json` / `gas/.clasprc.json` を追加。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `gas/DailyMetricsRecord.js` | `IMPRESSIONS_3M` を 26（Z）→27（AA）に変更 |
| `.gitignore` | `.clasprc.json` / `gas/.clasprc.json` を追加（clasp OAuth トークン保護） |
| `gas/.clasprc.json`（gitignore・非コミット） | useakat の clasp 認証をプロジェクトローカルに保存 |

## 確認結果

- シート見出しを実確認：Z(26)=「週間インプ」、AA(27)=「3M累計インプ」。
- `clasp push` 成功（`Pushed 9 files`、useakat@gmail.com 認証）。
- `git check-ignore gas/.clasprc.json` で ignore 済みを確認。git status に clasprc が現れないことを確認。
- global `~/.clasprc.json` が kitanagasekids に復元されていることを確認。

## 設計判断・今後

- **clasp 認証はプロジェクトローカルに分離**：この GAS は useakat 所有、別プロジェクトは kitanagasekids と、アカウントが異なる。global を上書きせず `gas/.clasprc.json` に useakat 認証を置くことで、両プロジェクトの clasp 操作を共存させた。今後この GAS を deploy する際は `gas/` ディレクトリ内で `clasp push` する。
- **GAS の反映は clasp push が必要**（コミットだけでは本番に反映されない）。列変更のような GAS 修正は push 忘れに注意。
