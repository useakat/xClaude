---
title: commit_and_sync.sh を対象限定コミットに対応させ全7スキルを追従
date: 2026-08-14
tags: [infra, workflow, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md#2026-08-14) ｜ [セッション履歴→](../../history/20260814_commit_and_sync_targeted_paths/)

## 背景・動機

`scripts/commit_and_sync.sh` は `git add -A` で作業ツリー全体をステージしていた。**複数の Claude セッションが同じリポジトリで同時に動く運用**では、これが他セッションの未コミット作業を巻き込む。

同日の `/record` 実行時に実際に発生し、43ファイル・8,833行のコミットになりかけた（SOHO販促の下書き、チャンドラセカール記事、W003 の作業ファイル等が混入）。`git reset --soft` で戻し、対象5ファイルに絞り直して再コミットしている。

これは今回が初めてではない。過去のセッション履歴を検索すると、**同じ回避作業が少なくとも6回**繰り返されていた。

- 2026-06-14 「`commit_and_sync.sh` は `git add -A` で `.envrc`・tmux ログを巻き込むため不使用」
- 2026-06-18 「無関係な未コミットファイルを巻き込まないため、関連ファイルを明示指定してコミットします」
- 2026-06-20 「作業ツリーには未コミットの WIP が多数あります。`commit_and_sync.sh` の一括 add は使わず、関連ファイルだけを選択コミットします」
- 2026-06-27（2件）「commit_and_sync が全 add する場合は、cron 関連ファイルのみ選択コミットします」
- 2026-07-03 「`commit_and_sync.sh` が全未追跡ファイルをステージしたため、記録コミットに無関係な生成物も含まれてしまいました」

さらに 2026-07-16 の報告書には、リスクとして明記もされていた。

> 「Always allow」クリックが git 差分になる：今後どの環境でもクリックのたびに settings.local.json が書き換わり、`commit_and_sync.sh`（全ファイルステージ）経由で routine のコミットに同乗して master に入り得る。

毎回その場で手作業回避していたため恒久対処が入っていなかった。スクリプト側で対象を絞れるようにする。

## 実施内容

### `scripts/commit_and_sync.sh`

- **第2引数以降で対象パスを受け取る**ようにした（`git add -- "${PATHS[@]}"`）
- パス省略時は従来どおり `git add -A` にフォールバックするが、**警告を表示**する（既存の呼び出し元を壊さないための後方互換）
- コミット前に**含まれるファイル一覧を表示**する（巻き込みがあれば目視で気づける）
- 対象を指定したが差分が無い場合、**空コミットせずに終了**する
- Co-Authored-By が `Claude Sonnet 4.6` のまま古かったため `Claude Opus 5` に更新

```bash
# 対象限定（推奨）
bash scripts/commit_and_sync.sh "message" <path> [<path>...]
# 全変更（非推奨・警告あり）
bash scripts/commit_and_sync.sh "message"
```

### 呼び出し元7スキルに対象パスを明示

| スキル | 対象パス |
|---|---|
| `record` | `docs/changelog.md`＋報告書＋セッション履歴 |
| `reporter-daily` | `docs/reports/daily/[DATE_ISO].md` |
| `reporter-weekly` | `docs/reports/weekly/[week_id].md`＋`index.md` |
| `reporter-monthly` | `docs/reports/monthly/[month_id].md`＋`index.md` |
| `update-permissions` | `.claude/settings.json` |
| `save-session` | `docs/history/YYYYMMDD_slug.md` |
| `classify-followers` | `docs/reports/YYYYMMDD_follower_persona_update.md` |

各スキルに「対象パスを必ず渡す。省略すると `git add -A` にフォールバックし、他セッションの未コミット作業を巻き込む」という注記を追加した。`record` にはさらに「実装ファイルは STEP 4.7 の時点でコミット済みのはずなので、ここでは docs のみを対象にする」と明記。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/commit_and_sync.sh` | 対象パス引数の追加・警告・ファイル一覧表示・空コミット防止・Co-Authored-By 更新 |
| `.claude/skills/record/SKILL.md` | STEP 6-1 に対象パス3件を明示＋注記 |
| `.claude/skills/reporter-daily/SKILL.md` | 日報ファイルを明示＋注記 |
| `.claude/skills/reporter-weekly/SKILL.md` | 週報＋index を明示＋注記 |
| `.claude/skills/reporter-monthly/SKILL.md` | 月報＋index を明示＋注記 |
| `.claude/skills/update-permissions/SKILL.md` | `settings.json` を明示＋注記 |
| `.claude/skills/save-session/SKILL.md` | 履歴ファイルを明示＋注記 |
| `.claude/skills/classify-followers/SKILL.md` | レポートを明示＋注記 |

## 設計判断

- **後方互換を残した**：パス省略時にエラーで止める案も考えたが、cron/routine から呼ばれる経路があると無人実行が停止する。警告つきフォールバックにして、スキル側で必ず渡す運用にした。
- **スクリプト側で解決した**：スキルに「明示指定せよ」と書くだけでは、過去6回と同じく毎回の判断に依存する。スクリプトが対象を受け取れる形にして初めて、スキルが機械的に渡せるようになる。
- **ファイル一覧の表示を追加した**：万一フォールバックしても、コミット直前に何が入るか見えれば気づける。今回の混入も、この表示があれば即座に検知できていた。

## 確認結果

一時リポジトリで4パターンを検証：

| ケース | 結果 |
|---|---|
| 対象限定（`keep.md` のみ指定） | `keep.md` のみコミット、`other.md` は未コミットのまま |
| 対象指定・差分なし | 空コミットせず「変更なし」で終了 |
| パス省略 | 警告表示のうえ従来どおり全変更をコミット |
| メッセージ無し | 使用方法を表示して終了 |

さらに**本変更自身のコミットを新スクリプトの対象限定モードで実行**し、指定8ファイルのみが含まれ、作業ツリーの他の未コミット変更（`logs/`・`check-fact-lim` 等）が混入しないことを実地で確認した。

## 今後の課題

- `save-session` の呼び出しパスが `/home/user/xClaude/...` とハードコードされたまま（他スキルは `git rev-parse --show-toplevel`）。今回の変更対象外だが、環境差で動かない可能性がある
- `docs/` 配下のスキルページは commit 時の hook（`update_wiki_skills.py`）で自動再生成されるため、本変更の内容は次回コミット時に Wiki へ反映される
