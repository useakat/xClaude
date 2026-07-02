---
title: セクション画像ワークフローを design-brief フェーズ＋テンプレ合成方式に刷新
date: 2026-07-02
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260702_section_image_designbrief_workflow/)

## 背景・動機

note 記事の各 H2 セクションに置く図解・イメージ画像は、これまで `visual_section-planner`（案出し）→ `visual_section-imager`（実画像化）で用意していたが、次の課題があった。

- imager が画像説明から直接プロンプトを作り、いきなり生成に進むため、**構図・トーンの方針をユーザーが確認する余地がなかった**。とくに実機の搭載位置・外見のように「正確には描けない／描くと捏造になる」対象を、事前にすり合わせる仕組みがなかった。
- 図解プロンプトのテンプレートが「汎用テンプレ or 用途別テンプレを丸ごと採用」の二択で、テンプレ全体と構成パターンを別々に組み合わせられなかった。
- セクション画像の目的・トーンを定義する専用の `plan.md`／`brand.md` が無く、サムネ用の定義を流用していた。

そこで、**design-brief（デザイン指示書）を挟んで承認を2段階にし**、図解プロンプトを「全体テンプレ＋レイアウト部品」の合成方式に変え、セクション画像専用のブランド定義を整備した。

## 実施内容

- **planner**: 案出し前に `image/plan.md`・`image/brand.md` を読み、その方針に沿って各 H2 に3案を出すよう変更。画像説明欄の記載（イメージ＝目的、写真＝検索語句）を明確化。
- **選択フローの明示（spec.md ステップ11）**: 案出し（`image-plan.md`・複数案）→ ユーザーが各セクション1案を選択 → 確定案を `image-plan_final.md` に保存 → imager へ、という流れを spec に明文化。
- **imager を3フェーズ化**:
  - フェーズ1: 写真以外の各セクションについて `image/design-brief_template.md`（テンプレ）・`design-brief_example.md`（例）をもとに `draft/images/<safe>_design-brief.md` を作成し、**保存先パスのみ提示して承認を待つ**（本文はチャットに貼らない）。
  - フェーズ2: 承認済み design-brief をもとにプロンプトを作成し、再度パス提示で承認を待つ。
  - フェーズ3: 図解は NotebookLM で各3枚生成、イメージは外部の画像生成AI（nano banana 等）でユーザーが生成、写真はスキップ。
- **図解プロンプトのテンプレ合成方式**: `infographic_template.md` を常に全体ベースにし、「# 図解の構成・レイアウト」だけを `infographic_layout_*`（compare-contrast / timeline / step-flow / radial / pyramid / checklist）から内容に応じて選んで差し込む。合うものが無ければ同セクションを自由記述。
- **セクション画像用ブランド整備**: `projects/w002/image/brand.md`・`plan.md` を新設（本文理解の補助・落ち着いたトーン・図解=ラベル可／イメージ=文字なし・キャラ/白人間禁止 など）。`image_template/` を `image/` へ移行。
- **W002 で実運用して検証**（ボイジャー再点火の全5セクション）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/visual_section-planner/SKILL.md` | 案出し前に `image/plan.md`・`image/brand.md` を読むステップを追加。画像説明欄の記載を明確化 |
| `.claude/skills/visual_section-imager/SKILL.md` | 入力を `image-plan_final.md` に変更。design-brief フェーズ追加で3フェーズ化。図解プロンプトを template＋layout 合成方式に。承認は保存先パスのみ提示 |
| `projects/w002/spec.md` | ステップ11 を案出し→選択→確定→design-brief 承認→プロンプト承認→生成に更新。画像プラン命名（image-plan / image-plan_final）追記 |
| `projects/w002/image/brand.md`・`plan.md` | セクション画像用のトーン・目的を新規定義 |
| `projects/w002/image/design-brief_{template,example}.md` | `image_template/` から移行 |
| `projects/visual_prompts/infographic_template.md`・`infographic_layout_*.md` | 全体テンプレ＋レイアウト部品の構成に整理。タイトルの「帯で強調」固定文を削除 |

## 設計判断

- **design-brief を挟む理由**: プロンプトはテンプレの体裁が混じり差分が読みにくい。design-brief は「媒体・目的・文字階層・構図・配色・禁止・レビュー基準」の粒度でレビューでき、実機位置のように描けない対象を「位置は主張しない／簡略アイコン」と事前に確定できる。
- **テンプレ合成（全体＋部品）を選んだ理由**: 図解ごとに全体の作法（テキスト厳守・白人間禁止・Negative prompt）は共通で、変わるのは構成パターンだけ。全体テンプレを固定し構成だけ差し替える方が一貫性と保守性が高い。
- **本文をチャットに貼らずパスのみ提示**: 長文プロンプト/指示書でチャットを埋めず、ファイルで確認・修正するワークフローに統一。

## 確認結果

- W002「ボイジャー再点火」で全5セクションを通し検証。planner で3案 → ユーザー選択 → `image-plan_final.md` → design-brief 5件を作成・承認 → プロンプト5件を作成・承認 → 図解4件を NotebookLM で各3枚生成（12枚成功）、イメージ1件は外部生成。`output/images/` に確定5枚を配置。
- design-brief フェーズで「スラスタの実機位置・外見は描けない」旨をユーザーと確認し、②を役割対比型（位置を主張しない・簡略アイコン）へ、③を関所メタファー（命令の“形”で通る/弾かれる）へ修正できた。
- スキルをセッション途中で編集しても Skill 呼び出しには当該セッションのキャッシュ（編集前）が渡ることを確認。実ファイル（on-disk）が正であり、反映は次セッション以降。

## 今後の課題

- planner のフォールバック先が `projects/w002/image/` にハードコードされている（他ワークスペースでは要調整）。
- 図解の「実機そっくりに描かない」制約は Negative prompt と指示文で抑止しているが、生成AIが写実的な機体を描く場合があり、レビューでの目視確認が必要。
