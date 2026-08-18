---
title: freeze_first_draft.sh / update_wiki_skills.py 呼び出しをサブディレクトリ起動対応に修正
date: 2026-08-18
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md#2026-08-18) ｜ [セッション履歴→](../../history/20260818_freeze_first_draft_subdir_fix/)

## 背景・動機

SOHO 販促投稿（W001）の初稿→最終稿の差分分析を行おうとしたところ、`draft/first-draft.md` が一度も作成されていないことが判明した。8/15 に導入した凍結フック（PostToolUse Write|Edit で記録 → Stop / UserPromptSubmit で凍結）が、この投稿の制作セッションでは一度も発火していなかった。

原因を settings.json で確認したところ、hook コマンドが `$CLAUDE_PROJECT_DIR/scripts/<script>` を決め打ちしていた。`$CLAUDE_PROJECT_DIR` はローカル環境ではセッション起動時の cwd に展開される。SOHO 投稿はこのセッションが `projects/w001` を作業ディレクトリとして起動されたため、`$CLAUDE_PROJECT_DIR` が `/root/xClaude/projects/w001` を指し、`scripts/freeze_first_draft.sh` が存在しないパスとなって `|| true` で無音失敗していた。

同種の問題は 2026-07-09 に mcp-gsheets の起動コマンドで一度発見・修正済みだった（`docs/reports/20260709_mcp_gsheets_launch_upward_search.md`）が、その修正は `.mcp.json` 内の該当コマンドに限定されており、`.claude/settings.json` の他の hook には波及していなかった。

## 実施内容

- `.claude/settings.json` の hook コマンドを、`$CLAUDE_PROJECT_DIR` から上方向にディレクトリを辿り、対象スクリプトが見つかった時点で実行する方式に変更（mcp-gsheets と同じパターン）。対象は以下4箇所：
  - `freeze_first_draft.sh --record`（PostToolUse Write|Edit）
  - `freeze_first_draft.sh`（Stop）
  - `freeze_first_draft.sh`（UserPromptSubmit）
  - `update_wiki_skills.py`（PostToolUse git commit）
- サブディレクトリ起動（`CLAUDE_PROJECT_DIR=/root/xClaude/projects/w002` 等）とルート起動の両方で、シェルロジックを直接実行してスクリプトの解決先を検証
- `style/story-check.md`（版1.1→1.2）に、相対時間表現の起点明示ルールを項目1へ追記。SOHO 制作で「技術者たちは…ソフトウェアを書き、宇宙にいるSOHOへ送った。40日後、…」という書き方が、よーん自身にも「ソフト送信からの経過」と誤読された実例に基づく

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | freeze_first_draft.sh（3箇所）・update_wiki_skills.py（1箇所）の hook コマンドを上方探索方式に変更 |
| `style/story-check.md` | 項目1【時系列】に相対時間の起点明示ルールを追記。版1.1→1.2 |

## 設計判断

- **新しいパターンを発明せず、既存の確立済み解決策を踏襲した**：`.mcp.json` の mcp-gsheets 起動コマンドが同じ問題を同じ「上方探索＋フォールバック」で解決済みだったため、settings.json 側にも同じロジックをそのまま移植した。異なる修正方式が併存すると保守コストが上がるため。
- **update_wiki_skills.py 呼び出しの WHILE ループ内で python3 を実行**：シェル側でファイルの存在を確認してから python3 を起動する形にし、bash と python3 のプロセス起動を1回に抑えた。
- **xmcp サーバー起動（SessionStart）は今回のスコープ外とした**：同種の未ガードパターン（`$CLAUDE_PROJECT_DIR/xmcp` の存在チェック）が残っているが、依頼範囲が「Wiki 自動更新」の修正に限定されていたため、今回は着手していない。

## 確認結果

- `python3 -c "import json; json.load(open('.claude/settings.json'))"` で JSON 構文を検証
- サブディレクトリ起動シミュレーション（`CLAUDE_PROJECT_DIR=/root/xClaude/projects/w002` 等）とルート起動シミュレーション（`CLAUDE_PROJECT_DIR=/root/xClaude`）の両方で、`freeze_first_draft.sh` と `update_wiki_skills.py` が正しく `/root/xClaude/scripts/` 配下に解決されることを確認

## 今後の課題

- `SessionStart` の xmcp サーバー起動コマンドにも同じ `$CLAUDE_PROJECT_DIR` 決め打ちパターンが残っている。サブディレクトリ起動セッションで xmcp が起動しない可能性があり、別途対応が必要
- 今回のバグにより、8/15〜8/17 頃に `projects/` 配下のサブディレクトリから起動されたセッションで生成された投稿の `first-draft.md` は欠落している可能性がある（過去分の遡及復元は行っていない）
