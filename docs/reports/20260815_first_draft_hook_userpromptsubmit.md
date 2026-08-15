---
title: first-draft 凍結フックに UserPromptSubmit を追加
date: 2026-08-15
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260815_first_draft_hook_userpromptsubmit/)

## 背景・動機

[8/10 に新設した初稿凍結フック](./20260810_first_draft_freeze_hook/)は、PostToolUse(Write|Edit) で `draft.md` への書き込みパスを記録簿に控え、Stop（＝ユーザーに原稿を提示した瞬間）で `first-draft.md` へコピーする2段階構成だった。

W001 の「オポチュニティ販促」記事の X 長文原稿では、`draft/draft.md` が同一セッション中に9回（Write 1回・Edit 1回・Write 7回）更新されたにもかかわらず、`draft/first-draft.md` が一度も作られていないことが判明した。記録簿は現在空、トランスクリプトにもフックの成功メッセージが実行結果として出力された痕跡が無い。

パスのマッチングやファイル書き込み自体は手元の再現テストで問題なかった。もっとも辻褄が合う説明は、**このセッション中に少なくとも1回、ユーザーによる明示的なターン中断（`[Request interrupted by user]`）が発生しており、中断されたターンでは Stop フックが発火しない**というものだった（hook の実行ログが残っていないため確証は無いが、他の要因は再現テストで排除できている）。

Stop 頼みの単一トリガーだと、中断が起きた回だけ記録簿のエントリが未消化のまま取り残されるリスクがある。

## 実施内容

- `.claude/settings.json` に `UserPromptSubmit` フックを追加。凍結ロジック（`freeze_first_draft.sh` 引数なしモード）はそのまま呼び出す
- Stop はそのまま保険の一段目として残し、UserPromptSubmit を二段目の保険として追加（二重発火しても `first-draft.md` が既にあれば何もしないため無害）
- `freeze_first_draft.sh` の冒頭コメントを更新し、トリガーが2つになった経緯を明記

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | `hooks.UserPromptSubmit` を新設し、`freeze_first_draft.sh`（引数なし）を登録 |
| `scripts/freeze_first_draft.sh` | コメントのみ更新（UserPromptSubmit 追加の理由・Stop との二重発火が無害である旨） |

## 設計判断

**Stop を UserPromptSubmit に置き換えるのではなく、両方登録した。** Stop は「早ければ即座に凍結される」利点があり、通常ケースでは最も早いタイミングで動く。UserPromptSubmit は「よーんが次の発言を送った時点で必ず発火する」ため、Stop の取りこぼしを確実に拾える。凍結処理自体が冪等（`first-draft.md` が既にあれば何もしない）なので、両方登録するコストはほぼゼロ。

## 確認結果

- `python3 -c "import json; json.load(open('.claude/settings.json'))"` で JSON 構文を確認
- `bash -n scripts/freeze_first_draft.sh` でシェル構文を確認
- 実際の初稿凍結の再発防止としては、次回の draft.md 執筆セッションで `first-draft.md` が確実に作られるかを見て確認する

## 今後の課題

- 今回の根本原因（Stop フックがターン中断時に発火しないこと）は再現テストで確証を取れていない推定にとどまる。同様の未凍結が再発する場合は、ledger を record 時点の内容スナップショット方式に変える等、より踏み込んだ対策の検討が必要
