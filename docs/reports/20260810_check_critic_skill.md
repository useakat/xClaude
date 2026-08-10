---
title: 知識ある読者チェック（check-critic）を新設し全投稿系プロジェクトに配線＋NotebookLM 呼び出しをブリッジへ切替
date: 2026-08-10
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md#2026-08-10) ｜ [セッション履歴→](../../history/20260810_check_critic_skill/)

## 背景・動機

金星ベネラ販促（20260806）の制作で、`/check-fact`（GPT・97点）を通過した初稿に対し、**ユーザーの質問だけで事実誤り3件と論理矛盾1件が発覚**した（「地表到達の初」の誤帰属／当時未確定の90気圧の断定／「未達＝失敗」の誤解／前提の自己否定）。

初稿と最終版を比較分析した結果、品質差の原因は文章力ではなく**検証の順序と種類**にあった：

1. **裏取りの土台（notebook）を初稿の後に作っていた** — 旧記事は w002 フォルダ・notebook が無く、`/check-fact`（GPT）フォールバックが弱点だった
2. **「本文に書かれていない前提への疑問」を検出する工程が無かった** — ユーザーの「5号と6号は同時？」「3号も途中で潰れたのでは？」型の質問は、本文の主張だけを照合するファクトチェック（7/20導入の項目別検証を含む）では原理的に検出できない

これを仕組み化するため、知識ある読者役の敵対的レビュー `/check-critic` を新設し、全投稿系プロジェクト（W001/W002/W003/Z01）に配線した。

## 実施内容

- **`/check-critic` スキル新設**：別コンテキストの「知識ある読者（分野に明るい科学好き・粗を根拠つきで指摘する層）」サブエージェントに**原稿だけ**を渡し（制作文脈は渡さない）、A事実への反論／B単純化しすぎ／C**本文が触れていない前提への疑問**／D論理の穴、を最大10件列挙させる。**改稿はせず**、指摘リスト＋検証方法を返し、裏取り工程（check-fact-lim / 一次情報）に流す。指摘自体が誤ることもあるため「裏取りなしで反映しない」を明記。
- **既存チェックとの役割分担を確立**：check-reader（素朴読者・理解のつまずき・改稿で閉じる）／check-fact系（本文の主張の照合）／check-critic（本文外の論点・裏取りが必要）。
- **4 spec への配線**（順序＝ファクト照合→素朴読者→知識読者→裏取り反映→ユーザー提示）：
  - W001: check-reader（6.3）・check-critic（6.6）追加
  - W002: check-critic（9.5）追加（check-reader --plan は構成段階に既存）
  - W003: ファクトチェックを `/check-fact`→`/check-fact-lim`（research_trivia-source の notebook 利用）に切替＋check-reader（5.3）・check-critic（5.6）追加
  - Z01: check-critic（STEP 4.5）追加（裏取りは一次情報）
- **W001 モードB の notebook フォールバック廃止**：w002 に notebook が無い古い記事は「**w002 フォルダを遡及作成＋`/research_setup-sources` で notebook 新規作成し、w002 側に保存**」を初稿の**前**に実施（一次ソースを初稿の土台にする）。金星の notebook（62ソース）を `projects/w002/2026-04-16_venera7/` に移設し初適用。他の旧記事はオンデマンド遡及。
- **NotebookLM 呼び出しをブリッジへ切替**：check-fact-lim（ask）・research_setup-sources（create/deep-research）・research_trivia-source（create/deep-research/ask）の呼び出し先を、cookie 認証が失効した `notebooklm_manager.py` から `notebooklm_browser_bridge.py` に変更（SKILL.md のみ・.py 無変更）。
- **ブリッジ `ask` の不具合調査**：報告されていた `TypeError` は再現せず（短文・長文 stdin とも正常動作）。deep-research 実行中の並行アクセスによる一時的な状態と判断し、「**ブリッジは並行実行しない**」を check-fact-lim に運用注意として明記。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/check-critic/SKILL.md` | 新規（知識ある読者チェック） |
| `.claude/skills/metadata.yaml` | check-critic を品質チェックに登録 |
| `projects/w001/spec.md` | 6.3/6.6 追加・モードB notebook 運用書き換え・Verification 追加 |
| `projects/w002/spec.md` | 9.5 追加・Verification 追加 |
| `projects/w003/spec.md` | check-fact-lim 切替・5.3/5.6 追加・Verification 追加 |
| `projects/z01/spec.md` | STEP 4.5 追加 |
| `.claude/skills/check-fact-lim/SKILL.md` | ブリッジ ask へ切替（stdin 渡し）・並行実行禁止を明記 |
| `.claude/skills/research_setup-sources/SKILL.md`・`research_trivia-source/SKILL.md` | create/deep-research/ask をブリッジへ切替 |
| `projects/w002/2026-04-16_venera7/` | 金星記事の遡及フォルダ（notebook-id.md・README） |

## 設計判断

- **check-reader への統合ではなく独立スキル**：素朴読者の指摘は「改稿で閉じる」、知識読者の指摘は「裏取りしないと真偽が決まらない」と後処理が異なるため分離した。
- **改稿させない設計**：由来ケースでも GPT の指摘の一部は一次情報で棄却された。指摘→裏取り→反映の分離が誤反映を防ぐ。
- **W003 も notebook 照合へ**：research_trivia-source が既に notebook を作成・保存していたため、切替コストはほぼゼロだった。

## 確認結果

- ブリッジ `ask` で金星 notebook（62ソース）に長文照会し、ベネラ本文の全事実（5・6号の犠牲的設計／12m²パラシュート／耐圧25気圧／90気圧確定は1967年末の統合解析／モルニヤM 1,130kg 制限）の追認を確認
- 4 spec すべてに check-critic の配線（grep で 2〜3 箇所ずつ）と Verification 追記を確認
- wiki 再生成（49スキル・check-critic ページ生成）

## 今後の課題

- infographic 系スキル（make-infographic / visual_infographic / notebooklm）は旧 manager 参照のまま（画像生成は lovart 移行済みのため優先度低）
- 旧記事の w002 遡及作成は販促のオンデマンドで実施（海王星・カッシーニ等は次回販促時）
- check-critic の実運用初回（次の投稿制作）で指摘の質・裏取りループの回り方を確認する
