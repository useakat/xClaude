---
title: reporter-daily 文体ルールの style ファイル外部化
date: 2026-05-07
tags: [skill, style, workflow]
---

← [変更ログへ](../changelog/)

## 背景・動機

reporter-daily SKILL.md の STEP 5 には、文体・1人称・NG表現・投稿フォーマット・一言の選び方など、報告文の文体ルールが直書きされていた。X ワンポイント解説には `style/style-xonepoint.md` が用意されているのに対し、日報・週報・月報には外部の文体ガイドが存在せず、ルールが SKILL.md 内に分散していた。

また 2026-05-06 の日報生成時、changelog 関連の特記事項を AI が生成したものをユーザーが 4 回修正した。その修正方向は以下の通りで、いずれも「具体性・明示性・能動性」を志向する一貫したパターンだった：

1. 「投稿文の事実確認に」→「claude code での投稿文の事実確認ステップに、」（場所・対象を具体化）
2. 「点数判定」→「文章の正確性判定」（簡潔語を説明的に展開）
3. 「文体・口調の」→「文体の」（重複概念の整理）
4. 「追いかける形」→「追求する形」（意志的な動詞）
5. 冒頭「〜が一段落整った日」を削除（要約・総評フレーズの排除）

これらをルール化して再現できるようにするため、文体ガイドを外部ファイル化したうえで今回の学びを盛り込んだ。

## 実施内容

- `style/style-reporter.md` を新規作成。想定読者・目的・人格・温度感・文の長さ・1人称・用語統一・NG表現・投稿の特記事項フォーマット・一言の選び方・changelog 関連の特記事項の書き方を1ファイルにまとめた
- 想定読者を「よーん本人、マネタイズコンサルタント、claude agent」と明記し、目的を「月報・週報作成の基盤となる重要な書類」と位置づけ
- NG表現に「総評フレーズ」「抽象的な圧縮表現」「重複概念の併記」「受動的・曖昧な動詞」「場所・主語・対象の省略」を追加
- changelog 関連の一言の書き方として悪い例・良い例を併記
- `.claude/skills/reporter-daily/SKILL.md` STEP 5 の直書き文体ルールを削除し、冒頭で `style/style-reporter.md` を Read してそのルールに従うよう変更
- データ条件分岐ルール（5,000 インプ以上の扱い・report_details の参照・フォロワー言及禁止・投稿なし日の書き方）はスキル固有のため SKILL.md 側に残した

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `style/style-reporter.md` | 新規作成。日報・週報・月報の共通文体ガイドを集約 |
| `.claude/skills/reporter-daily/SKILL.md` | STEP 5 の直書きルールを削除し style-reporter.md を参照する形に簡素化 |

## 設計判断

ファイル名は `style-reporter.md`（singular）。reporter-weekly / reporter-monthly でも将来的に同じファイルを参照できる命名にした。今回は reporter-daily のみ参照を変更し、weekly / monthly の差し替えは別タスクとした（影響範囲を最小化するため）。

## 確認結果

`style/style-reporter.md` の作成と `.claude/skills/reporter-daily/SKILL.md` STEP 5 の簡素化を確認し、master に push 済み。次回 `/reporter-daily` 実行時にスタイルガイドが参照されることを確認予定。

## 今後の課題

- reporter-weekly / reporter-monthly の SKILL.md も同じ style ファイルを参照するよう統一する
- 数日運用してみて、特記事項の生成品質が安定しているか確認する
