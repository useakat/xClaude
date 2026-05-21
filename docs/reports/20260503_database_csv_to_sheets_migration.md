---
title: database CSV → Google Sheets 移行
date: 2026-05-03
tags: [skill, infra]
---

← [変更ログへ](../changelog/)

## 背景・動機

remote session（Anthropic cloud VM）では git push が必要なため、`database/` の CSV を更新しても即時反映ができなかった。mcp-gsheets が整備されたことで、Google Sheets を唯一のデータストアとし、CSV 読み書きスクリプトを全廃できる条件が揃った。

## 実施内容

- SS1（`1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM`）に `outputs` シートを新設し、ヘッダー行（dateTime, URL, howID）を追加
- 8スキルの CSV / シェルスクリプト呼び出しを mcp-gsheets ツール呼び出しに書き換え
  - `sheets_get_values` で一覧取得・ステータスフィルタ
  - `sheets_update_values` でステータスを「使用済み」に更新
  - `sheets_append_values` で新規ネタ・投稿記録を追記
- 廃止スクリプト 6本を `unused-scripts/` に移動（削除ではなくアーカイブ）
- `sync-to-sheets` スキルを廃止済みに更新
- `.claude/settings.json` の `permissions.allow` から廃止スクリプト呼び出しパターンを削除
- CLAUDE.md のスクリプト一覧・データベース説明・Google サービス連携ルールを更新

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/daily-xonepoint/SKILL.md` | bash CSV 呼び出し → `sheets_get_values` / `sheets_update_values` / `sheets_append_values` |
| `.claude/skills/writer-xonepoint/SKILL.md` | 同上（onePointNeta） |
| `.claude/skills/writer-xnews/SKILL.md` | 同上（newsTopics） |
| `.claude/skills/writer-note/SKILL.md` | 同上（noteNeta） |
| `.claude/skills/research-trivia/SKILL.md` | `sheets_get_values` / `sheets_append_values` に変更 |
| `.claude/skills/research-note-projectx/SKILL.md` | 同上（noteNeta） |
| `.claude/skills/analyze-target/SKILL.md` | CSV 直接参照 → SS2 `sheets_get_values`（persona/pain/what） |
| `.claude/skills/research-plan/SKILL.md` | sheets_manager → `sheets_get_values` に変更 |
| `.claude/skills/sync-to-sheets/SKILL.md` | 廃止済みに更新 |
| `.claude/settings.json` | 廃止スクリプトの permissions.allow エントリを削除 |
| `CLAUDE.md` | database/ 説明を「参照用アーカイブ（読み取り専用）」に変更；廃止スクリプト削除；Sheets 連携ルール更新 |
| `unused-scripts/` | csv_reader.py, update_neta_status.py, sheets_manager.py, sync_to_sheets.sh, push_database.sh, record_output.py を移動 |
| `docs/scripts/index.md` | 廃止スクリプトを「廃止済み → unused-scripts/」セクションに移動 |
| `docs/skills/index.md` | sync-to-sheets を廃止済み表記に変更 |
| `docs/workflows/drive-sync.md` | database/→Sheets 同期セクションを廃止済みに更新 |
| `docs/skills/writer-xonepoint.md` | CSV 参照 → Sheets 参照に更新 |

## 設計判断

廃止スクリプトは削除ではなく `unused-scripts/` に移動した。既存の使用例やスクリプトの実装を参照できるようアーカイブとして残す判断。

ステータス列の行番号特定は `sheets_get_values` の結果から No 列で行う。行番号 = ヘッダー行 (1) + No の位置。

## 確認結果

SS1 に outputs シートが作成され、ヘッダー行が書き込まれていることを gws CLI で確認（sheetId=1064457966）。各スキルの SKILL.md が mcp-gsheets ツール呼び出し形式になっていることをコードレビューで確認。

## 今後の課題

- 次回 remote session でスキル実行し、`sheets_get_values` / `sheets_update_values` が正常動作するか動作確認
- mcp-gsheets がローカルセッションで使えるようになったら、outputs への記録も含めたエンドツーエンドテストを実施
