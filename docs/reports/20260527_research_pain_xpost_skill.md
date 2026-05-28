---
title: research_pain-xpost スキル新設
date: 2026-05-27
tags: [skill]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260527_research_pain_xpost_skill/)

## 背景・動機

X 投稿への反応（リプライ・引用RT）には、読者が本当に知りたがっていること・つまずいている点・誤解・もっと知りたいと感じた点が表れる。これらは note 記事のテーマを決めるうえで一次情報として価値が高いが、これまで「特定の投稿に対する反応を集めて、ニーズを抽出し、note テーマに変換する」という流れを担うスキルがなかった。手作業では再現性が低く、ブランド（執念の物語軸）への接続も属人的になる。

そこで、特定 X ポストのリプライ・引用RTを取得 → ニーズ・疑問を構造化 → note テーマに変換する一連の流れをスキル化した。引用RT・リプの取得は既存の `ops_post-reactions` が持つ仕組み（xmcp の `getPostsQuotedPosts` / `searchPostsRecent` と「リプ・引用一覧」シート、`fetch_sheet_replies.py`）をそのまま再利用し、新規スクリプトは作らない方針とした。

## 実施内容

- `research_pain-xpost` スキルを新設（7 STEP 構成）
  - STEP 0: `brand.md` / `plan.md` を Read してブランド・発信軸を確認
  - STEP 1: URL / tweet_id から ID を抽出
  - STEP 2: xmcp `getPostsQuotedPosts` で引用RTを取得
  - STEP 3: リプを「両方」から取得（直近7日は xmcp `searchPostsRecent`、過去分は `fetch_sheet_replies.py` でシート補完）し、マージ＆重複除去
  - STEP 4: 元投稿の文脈把握
  - STEP 5: 反応を5観点（疑問／誤解／もっと知りたい／驚き・共感／反論）でクラスタリングし、頻度付きで「本当の論点」を3〜5個に言語化
  - STEP 6: note テーマを5件以上提案（根拠コメント引用付き、執念の物語軸・plan.md 発信軸に接続）、noteNeta 既存と重複チェック
  - STEP 7: ユーザーが選んだテーマのみ noteNeta シートへ追記
- `metadata.yaml` に `research_pain-xpost: リサーチ・分析` を登録
- 作成後、スキル名を `research-note-from-post` から `research_pain-xpost` にリネーム（ディレクトリ名・frontmatter `name`・`metadata.yaml` の3か所）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/research_pain-xpost/SKILL.md` | 新規作成（7 STEP のスキル定義） |
| `.claude/skills/metadata.yaml` | `research_pain-xpost` を `リサーチ・分析` カテゴリに登録 |

## 設計判断

- **データソースは xmcp とシートの両方併用**：xmcp で引用RTと直近7日のリプを直接取得し、過去のリプ・引用RTは GAS が毎日収集する「リプ・引用一覧」シートから補完する。取りこぼしを最小化するため。
- **noteNeta への保存は承認後のみ**：提案テーマを勝手に追記せず、ユーザーが選んだものだけ append する（`research-note-projectx` は自動追記だが、本スキルは反応分析からの推定要素が多いため承認制とした）。
- **新規スクリプトを作らない**：`ops_post-reactions` の取得スクリプトと xmcp ツールを再利用。

## 確認結果

- `/research_pain-xpost <URL>` でスキルが呼び出せることを確認。
- 実行時、xmcp サーバーはローカル（`/root/xClaude`）向け設定のため、クラウド（web）セッションでは引用RT・リプの直接取得が不可。この環境ではシート補完のみ機能する。xmcp を使う取得はローカルセッションでの実行が前提。

## 今後の課題

- xmcp 依存ステップ（STEP 2・3a）はクラウドセッションでは動かないため、リモートでも取得できる手段（GAS 収集範囲の拡大、もしくはリモート用 X 取得スクリプト）の検討。
