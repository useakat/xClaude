---
title: W002 執念の物語 note 記事プロジェクト立ち上げ＋プロジェクト雛形
date: 2026-06-07
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

note の「困難を乗り越え成功した執念の物語」（what_id W002）を継続制作するためのワークスペースが未整備だった。x-onepoint プロジェクトと同様に、媒体・ターゲット・表現ルール・制作仕様をプロジェクト単位のドキュメント（plan/brand/spec）として固め、スキルから役割別に参照できる構成にする。あわせて、今後のプロジェクト立ち上げを高速化するための雛形も用意した。

## 実施内容

- `projects/note-story/` に W002 用の 3 ドキュメントを新設
  - `plan.md`: 目的・ターゲット（persona PE01/05/09/10、pain PR001）・CTA・Risks
  - `brand.md`: note 執念の物語固有の表現ルール。`style/style-note-story.md` の文体・演出ルール（ズラシの型・専門語翻訳・物語ドライブ装置・論理の橋・出力前セルフチェック）を取り込み、参照ではなく自己完結化
  - `spec.md`: 制作フロー・命名規則（記事フォルダ `YYYY-MM-DD_<短いタイトル>/`、draft/output/images 構造）
- 新規プロジェクト立ち上げ用の雛形 `projects/template/`（CLAUDE/plan/brand/spec/spec_example）を追加
- スキル雛形の記入例 `templates/SKILL_example.md` を追加（`templates/SKILL_temp.md` の具体例）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/note-story/plan.md` `brand.md` `spec.md` | W002 の目的・表現ルール・制作仕様を新設。style-note-story の内容を brand.md へ取り込み |
| `projects/template/*` | プロジェクト雛形一式を追加 |
| `templates/SKILL_example.md` | SKILL 雛形の記入例を追加 |

## 設計判断

- `style/style-note-story.md` は将来削除予定のため、参照ではなく brand.md に内容を取り込んで note-story プロジェクトを単体で自己完結させた。
- 画像成果物の置き場は draft（作業中）→ output（確定）、参照素材は reference、過去版は archive に分離。

## 確認結果

- `projects/note-story/` に plan/brand/spec が揃い、CLAUDE.md の起動ルール（spec.md を Read）と整合することを確認。
- 後続の SCEtoAUX 記事制作で spec のフォルダ構造・命名規則どおりに運用できることを確認。
