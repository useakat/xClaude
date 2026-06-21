---
title: W003 制作フローにチャット履歴保存ステップを追加
date: 2026-06-21
tags: [workflow, skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260621_w003_chat_history_step/)

## 背景・動機

直前に W003 制作フローへ「投稿フォルダを Drive へアップロード」工程を追加した（[drive_put_folder.sh 新設](20260621_w003_post_folder_drive_upload/)）。投稿の制作過程（どう調べ、どう判断し、どう直したか）はチャットに残っており、これも投稿フォルダに同梱して Drive に残しておきたい、というよーんの依頼。

これにより、各投稿テーマフォルダに原稿・図解・プロンプトに加えて**制作チャット履歴**が揃い、Drive アップロードで一括アーカイブされる。

## 実施内容

- **`projects/w003/spec.md`**: 制作フローの Gmail 下書き（Step 8）と Drive アップロードの間に **Step 9「チャット履歴を保存」** を挿入。`save_session_history.py` で Markdown 化し、生成物をテーマフォルダ直下に `chat_history.md` としてコピーする。Drive アップロードは Step 10 に繰り下げ。Verification に「チャット履歴 `chat_history.md` が投稿フォルダに保存されている」を追加。
- **`.claude/skills/daily-xonepoint/SKILL.md`**: 同様に **STEP 8「チャット履歴を保存」** を追加し、Drive アップロードを STEP 9 に繰り下げ。完了判定を「STEP 1〜9」に更新し、報告項目に「✅ チャット履歴保存完了（chat_history.md）」を追加。

既存の `scripts/save_session_history.py`（JSONL→Markdown 変換）を再利用し、生成物をテーマフォルダにコピーする方式とした。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/w003/spec.md` | 制作フローに Step 9（チャット履歴保存）を挿入・Drive を Step 10 に・Verification に1行追加 |
| `.claude/skills/daily-xonepoint/SKILL.md` | STEP 8（チャット履歴保存）追加・Drive を STEP 9 に・完了判定/報告を更新 |

## 確認結果

- 本セッションで実際に `save_session_history.py` で履歴を生成し、`projects/w003/20260620_血管総延長/chat_history.md`（約77KB）として保存できることを確認。
- spec.md と daily-xonepoint のステップ順序・番号が一致していることを確認（spec.md を正とする運用）。

## 今後の課題

- `save_session_history.py` は `docs/history/` にも生成物を残すため、テーマフォルダ用に使うと副産物が増える。テーマフォルダ直書きオプションの追加余地がある。
