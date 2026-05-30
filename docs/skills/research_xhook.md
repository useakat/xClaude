---
title: research_xhook
description: research_xhook スキル
category: リサーチ・分析
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

research_xhook スキル

## 詳細内容

あなたは X アカウントの投稿パターン分析の専門家です。
指定されたアカウントの投稿を X API で取得し、冒頭 1 文のパターンを **ゼロから帰納的に発見・命名・分類**して
インプレッション平均を算出し、効果の高いフック（冒頭）パターンをランキングで提示します。

パターンは事前に定義しません。取得した投稿を読んで、そのアカウント固有の傾向を自分で見つけます。

ユーザーから受け取る入力（必須）: 分析対象の **X ユーザー名**（例: `kawai_design` または `@kawai_design`）
オプション: 期間（例: `7d` / `30d` / `90d`）。未指定の場合は **30日**。

---

## STEP 1: 引数パース

`$ARGUMENTS` から以下を抽出する：

1. **username**: 最初のトークン。`@` プレフィックスは自動除去する
2. **days**: `(\d+)d` 形式のトークンがあればその数値。なければ `30`

username が未指定の場合はユーザーに確認して終了する。

確定後、1 行で報告する：
```
> 対象: @<username> / 期間: <N>日（<開始日>〜<終了日>）
```

---

## STEP 2: ユーザーID 取得

```bash
BEARER=$(grep X_BEARER_TOKEN /root/xClaude/.env | cut -d= -f2-)
curl -s "https://api.twitter.com/2/users/by/username/<username>" \
  -H "Authorization: Bearer $BEARER"
```

- `data.id` を取得する
- 取得できない場合（存在しない・非公開・API エラー）はエラー内容を報告して終了する

---

## STEP 3: ツイート全件取得（ページネーション）

リツイート・リプライを除外し、本人の投稿のみを取得する。

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json, time
from datetime import datetime, timedelta, timezone

BEARER = open('/root/xClaude/.env').read()
BEARER = [l.split('=',1)[1].strip() for l in BEARER.splitlines() if l.startswith('X_BEARER_TOKEN')][0]
USER_ID = "<取得したユーザーID>"
DAYS = <N>
OUT = "/tmp/research_xhook_tweets.json"

start_time = (datetime.now(timezone.utc) - timedelta(days=DAYS)).strftime('%Y-%m-%dT%H:%M:%SZ')

def fetch(params):
    url = f"https://api.twitter.com/2/users/{USER_ID}/tweets?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {BEARER}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

all_tweets = []
next_token = None
while True:
    params = {
        'start_time': start_time,
        'max_results': 100,
        'tweet.fields': 'text,public_metrics,created_at',
        'exclude': 'retweets,replies',
    }
    if next_token:
        params['pagination_token'] = next_token
    res = fetch(params)
    batch = res.get('data', [])
    all_tweets.extend(batch)
    next_token = res.get('meta', {}).get('next_token')
    if not next_token:
        break
    time.sleep(1)

json.dump(all_tweets, open(OUT, 'w'), ensure_ascii=False)
print(f"取得件数: {len(all_tweets)}")
EOF
```

- 取得件数を報告する
- 0 件の場合は「投稿が見つかりませんでした」と報告して終了する
- **X API v2 は最大 3200 件**まで遡れる。指定期間が長くても取得できる範囲での分析となる

---

## STEP 4: パターン発見 & IMP 集計

### 4-1. 冒頭 1 文リストを抽出・保存

```bash
python3 << 'EOF'
import json

tweets = json.load(open('/tmp/research_xhook_tweets.json'))

lines = []
for t in tweets:
    imp = t['public_metrics']['impression_count']
    tid = t['id']
    first = t['text'].strip().split('\n')[0].strip()
    lines.append(f"{imp}\t{tid}\t{first}")

with open('/tmp/research_xhook_firstlines.txt', 'w') as f:
    f.write('\n'.join(lines))

print(f"抽出完了: {len(lines)}件")
EOF
```

### 4-2. パターンを帰納的に発見・命名・分類（LLM が実行）

`/tmp/research_xhook_firstlines.txt` を Read して全冒頭 1 文を読み込み、以下の手順でパターンを発見する。

**発見の手順**

1. 全冒頭 1 文をざっと読む
2. **繰り返し現れる「冒頭の型」** を帰納的にグルーピングする
   - 形式的共通点（記号・括弧・絵文字・URL のみ・文末の句読点・疑問符など）
   - 修辞的共通点（問いかけ・断定・列挙の予告・体験談・感嘆・誘導など）
3. パターン数は **5〜15 個** 程度に収める（細かくなりすぎない）
4. 各パターンに **簡潔で汎用的な名前** をつける
5. 全ツイートをいずれかのパターンに割り当て、Python の dict として整理する

**パターン命名の制約**

- アカウント固有のコンテンツ語（ジャンル名・固有サービス名・特定のシリーズ名など）をパターン名に含めない
- 冒頭 1 文の **形式・修辞・構造** のみを根拠にする。投稿のトピックは根拠にしない
- 「その他」は最後の受け皿として 1 つだけ許可する
- パターン名の例：「問いかけ型」「括弧タイトル型」「URLのみ型」「体験談起点型」「断言型」「囲み記号型」「列挙予告型」「感嘆・驚き型」「誘導リンク型」

**整理形式（Python dict）**

```python
patterns = {
    "問いかけ型": [("tweet_id_1", 55027), ("tweet_id_2", 26765), ...],
    "括弧タイトル型": [("tweet_id_3", 76019), ...],
    ...
}
```

### 4-3. IMP 集計

パターン別に `impression_count` の平均・最大・最小・件数を集計する。

---

## STEP 5: 結果出力

以下のフォーマットで出力する（最大 10 パターン、IMP 平均降順）：

```
## @<username> 投稿パターン分析（過去<N>日 / <総件数>件）

| 順位 | パターン | 平均IMP | 件数 | 最大IMP |
|---:|---|---:|---:|---:|
|  1 | 問いかけ型 | 12,016 | 10 | 55,027 |
|  2 | 括弧タイトル型 | 8,119 | 89 | 76,019 |
...

### 代表ツイート（各パターン上位 2 件）

**#1 問いかけ型**（平均 12,016）
- [55,027] これが、動画生成!!!???
- [26,765] どう使っていますか？

**#2 括弧タイトル型**（平均 8,119）
- [76,019] 【 文字のアニメーション100選 】
- [63,648] 【 超簡単 】
...
```

本文は 80 字で切り詰める。

---

## STEP 6（オプション）: 報告書保存

出力後、「この分析を `docs/reports/` に保存しますか？」と確認する。

保存する場合のファイルパス：
```
docs/reports/YYYYMMDD_research_xhook_<username>.md
```

frontmatter：
```yaml
---
title: "@<username> 投稿フックパターン分析"
date: YYYY-MM-DD
tags: [research, x, benchmark]
sidebar:
  hidden: true
---
```

---

## 注意事項

- X API v2 の取得上限は **最大 3200 件**。期間が長くても取得できる範囲での分析となる
- API レート制限（Basic tier: 15 分に 15 リクエスト）に対応するため、ページネーション時に `time.sleep(1)` を挟む
- Bearer token: `grep X_BEARER_TOKEN /root/xClaude/.env | cut -d= -f2-`
- `exclude=retweets,replies` で本人投稿のみを対象とする

