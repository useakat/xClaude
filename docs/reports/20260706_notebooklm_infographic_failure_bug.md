---
title: notebooklm_manager.py インフォグラフィック生成失敗時の誤ダウンロードバグを修正
date: 2026-07-06
tags: [bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260706_notebooklm_infographic_failure_bug/)

## 背景・動機

W003投稿（RTG無充電電源）の画像追加生成中、`notebooklm_manager.py infographic` がAPIレート制限（`USER_DISPLAYABLE_ERROR`）で失敗したにもかかわらず、コマンドは `✓ 保存` と成功表示し、実際には直前に成功していた別パターンの画像を再ダウンロードしていた。3回連続で同じ誤ダウンロードが発生し、生成物の同一性チェック（MD5比較）で初めて発覚した。

原因は `cmd_infographic` / `cmd_make_infographic` の実装で、`generate_infographic` が返す `GenerationStatus` の成否を確認せず、`task_id` が空文字（失敗時の挙動）の場合に `wait_for_completion` をスキップしたあと、無条件で `download_infographic` を呼び出していたため。

## 実施内容

- `cmd_infographic`・`cmd_make_infographic` の両方で、生成完了後に `status.is_complete`（`GenerationStatus.status == "completed"` のプロパティ）を確認する分岐を追加
- 失敗時（`is_complete` が False）は `error` / `error_code` を表示し、`download_infographic` を呼ばずに `sys.exit(1)` で終了するよう変更
- モックで `GenerationStatus(task_id='', status='failed', error='API rate limit or quota exceeded...', error_code='USER_DISPLAYABLE_ERROR')` を返すケースを再現し、`download_infographic` が呼ばれず `SystemExit(1)` になることを確認

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/notebooklm_manager.py` | `cmd_infographic`・`cmd_make_infographic` に生成失敗チェックを追加（成功時のみダウンロード） |

## 確認結果

`unittest.mock` で `NotebookLMClient.from_storage` をモック化し、失敗ステータスを返した際に `download_infographic` が呼ばれないこと・`sys.exit(1)` で終了することを確認済み（実APIのクォータを消費せずに検証）。

## 今後の課題

同様のパターン（`task_id` 空文字時に後続処理を無条件実行）が他の `cmd_*` 関数（動画生成・レポート生成等）にも存在する可能性があるため、次回以降に横展開のレビューが必要。
