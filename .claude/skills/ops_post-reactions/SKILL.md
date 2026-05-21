# ops_post-reactions スキル

任意の条件で X 投稿を抽出し、その引用RT・リプライ反応者を 19 ペルソナに分類して、反応感度・反応密度・プロフ/フォロー転換率を一覧出力する。

---

## Input

ユーザーから抽出条件を受け取る（未指定の場合は確認する）：

- `--keyword TEXT` : 本文に含まれるキーワード（例: "実は"）
- `--how_id ID`    : 投稿目的 ID（例: W003 = ワンポイント解説）
- `--days_back N`  : 直近 N 日以内に絞り込む

---

## STEP 1: 対象投稿を取得

```bash
python3 scripts/ops_post-reactions/fetch_target_posts.py \
  [--keyword "キーワード"] [--how_id W003] [--days_back 90]
# → /tmp/target_posts.json: [{"tweet_id", "date", "text", "profile_clicks", "follows"}, ...]
```

件数を確認し、0 件の場合は条件を確認してユーザーに伝える。

---

## STEP 2: シートからリプライ・引用RT を取得

```bash
python3 scripts/ops_post-reactions/fetch_sheet_replies.py \
  --tweet_ids "<tweet_id1>,<tweet_id2>,..."
# → /tmp/sheet_replies.json: [{"username", "display_name", "tweet_id", "parent_tweet_id", "type"}, ...]
```

tweet_ids は STEP 1 の結果から抽出する。

---

## STEP 3: 引用RT を xmcp で補完取得

対象投稿ごとに（最大 5 並列で）引用RTを取得：

```
getPostsQuotedPosts(id=<tweet_id>, max_results=100,
  expansions="author_id", user.fields="username,name,description")
```

取得した引用RTと /tmp/sheet_replies.json をマージし、(username, parent_tweet_id) で重複除去して
`/tmp/all_reactors.json` に保存する。

形式: `[{"username": "@...", "display_name": "...", "parent_tweet_id": "...", "type": "リプライ|引用RT"}, ...]`

**7日以内の投稿がある場合のみ** `searchPostsRecent` でリプライを補完：

```
searchPostsRecent(query="in_reply_to_post_id:<tweet_id>",
  expansions="author_id", user.fields="username,name")
```

---

## STEP 4: フォロワー判定 & ペルソナ割当

`persona/follower_persona_llm.json` を Read して、各反応者の username と照合する：

- フォロワー → 既存ペルソナをそのまま使用（`is_follower: true` を付与）
- 非フォロワー → `/tmp/nf_reactors.json` に分離（STEP 5 で LLM 分類）

---

## STEP 5: 非フォロワーの LLM 分類

非フォロワーを 100 件バッチに分割し、並列 Agent（最大 10 並列）で 19 ペルソナ分類する。

各 Agent へのプロンプト（`persona/follower_persona_llm.json` に含まれる `classify-followers/SKILL.md` のペルソナ定義を参照）：

```
以下のユーザーリスト（username / display_name）を 19 ペルソナに分類してください。
分類できない場合は 13（その他）を使用。
出力形式: [{"username": "@...", "persona": N}, ...]

[バッチデータ]
```

各 Agent は `/tmp/nf_react_result_XX.json` に Write する。

---

## STEP 6: 集計

```bash
python3 scripts/ops_post-reactions/compute_metrics.py \
  --reactors /tmp/all_reactors.json \
  --nf_results "/tmp/nf_react_result_*.json" \
  --persona persona/follower_persona_llm.json
# → /tmp/metrics_output.json
```

---

## STEP 7: 出力

`/tmp/metrics_output.json` と `/tmp/target_posts.json` を Read して以下を出力する：

```
## [条件] 反応者ペルソナ分析

対象投稿: N件 / 期間: YYYY-MM-DD〜YYYY-MM-DD
反応者: 合計X人（フォロワーY人・非フォロワーZ人）

| P | ペルソナ | 全F数 | F反応 | 非F反応 | F反応率 | 反応感度 | 反応密度 |
|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ...% | ... | ... |
...（反応感度降順、F反応が0のペルソナは省略可）

---
プロフアクセス合計: X / フォロー増合計: Y（N投稿分）/ 転換率: Z%
```

**注記**: GAS によるリプライ蓄積は毎日 AM4:00 から開始。GAS 稼働前の投稿はリプライ数が過少の可能性あり。

---

## 指標定義

| 指標 | 計算式 |
|---|---|
| F反応率 | F反応数 / 全F数 |
| 反応感度 | (F反応数/F反応合計) / (全F数/全フォロワー) |
| 反応密度 | 延べ反応数 / ユニーク反応者数 |

反応感度 > 1.0 → そのペルソナは平均より反応しやすい。

---

## データソース

| データ | 場所 |
|---|---|
| X投稿一覧 | SS1 `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c` / X投稿一覧 |
| リプ・引用一覧 | SS1 / リプ・引用一覧（GAS が毎日 AM4:00 蓄積） |
| outputs（how_id 参照） | SS2 `1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc` / outputs |
| フォロワーペルソナ | `persona/follower_persona_llm.json` |
