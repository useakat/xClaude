---
title: ops_post-reactions スキル設計・実装 — セッション履歴
date: 2026-05-21
sidebar:
  hidden: true
---

# セッション履歴

> 2026-05-21 のセッション作業ログ。「実は」ワンポイント解説投稿への反応分析（2026-05-20）を汎用スキルとして実装した記録。設計の試行錯誤（3ラウンドのフィードバック）と最終実装までを収録。

← [報告書へ戻る](../reports/20260521_ops_post_reactions_skill/)

---

## 前提確認：searchPostsAll の使用可否

---

### よーん

まず `searchPostsAll` が使えるか確認して。

---

### Claude

xmcp の HTTP セッション経由で実測。結果: `403 Unsupported Authentication: OAuth 1.0a User Context is forbidden for this endpoint`。`searchPostsAll` は App-Only OAuth 2.0 が必要なため使用不可と確定。

リプライ取得は `searchPostsRecent`（7日以内）と GAS 蓄積シートの組み合わせで代替する設計が必要。


## GetRepliesAndQuotes.js の改修（別報告書と並行）

リプライ蓄積基盤として GetRepliesAndQuotes.js に `expansions=author_id` + `user.fields=username,name` を追加し、B列=@username・C列=アカウント名の7列構成に変更。この作業の詳細は [GetRepliesAndQuotes GAS スクリプト新設の報告書](../reports/20260521_get_replies_and_quotes_gas/) を参照。


## スキル設計（Round 1）

`analyze-post-reactions` スキルの実装計画を提示：
- STEP 2 で `/tmp/fetch_target_posts.py` を毎回生成・実行
- `gspread` + SA 認証で Sheets を読む設計


### よーん

まず、このスクリプトを毎回生成するのは無駄じゃない？あと、`gspread` の API 使用を想定しているが、20260517 の報告書（Drive MCP download_file_content のコスト検証）にあるように…スクリプトが MCP プロキシに直接 HTTP POST する方法は、`fetch_x_analytics_csv.py` を参考にして。

- スクリプトを `scripts/analyze-post-reactions/` に事前作成・再利用する方式に変更
- `fetch_x_b_col.py` 準拠の SA JWT + openssl + 直接 Sheets API 呼び出しパターンに変更
- LLM コンテキストを経由しないためトークンコストゼロ


## スキル設計（Round 2）

### よーん

リプライ取得に使う `searchPostsRecent` エンドポイントは直近7日分しか取れない。「リプ・引用一覧」シートが解決策になる。このことを踏まえて実装計画を修正して。まだ実装はしないでね。

- リプライ取得を「シート参照（全期間） + `searchPostsRecent` 補完（7日以内のみ）」の2段階に変更
- `fetch_sheet_replies.py` を追加（リプ・引用一覧シートから tweet_ids 絞り込み）
- シートを全件 MCP 取得すると大量トークン消費になるため、スクリプトから SA JWT で直接 API 呼び出し


### よーん

データが多くなってくると全件取得は効率悪い。STEP 6 で `total followers = 4183` とあるけど、これはその日によって変わる。

- `fetch_sheet_replies.py` をスクリプト化（MCP 経由でなく SA JWT で直接取得）
- `total_followers` を固定値 4183 から `len(follower_persona_llm.json)` の動的カウントに変更


## スキル設計（Round 3・承認）

計画をよーんに提示し承認。主な確定事項：

| 項目 | 決定内容 |
|---|---|
| スクリプト配置 | `scripts/analyze-post-reactions/` に事前作成（毎回生成しない） |
| Sheets アクセス | SA JWT + openssl + 直接 HTTP（`fetch_x_b_col.py` 準拠） |
| リプライ取得 | シート優先（全期間）+ searchPostsRecent 補完（7日以内のみ） |
| total_followers | `len(follower_persona_llm.json)` で動的カウント |
| how_id フィルタ | SS2 outputs シートとの照合で絞り込み |


## 実装フェーズ

### X投稿一覧 列構成確認

`mcp-gsheets` で X投稿一覧の1行目を取得し列構成を確定：

- A=投稿日時 / B=ポストURL / C=ポスト本文
- Q(17)=プロフアクセス / AC(29)=フォロー増

### スクリプト3本の作成

**`fetch_target_posts.py`**（SS1 X投稿一覧フィルタ）
- `--keyword` / `--how_id` / `--days_back` 引数
- `--how_id` は SS2 outputs シートとのURL照合で絞り込み
- 出力: `/tmp/target_posts.json`

**`fetch_sheet_replies.py`**（リプ・引用一覧フィルタ）
- `--tweet_ids` で絞り込み
- (username, parent_tweet_id) で重複除去
- 出力: `/tmp/sheet_replies.json`

**`compute_metrics.py`**（Sheets アクセスなし）
- フォロワー判定・ペルソナ割当・指標計算
- 反応感度 = (F反応数/F反応合計) / (全F数/全フォロワー)
- 反応密度 = 延べ反応数 / ユニーク反応者数
- 出力: `/tmp/metrics_output.json`（反応感度降順）

### SKILL.md・metadata.yaml の作成

- `.claude/skills/analyze-post-reactions/SKILL.md`（7ステップフロー）
- `.claude/skills/metadata.yaml` に追記


## リネーム

### よーん

スキル名を `ops_post-reactions` にして。

ディレクトリ・スクリプトパス・metadata.yaml・SKILL.md 内タイトルをすべて `ops_post-reactions` に変更してコミット・プッシュ。


## 最終コミット構成

| コミット | 内容 |
|---|---|
| `957eaf7` | feat(skill): ops_post-reactions スキル新設・スクリプト3本追加 |
| `4c3663f` | docs: ops_post-reactions スキル新設の報告書・変更ログを追加 |
