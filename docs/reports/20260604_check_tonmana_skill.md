---
title: check-tonmana スキル新設（トンマナ調整＋P01化スコアリングの切り出し）
date: 2026-06-04
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260604_check_tonmana_skill/)

## 背景・動機

`daily-xonepoint` スキルの STEP 4-2（トンマナ調整）・STEP 4-3（P01化スコアリングループ）は、style-xonepoint.md に照らした文体調整と6項目採点ループという独立した処理だが、daily-xonepoint の中にインラインで書き込まれていた。

このロジックは X ワンポイント解説の本文であれば daily-xonepoint 以外（writer 系の単体実行など）からも再利用できる汎用処理であり、独立スキルに切り出すことで再利用性と保守性を高める。採点基準テーブルや書き直しルールを一箇所に集約でき、今後の調整も check-tonmana だけ直せばよくなる。

## 実施内容

- `templates/SKILL_temp.md`（汎用テンプレート）の構造（目的・手順・出力形式・禁止事項）に沿って `check-tonmana` スキルを新設
- daily-xonepoint の STEP 4-2/4-3 の内容（トンマナ調整・P01化採点基準テーブル・ループ手順・書き直しルール・チェックサマリー記録形式）を check-tonmana に移植
- daily-xonepoint 側の STEP 4-2/4-3 を `/check-tonmana` 呼び出しに置換し、返却された【最終原稿】【スコアサマリー】を受け取る形に簡略化
- `metadata.yaml` に `check-tonmana: 品質チェック` を追記
- `update_wiki_skills.py` を実行し Wiki（`docs/skills/check-tonmana.md`・index・daily-xonepoint）を再生成

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/check-tonmana/SKILL.md` | 新規作成。本文テキストを受け取りトンマナ調整＋P01化採点ループを実行し、最終原稿とスコアサマリーを返す |
| `.claude/skills/daily-xonepoint/SKILL.md` | STEP 4-2/4-3 のインライン記述を `/check-tonmana` 呼び出しに置換 |
| `.claude/skills/metadata.yaml` | `check-tonmana: 品質チェック` を追記 |
| `docs/skills/check-tonmana.md` | Wiki 詳細ページ（自動生成） |
| `docs/skills/index.md`, `docs/skills/daily-xonepoint.md` | Wiki 差分再生成 |

## 設計判断

- 切り出し方は「ロジックを check-tonmana に移植 → 呼び出し元はスキル呼び出しに置換」とした。daily-xonepoint に採点基準を残す案もあったが、二重管理になるため移植に統一した。
- 入力は「本文テキスト」とし、ファクトチェック後の確定テキストを渡す前提にした。これにより writer 系の単体フローからも独立して呼べる。

## 確認結果

- `check-tonmana` スキルが `/check-tonmana` で呼び出せること、metadata 反映により Wiki 詳細ページが生成されることを確認。
- daily-xonepoint の STEP 4-2 が `/check-tonmana` を参照する形に置き換わっていることを確認。
