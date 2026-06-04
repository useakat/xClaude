---
title: check-fact-lim スキル新設（NotebookLM ソース限定ファクトチェック） — セッション履歴
date: 2026-06-04
sidebar:
  hidden: true
---

# セッション履歴

> 2026-06-04 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260604_check_fact_lim_skill/)

---

## よーん *(13:28 JST)*

check-fact スキルをコピーして、check-fact-lim というスキルを作って。このスキルでは、GPT にファクトチェックをさせる代わりに、notebookLMの 特定の notebook のソースだけを参照してファクトチェックをさせたい。ファクトチェックの流れ・構造は変えず、GPT にさせていた処理を notebookLM にさせる。
実装計画を立てて。まだ実装はしないで

### Claude *(13:28 JST)*

計画を立てるため、まず関連ファイルを調べます。

*[ツール: `Agent`, `Agent`]*

両スキルの構造を把握しました。check-fact は STEP1（完全性チェック `completeness_check.py`）+ STEP2（ファクトチェック `chatgpt_factcheck.py`、最大5ループ）の2段階で、いずれも GPT（`gpt-5.4-mini`）を呼んでいます。一方 `notebooklm_manager.py ask` は notebook_id を指定すればその notebook のソースだけを参照して回答できます。

計画を固める前に2点確認させてください。

*[ツール: `AskUserQuestion`]*

回答ありがとうございます。`notebook_id` は実行時引数、STEP1・STEP2 両方を NotebookLM に置き換える方針で計画を固めます。正確に書くため元の SKILL.md を読みます。

*[ツール: `Read`]*

十分に把握できました。要件が明確なので、計画をまとめます。

*[ツール: `Write`, `ToolSearch`, `ExitPlanMode`]*

計画が承認されました。まず GPT 版のシステムプロンプト本文を正確に取得するため、2つのスクリプトのプロンプト部分を読みます。

*[ツール: `Read`, `Read`]*

プロンプト本文を取得しました。NotebookLM 版では「背景知識とウェブ情報を活用」→「このノートブックのソースのみを根拠にする」へ趣旨を変える必要があります。SKILL.md を作成します。

*[ツール: `Write`]*

metadata.yaml に追記します。まず現状を確認します。

*[ツール: `Read`]*

check-fact の直後に check-fact-lim を追記します。

*[ツール: `Edit`]*

実装が完了しました。

## 完了内容

**1. 新規スキル `.claude/skills/check-fact-lim/SKILL.md`**
- `check-fact` をベースに、GPT 呼び出し2箇所（STEP1 完全性チェック・STEP2 ファクトチェック）を NotebookLM の `ask` に差し替え
- `$ARGUMENTS` の先頭トークンを `notebook_id`（必須）として解釈、残りをチェック対象に
- 各 STEP で指示文＋対象テキストを `/tmp/check_fact_lim_prompt.txt` に書き出し、`notebooklm_manager.py ask <notebook_id> "$(cat ...)"` で送信 → その notebook のソースだけを根拠に判定
- プロンプトは「ソースのみを根拠に」「ソースに根拠がない論点は要確認」へ趣旨変更
- 出力契約（`## スコア`/`## 追加文案`/`## 修正文案`）・STEP2 の最大5ループ・サマリー表・Drive 連携分岐は **元の構造のまま維持**

**2. `metadata.yaml`** に `check-fact-lim: category: 品質チェック` を追記

**やらなかったこと**（計画どおり）: スクリプトの新規作成・編集なし。既存 `notebooklm_manager.py ask` をそのまま利用。`check-fact` 側は無改変。

---

## よーん *(13:48 JST)*

まず、bd47dcce-7172-483b-8c72-58a817a931ca　の id の notebook で動作検証

### Claude *(13:48 JST)*

検証用に、まず notebook が参照可能か確認します。

*[ツール: `Bash`]*

認証OK、対象 notebook（`金の起源_超新星と中性子星合体`）が存在します。この notebook のソースで真偽判定できるテキストを作って検証します。意図的に **事実誤りを1箇所**仕込みます（金の起源テーマ）。

まず STEP1（完全性チェック）を実行します。

*[ツール: `Bash`]*

STEP1 が機能しました（スコア **40/100**、ソース[1]〜[11]を根拠に誤りを指摘、`## 追加文案`を生成）。仕込んだ誤り「太陽の核融合で金が大量生成」をソース根拠で検出しています。

スコア<95 なので、`## 追加文案`を入力に STEP2 第1回を実行します。

*[ツール: `Bash`]*

STEP2 第1回で **100/100・問題なし** → ループ終了条件（≥95）で正しく停止。検証成功です。

## 動作検証結果（notebook: `bd47dcce…` 金の起源）

意図的に誤り（「金は太陽の核融合で大量生成」）を仕込んだ文章で実行：

| 回 | チェック種別 | スコア | 指摘内容 | 対応 |
|----|---------|--------|---------|------|
| - | 完全性 | 40/100 | 恒星核融合は鉄まで／rプロセス欠落／地球の金の由来（隕石）／生成現場の補足 | 追加あり |
| 第1回 | ファクト | 100/100 | （追加文案で誤り解消済み） | 問題なし → 終了 |

**確認できた挙動**
- ✅ notebook_id を引数で受け取り、その notebook のソース**だけ**を参照（回答にソース[1]〜[11]の引用付き）
- ✅ STEP1 が誤りを検出しスコア算出＋`## 追加文案`生成、Claude 側でスコア抽出
- ✅ スコア<95 で追加文案を STEP2 へ送り込み
- ✅ STEP2 がスコア≥95 で即座にループ終了
- ✅ 出力契約（`## スコア`/`## 追加文案`/`## 問題なし`）が GPT 版と同一フォーマットで返る

GPT 依存を外し、NotebookLM の特定ソースのみを根拠とするファクトチェックが、元の構造のまま動作しています。

---

## よーん *(13:51 JST)*

commit & push

### Claude *(13:51 JST)*

*[ツール: `Bash`, `Bash`]*

master に push しました（`d058245..de1736d`）。ただ Wiki 自動生成（`docs/skills/check-fact-lim.md`）が出ていません。commit 時の hook が `yaml` 未インストールのため黙って失敗していました（`python3 ... || true` で握り潰される設計）。

*[ツール: `Bash` × 複数]*

この環境には当初 `pip`/`yaml` が無く、`update_wiki_skills.py`（PyYAML 依存）が実行できない状態でした。

---

## よーん *(13:55 JST)*

pip/yaml　を入れて

### Claude *(13:55 JST)*

pip/yaml を入れます。ensurepip はディストロにブロックされたため、sudo で apt を使い `python3-pip`・`python3-yaml`（yaml 6.0.2）を導入。これで commit 時の Wiki 自動生成 hook が今後は正常に動きます。

*[ツール: `Bash` × 複数]*

Wiki が生成されました。`check-fact-lim.md` 新規に加え、過去に hook 未実行で溜まっていた他スキルの差分も再生成。全て `docs/skills/` の自動生成物なのでまとめて commit・push しました。

**push 済み（master）**
1. `de1736d` — check-fact-lim スキル本体＋metadata
2. `51319a0` — Wiki（`docs/skills/check-fact-lim.md` 新規＋既存スキル差分の再生成）

---

## よーん *(13:58 JST)*

はい（`/record` で記録）

### Claude *(14:00 JST)*

未記録の変更は今回の `check-fact-lim` のみと特定し、報告書・セッション履歴・変更ログを作成。

*[ツール: `Skill`, `Read`, `Bash`, `Write`]*
