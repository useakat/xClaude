---
title: check-fact-lim スキル新設（NotebookLM ソース限定ファクトチェック）
date: 2026-06-04
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260604_check_fact_lim_skill/)

## 背景・動機

既存の `check-fact` スキルは、ファクトチェックと完全性チェックを OpenAI GPT（`gpt-5.4-mini`）に投げている。GPT は学習済み知識＋ウェブを根拠にするため、**判定の根拠ソースを限定できない**。特定の信頼できる資料群（論文・一次資料）だけを根拠に検証したいケースでは、根拠の出所を制御できないことが課題だった。

そこで、根拠を **指定した NotebookLM ノートブックのソースだけ** に限定してファクトチェックさせる派生スキル `check-fact-lim`（lim = limited source）を新設した。`notebooklm_manager.py ask <notebook_id>` は、その notebook に登録されたソースのみを参照して回答するため、notebook_id を渡すだけで「根拠ソースの限定」が実現できる。

ファクトチェックの流れ・構造（STEP1 完全性チェック → STEP2 ファクトチェック最大5ループ → サマリー出力、テキスト/Drive 入力の自動分岐）は一切変えず、**GPT 呼び出し2箇所だけを NotebookLM の `ask` に差し替える**方針とした。

## 実施内容

- `check-fact` の SKILL.md をベースに `check-fact-lim/SKILL.md` を新設
- 入力仕様を変更：`$ARGUMENTS` の **先頭トークンを notebook_id**（必須）、残りを従来どおりチェック対象（テキスト / Drive ファイル ID / ローカルパスを自動判定）として解釈
- STEP1 完全性チェックの GPT 呼び出し（`completeness_check.py`）を NotebookLM `ask` に差し替え。指示文＋対象テキストを `/tmp/check_fact_lim_prompt.txt` に書き出し `"$(cat ...)"` で渡す（長文・改行のクォート崩れ防止）
- STEP2 ファクトチェック（最大5ループ）の GPT 呼び出し（`chatgpt_factcheck.py`）も同様に NotebookLM `ask` に差し替え
- プロンプト趣旨を「背景知識＋ウェブ活用」→「**このノートブックのソースのみを根拠**・根拠がない論点は要確認」へ変更。出力契約（`## スコア: XX/100` / `## 追加文案` / `## 修正文案`）は GPT 版と同一に保ち、スコア抽出・ループ制御は従来どおり Claude 側で実施
- `metadata.yaml` に `check-fact-lim: category: 品質チェック` を追記
- 新規スクリプトの作成・既存スクリプトの改変は行わず、既存 `notebooklm_manager.py ask` を流用

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/check-fact-lim/SKILL.md` | 新規。GPT 呼び出し2箇所を NotebookLM `ask` に差し替え、notebook_id を先頭引数で受け取る入力仕様に変更 |
| `.claude/skills/metadata.yaml` | `check-fact-lim`（品質チェック）を追記 |
| `docs/skills/check-fact-lim.md` ほか | `update_wiki_skills.py` による Wiki 詳細ページ自動生成（既存スキルの未反映差分も再生成） |

## 設計判断

- **根拠限定の実現方法**：vendor ライブラリの `chat.ask` は `source_ids` での個別ソース指定もできるが、「特定ノートブックのソースだけ」という要件は notebook 単位で十分なため、既存 `ask` コマンド（notebook_id 指定）をそのまま流用し、新規スクリプトを作らない方針とした。
- **notebook_id の渡し方**：スキルに固定 ID を埋め込まず、実行時に引数で渡す方式を採用（複数ノートブックを使い分け可能にするため）。
- **置き換え範囲**：STEP1・STEP2 両方を NotebookLM に置き換え、GPT 依存を完全に外した。

## 確認結果

notebook `bd47dcce-7172-483b-8c72-58a817a931ca`（金の起源_超新星と中性子星合体）で動作検証。意図的に事実誤り（「金は太陽の核融合で大量生成される」）を仕込んだ文章を入力：

| 回 | チェック種別 | スコア | 指摘内容 | 対応 |
|----|---------|--------|---------|------|
| - | 完全性 | 40/100 | 恒星核融合は鉄まで／rプロセス欠落／地球の金の由来（隕石）／生成現場の補足 | 追加あり |
| 第1回 | ファクト | 100/100 | （追加文案で誤り解消済み） | 問題なし → 終了 |

- ✅ notebook_id を引数で受け取り、その notebook のソースのみを参照（回答にソース引用 [1]〜[11] 付き）
- ✅ STEP1 が誤りを検出しスコア算出＋`## 追加文案`生成、Claude 側でスコア抽出
- ✅ スコア<95 で追加文案を STEP2 へ送り込み、STEP2 がスコア≥95 で即座にループ終了
- ✅ 出力契約が GPT 版と同一フォーマットで返ることを確認

## 今後の課題

- 個別ソース単位での限定（`source_ids` 指定）は未対応。notebook 内の一部ソースだけを根拠にしたい要望が出た場合に検討。
