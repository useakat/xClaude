---
title: X長文→note 導線の分割設計フロー（plan-xnote-funnel）を追加
date: 2026-07-03
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260703_plan_xnote_funnel_split_design/)

## 背景・動機

W001（X長文・約600字＋note誘導セルフリプ）と W002（有料note・6000〜8000字）は、これまで
**後追いで一方向に深掘りする**構造だった：W002 modeB＝既存 W001 X投稿を note 化／W001 modeB＝既存 note から X 長文化。

このため「X長文でどこまで書き、何を有料 note の“売り”に温存するか（＝セルフリプ文面に直結）」を
**先に一体で設計できない**という課題があった。よーんは、ネタ選定の直後に **X長文の範囲・note の売り・セルフリプ文面まで
一括で決めてから** X長文と note を書きたい（X長文でバズ→セルフリプで note へ誘導、という導線前提）。

既存資産：W001 は本編が X 内で完結し note 誘導はセルフリプ（2投稿目）に分離する設計、
クロス週モデル（note 先出し→翌週 W001 で誘導）がすでにある。本変更はこの上に「分割設計」を前段として足す。

## 実施内容

- **新スキル `plan-xnote-funnel`** を新設（上流・対話）。ネタ選定 → 共有 notebook 準備（`/research_setup-sources`）→
  物語アーク把握 → **分割設計【対話・承認】**（X長文の範囲／note の売り・課金壁／セルフリプ文面）→
  共有ブリーフ `funnel-brief.md` 保存、まで。本文は書かず W001/W002 に委譲。**X をクリフハンガーにしない**制約を明記。
- **W002 spec にモードC（協調／ブリーフ起点）** を追加。導入 C1〜C7 で、B5 の「独立5構成案」を
  **ブリーフの「note の売り／課金壁」から導く**方式に置換。note は独立完結記事のため **X の既出範囲を無料部分で再掲してよい**
  （温存すべきは有料部分の売り）。ネタ使用済み更新はモードC で実施（note 先行のため二重選定を防ぐ）。
- **W001 spec にモードC** を追加。題材＝ブリーフの `## X長文の範囲`、notebook＝ブリーフの `notebook_id` 継承、
  **セルフリプ＝ブリーフの確定文面**（note 公開後に実 URL 差替）、来歴を `funnel-brief-ref.md` に記録。
- **metadata.yaml** に `plan-xnote-funnel: category: コンテンツ制作` を登録し、Wiki（`docs/skills/`）を再生成。
- 既存 modeA / modeB は両 spec とも併存。制作順序は **note 先行・公開 → W001 X長文投稿**。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/plan-xnote-funnel/SKILL.md` | 新規。分割設計スキル本体（ネタ選定→notebook→アーク→分割設計→funnel-brief.md） |
| `projects/w002/spec.md` | モードC（C1-C7）追加。B5 をブリーフ起点に。Naming に funnel-brief.md／ネタ更新／Verification 整備 |
| `projects/w001/spec.md` | モードC 追加。題材=ブリーフのX範囲・セルフリプ=ブリーフ確定文面・funnel-brief-ref.md 記録／Verification |
| `.claude/skills/metadata.yaml` | `plan-xnote-funnel` を登録 |
| `docs/skills/*` | Wiki 再生成（plan-xnote-funnel 詳細ページ・index 追加ほか追随） |

## 設計判断

- **分割設計を上流の独立スキルにした理由**：X長文とnoteの「分割点」と「セルフリプ文面」は相互依存し、
  ネタ確定直後に一度で決めるのが自然。W001/W002 の本文フローに埋め込むより、共有ブリーフを1枚作って両者が読む方が疎結合で保守しやすい。
- **note を独立完結記事とした理由**（当初案から修正）：note は X と別に読まれる「決定版」であり、
  X の既出範囲を再掲しても問題ない。分割の主眼は「有料部分に何を温存するか」。重複回避を制約にしない。
- **ブリーフの置き場所を W002 側にした理由**：制作順序が note 先行のため。W001 は `funnel-brief-ref.md` でパス参照する。

## 確認結果

- 新スキルが `/plan-xnote-funnel` として登録され、Wiki 詳細ページ（`docs/skills/plan-xnote-funnel.md`）が生成されることを確認。
- W002 spec のモードC 参照 8 箇所、W001 spec のモードC 参照 12 箇所を grep で確認。既存 modeA/modeB の記述は温存。
- 実データでの通し検証（ブリーフ生成→W002 modeC→W001 modeC）は未実施。次に本番ネタで走らせて、
  ①ブリーフ全セクションが埋まり承認ゲートで止まる ②note 有料部に売りが温存 ③X が本編完結・セルフリプがブリーフ文面、を確認する。

## 今後の課題

- 未検証の実運用（ブリーフ→note→X の一気通貫）を1本走らせて挙動を確認する。
- `funnel-brief.md` の配置・参照記録の運用（`funnel-brief-ref.md`）が sync-x-note-analytics の集計と齟齬しないか観察。
- 当面は対話・承認ゲートありの半自動。全自動オーケストレータ化は必要が出たら検討。
