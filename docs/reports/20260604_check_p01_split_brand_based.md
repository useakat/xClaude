---
title: check-tonmana 縮小・check-p01 分離（brand.md 基準化）
date: 2026-06-04
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260604_check_p01_split_brand_based/)

## 背景・動機

同日に新設した `check-tonmana` は「トンマナ調整＋P01化スコアリング」を1スキルで担い、参照は `style/style-xonepoint.md` だった。これを次の2点で見直した。

1. **責務分離**: トンマナ調整（文体・口調を整える）と P01化スコアリング（6項目採点ループ）は性質の異なる処理であり、別スキルに分けた方が再利用・保守がしやすい。
2. **スタイルガイドの一本化**: x-onepoint プロジェクトの発信ルールは `projects/x-onepoint/brand.md` に集約されつつある。トンマナ・採点とも、作業フォルダの brand.md を単一の参照元にしたい。

ただし採点・書き直しに必要な詳細材料（冒頭フック5軸の判定語彙・各種 OK/NG 例・削る対象優先度リスト）は style-xonepoint.md にしか無く、brand.md には要約しか存在しなかった。そのまま brand.md へ切り替えると check-p01 の採点・書き直し精度が落ちるため、brand.md 側に詳細を展開して「非劣化」を担保する必要があった。

## 実施内容

- `check-tonmana` をトンマナ調整専用に縮小。参照を作業フォルダの `./brand.md` に変更し、出力を【調整後本文】＋トンマナサマリーに簡素化。
- `check-p01`（新規）に P01化チェックリスト6項目の10段階採点ループ（最大5回・警告フラグ）を移植。参照を `./brand.md` に統一。
- `projects/x-onepoint/brand.md` の Writing Rules を拡充し、check-p01 が brand.md 単体で完結できるようにした：
  - 冒頭フック5軸の各軸判定語彙（体接続動詞・読者代名詞・具体数字・直感的比較数字・パワーワード）＋ OK/NG 例
  - 専門用語言い換え・視点段落分け・数値具体（Before/After）・感覚語の具体例
  - 「削る対象優先度リスト（字数超過時）」5項目を新規追加
- `daily-xonepoint` の STEP 4 を 4-2（/check-tonmana）→ 4-3（/check-p01）の2段呼び出しに変更。
- `metadata.yaml` に `check-p01: 品質チェック` を追加。
- `style/style-xonepoint.md` は無変更（writer-xonepoint / writer-xqa が現役で参照するため非破壊で維持）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/check-tonmana/SKILL.md` | トンマナ調整専用に縮小、参照を作業フォルダ brand.md に変更 |
| `.claude/skills/check-p01/SKILL.md` | 新規。P01化6項目採点ループ。字数削減は brand.md の削る対象優先度リスト参照 |
| `.claude/skills/daily-xonepoint/SKILL.md` | STEP 4 を 4-2/4-3 の2段呼び出しに変更 |
| `.claude/skills/metadata.yaml` | `check-p01: 品質チェック` を追加 |
| `projects/x-onepoint/brand.md` | Writing Rules を拡充（5軸語彙・各種例・削る対象優先度リスト） |
| `docs/skills/*` | Wiki 自動再生成 |

## 設計判断

- 「移植」の方式は、style-xonepoint.md から削除せず **brand.md に詳細を展開**する形にした。style-xonepoint.md は writer 系スキルが参照しているため、削除すると writer 系が壊れる。結果として削る対象優先度リスト等は両ファイルに併存する（brand.md = 自己完結ハブ / style-xonepoint.md = writer 系詳細という役割分担）。drift を避けたい場合は将来 writer 系も brand.md 参照へ寄せる別タスクが必要（今回スコープ外）。

## 確認結果

- check-p01 の6項目すべてについて、採点・書き直しに必要な材料が `projects/x-onepoint/brand.md` 内に存在することを項目別に突き合わせて確認（全項目 style-xonepoint.md と同等）。
- check-p01 SKILL.md の参照見出し名（「削る対象優先度リスト」「Writing Rules」）が brand.md の実見出しと一致することを確認。
- `style/style-xonepoint.md` が無変更であること（writer 系非破壊）を確認。
- `/check-tonmana`・`/check-p01` がスキルとして呼び出せること、Wiki 詳細ページが生成されることを確認。

## 今後の課題

- brand.md と style-xonepoint.md の併存内容の drift 防止（writer 系の brand.md 参照寄せ）。
