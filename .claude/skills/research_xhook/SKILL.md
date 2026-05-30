あなたは X アカウントの投稿パターン分析の専門家です。
指定されたアカウントの投稿を X API で取得し、冒頭1文のパターンを分類して
インプレッション平均を算出し、効果の高いフック（冒頭）パターンをランキングで提示します。

ユーザーから受け取る入力（必須）: 分析対象の **X ユーザー名**（例: `kawai_design` または `@kawai_design`）
オプション: 期間（例: `7d` / `30d` / `90d`）。未指定の場合は **30日**。

---

## STEP 1: 引数パース

`$ARGUMENTS` から以下を抽出する：

1. **username**: 最初のトークン。`@` プレフィックスは自動除去する
2. **days**: `(\d+)d` 形式のトークンがあればその数値。なければ `30`

username が未指定の場合はユーザーに確認して終了する。

確定後、1行で報告する：
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
- 0件の場合は「投稿が見つかりませんでした」と報告して終了する
- **X API v2 は最大3200件**まで遡れる。指定期間が長くても取得できる範囲での分析となる

---

## STEP 4: パターン分類 & IMP 集計

冒頭1文の抽出ルール：**テキストの最初の改行（`\n`）まで**を取得する。

パターン分類ルール（**優先順位順**に評価する）：

| 優先 | パターン名 | 判定条件 |
|---|---|---|
| 1 | URLのみ | 全体が `^https?://\S+$` にマッチ |
| 2 | 絵文字＋AIニュース速報 | `☀️/🌛/🌞` で始まり `NEWS/ニュース/OHAYO` を含む |
| 3 | 絵文字＋夜の反省会系 | `🌛` で始まり `反省会/AI仕事` を含む |
| 4 | ＼○○／囲み型 | `＼` または `\` で始まる |
| 5 | 絵文字＋シリーズ・感嘆 | Unicode 絵文字で始まる（上記以外） |
| 6 | 【】AIニュース見出し | `【` で始まり `ニュース/NEWS` を含む |
| 7 | 【】タイトル型 | `【` または `[` で始まる（上記以外） |
| 8 | 問いかけ型 | `なぜ/どこ` で始まる、または `？/?` で終わる |
| 9 | AI〜主張・観察 | `AI` または `「AI` で始まる |
| 10 | 一人称起点 | `私が/私は/私も` で始まる |
| 11 | 短文報告・誘導型 | URL除去後の冒頭1文が20字未満 |
| 12 | その他（主張・ストーリー型） | 上記に非該当 |

```python
import json, re
from collections import defaultdict

tweets = json.load(open('/tmp/research_xhook_tweets.json'))

def first_line(text):
    return text.strip().split('\n')[0].strip()

def classify(fl):
    if re.match(r'^https?://\S+$', fl):
        return 'URLのみ（リンク投稿）'
    if re.match(r'^[☀️🌛🌞]', fl) and re.search(r'NEWS|ニュース|OHAYO', fl):
        return '絵文字＋AIニュース速報'
    if re.search(r'^🌛', fl) and re.search(r'反省会|AI仕事', fl):
        return '絵文字＋夜の反省会系'
    if re.match(r'^[＼\\]', fl):
        return '＼○○／囲み型'
    if re.match(r'^[\U0001F300-\U0001FFFF☀-➿]', fl):
        return '絵文字＋シリーズ・感嘆'
    if re.match(r'^[【\[]', fl) and re.search(r'ニュース|NEWS', fl):
        return '【】AIニュース見出し'
    if re.match(r'^[【\[]', fl):
        return '【】タイトル型'
    if re.match(r'^(なぜ|どこ)', fl) or re.search(r'[？?]$', fl):
        return '問いかけ型'
    if re.match(r'^(AI|「AI)', fl):
        return 'AI〜主張・観察'
    if re.match(r'^私[がはも]', fl):
        return '一人称起点'
    if len(re.sub(r'https?://\S+', '', fl).strip()) < 20:
        return '短文報告・誘導型'
    return 'その他（主張・ストーリー型）'

data = defaultdict(list)
for t in tweets:
    imp = t['public_metrics']['impression_count']
    fl = first_line(t['text'])
    data[classify(fl)].append((imp, fl, t['text']))

results = sorted(
    [(sum(i for i,_,_ in v)/len(v), len(v), k, v) for k, v in data.items()],
    reverse=True
)
```

---

## STEP 5: 結果出力

以下のフォーマットで出力する（最大10パターン）：

```
## @<username> 投稿パターン分析（過去<N>日 / <総件数>件）

| 順位 | パターン | 平均IMP | 件数 | 最大IMP |
|---:|---|---:|---:|---:|
|  1 | 【】タイトル型 | 8,119 | 89 | 76,019 |
...

### 代表ツイート（各パターン上位2件）

**#1 【】タイトル型**（平均 8,119）
- [76,019] 【 文字のアニメーション100選 】 Webサイトに動きが欲しい…
- [63,648] 【 超簡単 】 広告生成プロンプトがサクッと作れる…

**#2 問いかけ型**（平均 12,016）
- [55,027] これが、動画生成!!!???
- [26,765] どう使っていますか？
...
```

代表ツイートは各パターンの **IMP上位2件** を表示する。本文は80字で切り詰める。

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

- X API v2 の取得上限は **最大3200件**。期間が長くても取得できる範囲での分析となる旨を出力冒頭に注記する
- API レート制限（Basic tier: 15分に15リクエスト）に対応するため、ページネーション時に `time.sleep(1)` を挟む
- Bearer token: `grep X_BEARER_TOKEN /root/xClaude/.env | cut -d= -f2-`
- `exclude=retweets,replies` で本人投稿のみを対象とする
