---
title: visual_section-planner スキル新設
date: 2026-06-07
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

note 記事（執念の物語）の制作フローでは「各 H2 セクションに 1 つ画像を配置する」工程があるが、どのセクションにどんな画像を載せるかを案出しする専用スキルがなかった。執筆後の画像準備を再現性のある形で標準化するため、本文を入力に H2 ごとの画像案を出力するスキルを新設した。

## 実施内容

- `visual_section-planner` を新設。記事本文（テキスト or ファイルパス）を入力に、`## ` で H2 セクションを分割（導入部・参考情報は対象外）
- 各 H2 セクションに対し、画像案を **3 つ**（図解／イメージ／写真Web取得）出力。表ではなくセクション分け markdown 形式で、生成プロンプトは書かず**画像の説明のみ**
- 出力を入力と同じ `draft/` ディレクトリの `image-plan.md` に保存（テキスト直貼り時は表示のみ）
- `metadata.yaml` に登録（カテゴリ: 画像・同期）、note-story spec のフロー10 を本スキル呼び出しに更新

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/visual_section-planner/SKILL.md` | 新規。`templates/SKILL_temp.md` 準拠（目的／手順／出力形式／禁止事項） |
| `.claude/skills/metadata.yaml` | `visual_section-planner: 画像・同期` を追加 |
| `projects/note-story/spec.md` | フロー10 を画像プランニング（本スキル）に更新 |
| `docs/skills/visual_section-planner.md` `index.md` | Wiki 自動生成 |

## 設計判断

- 出力は「表」から「セクション分け markdown」に変更（ユーザー指定）。各セクション 3 案で選択の幅を持たせ、生成プロンプトは持たせず説明のみに絞って後段スキルへ委譲。

## 確認結果

- SCEtoAUX 原稿で実行し、4 セクション・各 3 案・プロンプトなしで `draft/image-plan.md` が生成されることを確認。
