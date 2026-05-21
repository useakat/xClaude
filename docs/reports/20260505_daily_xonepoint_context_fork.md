---
title: daily-xonepoint の子スキル隔離（context:fork 対応）
date: 2026-05-05
tags: [skill, bugfix]
---

← [変更ログへ](../changelog/)

## 背景・動機

`/daily-xonepoint` が STEP 3 で `/check-fact` を呼び出すと、check-fact の完了マーカー（「チェック完了」）が親の会話ターンに漏れ込み、親スキルがそこで処理を止めてしまう構造バグがあった。また STEP 2 の原稿作成ロジックが `writer-xonepoint` と重複しており、スタイルガイドの変更などを両スキルで二重メンテする必要があった。

Claude Code のスキルフロントマターに `context: fork` を設定すると、そのスキルは親の会話コンテキストを引き継いだフォークされた Subagent として隔離実行される機能があることを確認し、これを用いて解決した。

## 実施内容

- `writer-xonepoint/SKILL.md` に `context: fork` フロントマターを追加
- `check-fact/SKILL.md` に `context: fork` フロントマターを追加
- `daily-xonepoint/SKILL.md` の STEP 2（約60行のインライン実装）を `/writer-xonepoint` への委譲6行に置き換え
- `writer-xonepoint` でネタ更新後に【タイトル案】【本文】を再掲して最終出力にすることで、親への Result 返却を修正
- `check-fact` で「チェック完了」宣言後に最終修正案を再掲して最終出力にすることで、親への Result 返却を修正

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/daily-xonepoint/SKILL.md` | STEP 2 をインライン実装から `/writer-xonepoint` 委譲に変更 |
| `.claude/skills/writer-xonepoint/SKILL.md` | `context: fork` フロントマター追加・出力順を「ネタ更新 → 最終出力」に変更 |
| `.claude/skills/check-fact/SKILL.md` | `context: fork` フロントマター追加・「チェック完了」後に最終修正案を再掲 |

## 設計判断

当初は `.claude/agents/` に別ファイルを定義して `Agent` ツールで呼び出すアプローチを検討していたが、`context: fork` フロントマターで同じ隔離効果が得られることがわかり、既存の `Skill` 呼び出し構造を変えずに済む後者を採用した。

`context: fork` では子スキルの**最後の出力**が親への `Result` として返る仕様のため、各スキルの最終出力が必要なコンテンツになるよう処理順を調整した。

## 確認結果

routine agent の実行ログで `Skill "writer-xonepoint" completed (forked execution).` が確認でき、子スキルが隔離実行されていることを確認。

## 今後の課題

Result の返却内容（最後の出力のみ vs. 全出力）の仕様を今後も観察する。`check-fact` の Result 返却が正しく機能しているかは次回 `/daily-xonepoint` 実行時に確認が必要。
