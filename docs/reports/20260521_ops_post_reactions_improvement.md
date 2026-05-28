---
title: ops_post-reactions スキル改善：非フォロワー分類の精度向上
date: 2026-05-21
tags: [skill, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260521_ops_postreactions_improvement_and_target_reader_session/)

## 背景・動機

ops_post-reactions スキルの初回実行（「実は、」ワンポイント解説投稿の反応分析）で、非フォロワーの LLM 分類精度が不十分だった。bio が短い・空欄のユーザーが多く、bio だけでは判断できないケースが頻発した。また、fetch_target_posts.py が date フィールドを人間可読な文字列（例: "May 21, 2026"）で保存していたため、日付比較ロジックが機能しない不具合もあった。

## 実施内容

- `fetch_sheet_replies.py`：GAS シートの E 列（ポスト本文）を `reaction_text` フィールドとして取得するよう追加
- `SKILL.md` の STEP 3・5 を更新：非フォロワー LLM 分類の入力データに `reaction_text`（リプライ本文）・`description`（bio）・`followers_count`・`following_count` をすべて含めるよう明記
- `compute_metrics.py`：`follower_persona_llm.json` の `{"results": [...]}` 形式と直接リスト形式の両方を受け付けるよう修正
- `fetch_target_posts.py`：date フィールドを ISO 8601 形式（`YYYY-MM-DD`）で保存するよう修正

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/ops_post-reactions/fetch_sheet_replies.py` | E列（ポスト本文）を `reaction_text` として出力に追加 |
| `scripts/ops_post-reactions/compute_metrics.py` | follower_persona_llm.json の `{"results":[...]}` 形式に対応 |
| `scripts/ops_post-reactions/fetch_target_posts.py` | date フィールドを ISO 形式（YYYY-MM-DD）で保存 |
| `.claude/skills/ops_post-reactions/SKILL.md` | STEP 3・5 の LLM 分類入力に reaction_text・bio・公開指標を追加 |

## 設計判断

bio のみで 19 ペルソナに分類するのは元々無理があった。「その人が実際に書いた反応文章（reaction_text）」は最も直接的な分類根拠であり、bio 不足を補う最強の手がかりとなる。xmcp 経由の引用RT取得でも reaction_text は取得済みであったが、GAS シートからのリプライデータには含まれていなかったため、スクリプト側で追加した。

## 確認結果

「実は、」ワンポイント解説投稿31件・反応者406人の分析で、非フォロワー350人を4バッチ並列 LLM 分類し、365件の分類結果を取得。reaction_text を活用することで P01（文系会社員）・P12（ユーモア系）などの分類精度が向上した。
