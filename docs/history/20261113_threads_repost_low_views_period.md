---
title: Threads 低 views 期（7/24〜9/23）の投稿を 1 日 1 本ずつ再投稿する下書き作成 cron を新設 — セッション履歴
date: 2026-11-13
sidebar:
  hidden: true
---

# セッション履歴

> 2026-11-11〜13 のセッション作業ログ。

← [報告書へ戻る](../../reports/20261113_threads_repost_low_views_period/)

---

## よーん *(21:46 JST)*

threads の投稿の多くが 2桁 views くらいしか出なくなった時期が５月以降にあるんだけど、それがいつからいつまでだったか調べて

### Claude *(21:46 JST)*

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`]*

Threads投稿一覧（本体投稿 201 本、リプライ除外）の views を週別・日別に見た結果です。

**2 桁 views の時期：2026 年 7 月 24 日ごろ 〜 9 月 23 日（約 2 か月）**

- **始まり**：7/23 までは 2,109 / 5,033 / 587 など通常の伸びがあり、**7/24 20:00 の投稿（27 views）以降**、7/25 の 142 を最後に 100 を超えなくなる
- **終わり**：9/23 20:00（56 views）まで続き、**9/24 12:00 の投稿（437 views）から回復**。9/26 に 2,183、9/28 に 12,131 / 10,070 と完全に戻る

週別の中央値（本体投稿のみ）：

| 週 | 本数 | 中央値 | 2 桁以下 |
|---|---|---|---|
| 7/13〜 | 14 | 426 | 3 |
| 7/20〜 | 17 | 169 | 7（7/24 から） |
| 7/27〜 | 8 | 28 | 8 |
| 8/3〜 | 10 | 23 | 9 |
| 8/10〜 | 15 | 18 | 15 |
| 8/17〜 | 6 | 14 | 6 |
| 8/24〜 | 7 | 12 | 7 |
| 8/31〜 | 12 | 9 | 12 |
| 9/7〜 | 12 | 15 | 12 |
| 9/14〜 | 13 | 15 | 13 |
| 9/21〜 | 14 | 115 | 7（9/23 まで） |
| 9/28〜 | 10 | 985 | 0 |

補足：
- 期間中 8 週間で 1 本も 100 views を超えていません（最大は 8/3 週の 104 が 1 本だけ）。投稿頻度は保っていたので、投稿量の問題ではなく配信側で抑えられていた形です
- 5 月は投稿がほぼ無く（4/27 週 2 本の後、6/29 週まで空白）、「5 月以降」の中で該当する落ち込みはこの 7/24〜9/23 の 1 回だけでした
- 9/24 前後に何か操作（プロフィール変更・投稿形式の変更・アプリ側の対応など）をしていれば、それが回復のきっかけの候補になります。心当たりがあれば changelog や日報と突き合わせます

---

## よーん *(22:33 JST)*

7/24〜9/23 の間に threads に投稿したものを、再度順番に threads に投稿するようにしたい。どうしたらいいか考えて計画を立てて。

### Claude *(22:33 JST)*

*[ツール: `Agent`, `Bash`, `Bash`]*

Image URLs still resolve (8/8 checked), so the images can be re-downloaded now before the CDN links expire. Waiting on the exploration of the posting pipeline before designing.

*[ツール: `Bash`]*

Enough is known to pin down the design choices. A few decisions are yours:

*[ツール: `AskUserQuestion`, `Read`, `Read`, `Bash`, `Bash`, `Write`, `ToolSearch`, `ExitPlanMode`, `Read`, `Bash`, `Write`, `Write`, `Edit`, `Bash`, `Bash`, `Bash`, `Bash`]*

Checking the link-reply exclusion and carousel note cases, and verifying the memo tag doesn't disturb the email parser.

*[ツール: `Bash`, `Bash`]*

The memo text contained the literal `[リプ]`, which the tag parser then matched from the memo. Fixing the wording and re-verifying.

*[ツール: `Edit`, `Bash`, `Bash`, `Bash`, `Bash`, `Bash`]*

実装が完了し、1 本目の下書きまで作成済みです。

**作成・変更**
- `scripts/make_threads_repost_draft.py`（新規）：キュー生成（`--init`）、毎回先頭 1 本の【threads投稿】下書き作成、`--redo N`、再投稿URL の自動突合
- `scripts/run_threads_repost_draft.sh`（新規）：flock・ログ・失敗時 Gmail 通知
- `scripts/run_threads_post.sh`：ヘッダコメントのみ更新
- `logs/threads_repost_queue.csv`：98 行のキュー（順番 1 に下書き作成日 2026-11-12 を記録済み）
- crontab：`0 18 * * *` 下書き作成、`0 9 * * *` 投稿 を追加

**確認結果**
- `--init --dry-run`：98 件、7/24 18:53 大赤斑 → 9/23 の順
- 順番 4（カッシーニ）：続きリプ 1 件が `[リプ]` に入る／順番 35：リンク入りリプのみ → 付けずメモに注記／順番 8：カルーセル → 1 枚投稿の注記
- 生成した本文を `extract_tag.py` に通して 投稿文・画像URL・リプ が正しく取れることを確認。途中で「メモ内の `[リプ]` という文字列を本文として拾う」不具合を見つけて修正済み
- ラッパー実行で Gmail 下書き「【threads投稿】実は、木星の大赤斑はだんだん小さくなって」が作成されたことを確認

**運用**：Gmail の下書きを確認（先頭の `[メモ]` に元 URL・元 views・時期依存語の注意）→ 自分宛に送信 → 翌 09:00 に投稿。スキップしたい投稿は下書きを削除するだけで次に進みます。

commit & push してよいですか？（対象は上記の新規 3 ファイル＋`run_threads_post.sh`＋キュー CSV。ログは含めません。）

---

## よーん *(14:38 JST)*

前回のcommit push /record

### Claude *(14:38 JST)*

Threads 再投稿の実装を commit & push し、続けて `/record` を実行します。まず index が空であることを確認してから、対象ファイルだけをコミットします。

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`]*

master に push しました（`e0f04d9`、対象 4 ファイルのみ。混入なし）。続いて `/record` を実行します。

*[ツール: `Skill`]*

---
