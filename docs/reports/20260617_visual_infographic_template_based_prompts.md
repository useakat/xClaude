---
title: visual_infographic のタイトル＆プロンプトをテンプレート基準に変更
date: 2026-06-17
tags: [skill]
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260617_visual_infographic_template_based_prompts/)

## 背景・動機

金の起源の図解を実制作する中で、「タイトル＝原稿（index.md）の冒頭文」「プロンプト＝`infographic_template/` の型テンプレートを実際に Read して厳密に埋める」方式が良い結果になった。従来の SKILL.md は (1) タイトルを「『実は、』で始まれば冒頭文／それ以外は15字以内を生成」と分岐し、(2) プロンプトをテンプレートファイルを参照せずその場で自走生成していたため、この運用と乖離していた。スキルと spec をこの運用に合わせる。

## 実施内容

- **Step 2（タイトル）**: 分岐を廃止し、**入力テキストの冒頭1文（先頭〜最初の句点、句点は除く）を常にメインタイトル**にするルールへ変更。
- **Step 3（プロンプト生成）**: 「型テンプレート基準」へ全面書き換え。
  - テンプレートは `projects/w003/infographic_template/` 固定（6型: step_flow / compare_contrast / radial / timeline / pyramid / checklist）。
  - 入力内容に合う `count` 個を自動選択（不適な型は除外、例: 階層が無ければ pyramid を外す）。
  - 各テンプレートを Read し、**共通指示・スーパーニャンコ指定・テキスト厳守ルールはそのまま、プレースホルダだけ差し替える**手順を明記。
  - テンプレートディレクトリ不在時のみ従来の自走生成にフォールバック（警告付き）。
- **Step 5**: `make-infographic` は既に `--infographic-title "[メインタイトル]"` を渡しており、これが冒頭1文に解決されるため変更不要。
- **spec.md**: 制作フロー step 7 に「タイトル＝output/index.md 冒頭1文」「プロンプトは infographic_template の型を基に作成（内容に合う5型）」を明記。Naming に型テンプレ置き場（6型）を追記。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/visual_infographic/SKILL.md` | Step 2 タイトルを冒頭1文固定に、Step 3 をテンプレート基準（Read→プレースホルダ差し替え、count個自動選択、不在時フォールバック）に書き換え |
| `projects/w003/spec.md` | step 7 にタイトル・テンプレート運用を明記、Naming に infographic_template を追記 |

## 確認結果

- `output/index.md`（冒頭文「金って、実は超新星爆発でもほとんど作れない元素だった」）を入力に、テンプレートを Read して各型のプレースホルダのみ差し替えたプロンプトで5枚生成し、タイトルが冒頭文になることを実地確認（本セッション）。
- 文書（SKILL.md / spec.md）のみの変更でスクリプト変更なし。

## 今後の課題

- テンプレート置き場が W003 固定パスのため、他プロジェクト（W001/W002）で使う場合は `--template-dir` 等の汎用化が必要。
