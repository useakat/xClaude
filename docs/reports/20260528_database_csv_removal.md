---
title: database CSV アーカイブ削除・残存参照の Sheets 化
date: 2026-05-28
tags: [infra, skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../history/20260528_database_csv_removal/)

## 背景・動機

`database/*.csv` は 2026-05-03 の「database CSV → Google Sheets 移行」より前のスナップショットで、移行後は読み取り専用の参照用アーカイブとして残していた。実体（正データ）は Google Sheets。

今回、ネタ補充ルーティンが `database/noteNeta.csv` を直接カウントして未使用ネタ数を判定していたため、問題が表面化した。CSV アーカイブは古く、未使用が 3 件しかない状態だった一方、正である Sheets には未使用が 135 件あった。この乖離によりルーティンが「ネタ不足」と誤判定し、不要な `/research-note-projectx` を実行してしまった。

アーカイブ CSV は更新されないまま乖離が広がるだけで、誤判定の温床になる。Sheets が唯一の正データという方針が確立している以上、CSV アーカイブは役目を終えていると判断し、削除して残存参照を Sheets に向けることにした。

## 実施内容

- `database/` 配下の CSV 7 件を削除（newsTopics / noteNeta / onePointNeta / outputs / pain / persona / what）
- `research-plan` スキルに残っていた `database/noteNeta.csv` 参照 2 箇所を「noteNeta シート」表現に修正
- ネタ補充ルーティンの未使用判定を、ローカル CSV カウントから Sheets のステータス列ベースに変更（ルーティン本文は Web トリガー設定のためリポジトリ外。判定列は onePointNeta=I列・noteNeta=L列で「未使用」をカウント）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `database/newsTopics.csv` ほか CSV 6 件 | 削除（参照用アーカイブの廃止） |
| `.claude/skills/research-plan/SKILL.md` | 冒頭とファイル保存セクションの `database/noteNeta.csv` 参照を「noteNeta シート」表現に修正 |

## 設計判断

- **CSV を残さず削除した理由**：Sheets が正データである以上、更新されないアーカイブは乖離して誤判定を生むだけ。git 履歴に残るため復元も可能で、保持コストに見合わない。
- **参照修正を `research-plan` のみに限定した理由**：よーんの指示により今回は `research-plan` スキルの参照だけを Sheets 化した。`scripts/` 配下のスクリプトや CLAUDE.md・docs にも CSV 参照が残っているが、スコープ外として未着手（今後の課題に記載）。

## 確認結果

- `git status` で `database/*.csv` 7 件が削除（`D`）されていることを確認。
- Sheets `noteNeta!L:L`（ステータス列）で未使用が 141 件（新ネタ 6 件追加後）であることを確認。CSV の 3 件との乖離が削除判断の根拠。
- `research-plan/SKILL.md` を grep し、`.csv` 参照が残っていないことを確認。

## 今後の課題

CSV を参照したままの箇所が残っている。必要に応じて Sheets 参照への書き換え、または廃止を検討する：

- 現役スクリプト：`scripts/csv_reader.py` / `scripts/sheets_manager.py` / `scripts/update_neta_status.py` / `scripts/sync_to_sheets.sh`
- ドキュメント：`CLAUDE.md`（構造ツリー・アーカイブ記述）、`docs/database.md`、`docs/skills/*`
