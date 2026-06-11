---
title: writer_note-story を本文フェーズ専用に絞り込み
date: 2026-06-11
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260611_writer_note_story_body_phase_only/)

## 背景・動機

`projects/note-story/spec.md` の制作フローは 15 ステップから成る note 記事制作の全体仕様だが、これまで `writer_note-story` スキル（369行）が構成フェーズ・本文・6000字チェック・演出チェック・ファクトチェック・保存・Drive アップロード・シート更新・メール送信までほぼ全工程を一括で抱えていた。

スキルの責務を「本文フェーズ・6000字チェック・演出セルフチェック」の3工程だけに絞り、ネタ選定・構成承認・ファクトチェック・保存・通知といった前後工程は外側の制作フロー（spec.md を実行する側）が担当する構成に分離する。これによりスキルは「承認済み構成を受け取って本文を書き上げて返す純粋なライター」になり、フローの組み替えや単体テストがしやすくなる。

あわせて、勝手な WebSearch で信頼度不明な情報を記事に書く事故を防ぐため、史実・出典の根拠を `notebook-id.md` の notebook ソースのみに限定した。

## 実施内容

- 現行スキルを `writer_note-story_old/` に丸ごとバックアップ（`metadata.yaml` には未登録 → Wiki に出さない）。
- `writer_note-story/SKILL.md` を本文フェーズ専用に縮小（369行 → 約215行）。
  - 削除：ネタ取り扱い／構成フェーズ／構成承認ゲート／ファクトチェック／保存・Drive・シート更新・メール送信／構成相談系の出力スタイル。
  - 新設：「入力」（plan.md / brand.md / draft/agenda.md / notebook-id.md / reference を読み込む）、「前提」（構成は承認済み）、「ソースの取り扱い（最重要）」（notebook ソース限定・勝手な WebSearch 禁止）。
  - 改変：想定読者を `plan.md` の Audience に従う形へ。文体・演出は `brand.md` を唯一の権威にし、`style/style-note-story.md` の参照を撤廃。
  - 「本文フェーズのルール」「6000字チェック」「演出セルフチェック」を独立見出し化。演出チェックから出典・文献番号形式（`[^N]`）の項目は brand.md と重複するため除外。
- `projects/note-story/spec.md` の制作フロー step6-8 を `/writer_note-story` への委譲として明記（step6 で agenda.md＋plan.md＋brand.md を渡す）。step9 以降は外側工程として据え置き。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/writer_note-story/SKILL.md` | 本文フェーズ専用に縮小・入力/ソース取り扱いルール追加 |
| `.claude/skills/writer_note-story_old/`（新規） | 旧スキルのバックアップ（SKILL.md / references / examples） |
| `projects/note-story/spec.md` | 制作フロー step6-8 を /writer_note-story への委譲として明記 |

## 設計判断

- バックアップ（_old）は `metadata.yaml` に登録しない方針とした。Wiki 自動生成（`update_wiki_skills.py`）は metadata.yaml を参照するため、未登録ならスキル一覧・Wiki に現れず、純粋な退避用として保持できる。
- 文体・演出の二重定義を避けるため、`style/style-note-story.md` は参照せず `brand.md` を唯一の権威とした（ファイル自体は残置）。スキル内に残した中核ルールと brand.md が矛盾する場合は brand.md を優先する旨を明記。

## 確認結果

- `grep` で旧工程の記述（構成フェーズ／check-fact／drive_put／send_gmail／sheets_update_values／style-note-story）がスキルから消えていることを確認。
- 「本文フェーズのルール」「6000字チェック」「演出セルフチェック」の3見出しが存在することを確認。
- `metadata.yaml` に `writer_note-story_old` が無いことを確認。
- バックアップ `writer_note-story_old/SKILL.md` が変更前の SKILL.md と完全一致することを `diff` で確認。
