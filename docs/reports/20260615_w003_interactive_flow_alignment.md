---
title: W003 制作フローを spec.md 基準で対話化（trivia研究→ネタ選択→フォルダ作成→画像承認）
date: 2026-06-15
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260615_w003_interactive_flow_alignment/)

## 背景・動機

W003（X ワンポイント解説）の `spec.md` 制作フローに、ネタ選定の次の2ステップ（① 選定ネタを `/research_trivia-source` に渡して候補を展開しユーザーに選ばせる、② テーマフォルダ作成）を追加した。

その後、spec.md と各スキルの整合性をチェックしたところ、**spec のフロー全体を動かすオーケストレータ `daily-xonepoint`（cron 無人実行・全自動）が新フローと正面衝突**していることが判明した：

- spec の新フローは「候補をユーザーに提示して選択」「画像は承認後に生成」= **ユーザー対話が前提**
- daily-xonepoint は「ユーザー入力を待たない」全自動が前提
- さらに daily-xonepoint には spec が定義するテーマフォルダ作成・draft/output 保存・画像生成ステップが存在しなかった
- writer-xonepoint は `テーマ／冒頭1行案／仕組みのポイント／感情的締め案` の4項目入力を期待していたが、`research_trivia-source` の出力（タイトル・選定理由・出典）とは噛み合わなかった

ユーザー判断で **spec を正**とし、**writer-xonepoint へはテーマのみ渡す**、**daily-xonepoint を完全に対話化（cron 無人実行は廃止を容認）**する方針を採用した。

## 実施内容

- `spec.md` 制作フローに「テーマフォルダ作成」ステップを追加（ネタ選定の次）し、以降のステップ番号を繰り下げ。
- `spec.md` ネタ選定ステップに `/research_trivia-source {ネタ}` 実行＋候補提示＋ユーザー選択を追記。
- `writer-xonepoint` を **テーマ単独入力**で成立するよう修正（冒頭1行案/仕組み/締めは任意扱い）。
- `daily-xonepoint` を spec の8ステップに全面再構成：
  - STEP2: Sheets でシードネタ選定 → `/research_trivia-source` で候補展開 → **ユーザー選択を待つ** → 選択後に使用済み更新
  - STEP3（新）: テーマフォルダ作成（`YYYYMMDD_topic/draft`・`output`）
  - STEP4: writer-xonepoint へテーマのみ渡し `draft/draft.md` 保存
  - STEP5: ファクト→ブランド適合（既存維持）→ `output/` 保存
  - STEP6: Gmail 下書き（既存維持）
  - STEP7（新）: **承認後** `/visual_infographic` 5パターン → `draft/infographic_[連番].png`
- `daily-xonepoint` agent 定義を対話式・cron 廃止に書き換え。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/w003/spec.md` | テーマフォルダ作成ステップ追加、ネタ選定に trivia研究＋ユーザー選択追記、フロー見出しを対話実行に修正、タイトル案の扱いを明記 |
| `.claude/skills/daily-xonepoint/SKILL.md` | spec の8ステップに全面再構成（trivia研究・ユーザー選択・フォルダ作成・draft/output 保存・画像生成）、無人前提の記述を対話前提に書き換え |
| `.claude/skills/writer-xonepoint/SKILL.md` | `$ARGUMENTS` をテーマ単独で成立するよう修正、拡張項目を任意化 |
| `.claude/agents/daily-xonepoint.md` | 自律実行の説明を対話式（STEP2・7で停止）に修正、cron 無人実行廃止を明記 |

## 設計判断

- **spec を正とした**理由：spec.md は W003 プロジェクトの制作仕様の権威であり、フローの追加要件（対話的なネタ選択・テーマフォルダ）はここから発生したため。スキル側を spec に合わせる方が責務が一貫する。
- **テーマのみ渡す**理由：`research_trivia-source` の出力は「テーマ（トリビアネタ）」までで、冒頭1行案・仕組み・締めは生成しない。writer-xonepoint 側が4段構成・フックの構築力を持つため、テーマだけ渡して本文をゼロから構築させる方がシンプル。
- **cron 無人実行の廃止を容認**：ネタ選択・画像承認の2点でユーザー対話を挟む以上、無人 cron では完走しない。対話品質（ネタの吟味・画像承認）を優先した。

## 確認結果

- `spec.md` の8ステップと `daily-xonepoint/SKILL.md` のステップ番号・内容が1対1で対応することを目視確認。
- ローカル crontab・`scripts/` に daily-xonepoint の cron 参照が無いことを確認（無効化対象のローカル cron は無し）。

## 今後の課題

- クラウドのルーティン（`/schedule`）で daily-xonepoint を登録している場合は、対話化により完走しないため無効化が必要。
- 対話化後の通しフロー（ネタ選択停止→フォルダ生成→draft/output 保存→画像承認）の実地動作確認は次回実運用時に行う。
