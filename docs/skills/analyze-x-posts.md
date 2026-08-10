---
title: analyze-x-posts
description: "analyze-x-posts スキル"
category: リサーチ・分析
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

analyze-x-posts スキル

## 詳細内容

# analyze-x-posts

X投稿一覧シートのデータを分析してユーザーの質問に答えるスキル。
レポート作成を指示された場合は、ローカル保存のみ行う。

ユーザーの依頼: $ARGUMENTS

---

## データソース

| 項目 | 値 |
|---|---|
| スプレッドシートID | `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c` |
| シート名 | `X投稿一覧` |
| Drive レポートフォルダID | `1BkOTTY7wdmdNcFExsjTS75s5sfEzqPmB` |
| ローカル保存先 | `outputs/reports/YYYYMMDD_<タイトル>.md` |

### 主要カラム一覧

| インデックス | カラム名 | 備考 |
|---|---|---|
| 0 | 投稿日時 | |
| 1 | ツイート本文 | |
| 2 | ツイート種類 | 通常ツイート / リプライ 等 |
| 3 | 文字数 | |
| 4 | ハッシュタグ | |
| 5 | 画像枚数 | |
| 8 | インプレッション | カンマ区切り文字列に注意 |
| 9 | いいね | |
| 10 | リツイート | |
| 11 | リプライ | |
| 12 | ブックマーク | |
| 13 | エンゲージメント | |
| 14 | プロフアクセス | |
| 15 | エンゲ率 | 小数（0.05 = 5%） |
| 16 | いいね率 | 同上 |
| 17 | リツイート率 | 同上 |
| 18 | プロフ率 | 同上 |
| 19 | ブクマ率 | 同上 |
| 24 | 目的 | |
| 23 | ツイートURL | |

---

## 手順

### STEP 1: データ取得

```bash
gws sheets spreadsheets values get \
  --params '{"spreadsheetId": "1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c", "range": "X投稿一覧"}' \
  2>/dev/null > /tmp/xpost_data.json
```

### STEP 2: ユーザー依頼を判断する

依頼の種類に応じて対応を分ける：

| 依頼の種類 | 対応 |
|---|---|
| 単発の質問・分析（「〜を教えて」「〜はどう？」「〜を出して」） | STEP 3 → チャット回答のみ |
| レポート作成（「レポートにして」「まとめて」「保存して」） | STEP 3 → STEP 4 |

### STEP 3: 分析実行

#### データ読み込みのひな型（Python）

```python
import json, numpy as np

with open('/tmp/xpost_data.json') as f:
    d = json.load(f)
rows = d.get('values', [])
header = rows[0]
data_rows = rows[1:]

def to_float(s):
    """カンマ・%を除去して float に変換。失敗したら None"""
    try:
        return float(str(s).replace(',', '').replace('%', '').strip())
    except:
        return None

def to_pct(s):
    """率系カラム（小数 or %）を % に統一"""
    v = to_float(s)
    if v is None:
        return None
    return v * 100 if v <= 1.0 else v
```

#### 分析メニュー（依頼に応じて選択・組み合わせる）

**① 基本統計（分位・平均・最大など）**
```python
import numpy as np
arr = np.array([v for v in values if v is not None])
stats = {
    'n': len(arr),
    'mean': arr.mean(),
    'median': np.median(arr),
    'p25': np.percentile(arr, 25),
    'p75': np.percentile(arr, 75),
    'max': arr.max(),
    'min': arr.min(),
}
```

**② ヒストグラム生成**
```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
rcParams['font.family'] = 'Noto Sans CJK JP'
rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(arr, bins=30, color='#4C9BE8', alpha=0.8, edgecolor='white')
ax.axvline(arr.mean(), color='red', linestyle='--', label=f'平均 {arr.mean():.2f}%')
ax.axvline(np.median(arr), color='navy', linestyle=':', label=f'中央値 {np.median(arr):.2f}%')
ax.legend()
plt.tight_layout()
plt.savefig('/tmp/xpost_chart.png', dpi=150, bbox_inches='tight', facecolor='white')
```

**③ カテゴリ別比較（ツイート種類・画像あり/なし・目的別など）**
```python
groups = {}
for row in data_rows:
    key = row[2] if len(row) > 2 else ''  # ツイート種類
    val = to_pct(row[15]) if len(row) > 15 else None  # エンゲ率
    if val is not None:
        groups.setdefault(key, []).append(val)

for k, vals in groups.items():
    arr = np.array(vals)
    print(f"{k}: n={len(arr)}, 中央値={np.median(arr):.2f}%, 平均={arr.mean():.2f}%")
```

**④ 時系列トレンド（月別・週別）**
```python
from datetime import datetime
monthly = {}
for row in data_rows:
    try:
        dt = datetime.strptime(row[0][:7], '%Y/%m')
        val = to_pct(row[15])
        if val is not None:
            monthly.setdefault(dt, []).append(val)
    except:
        pass

for dt in sorted(monthly):
    arr = np.array(monthly[dt])
    print(f"{dt.strftime('%Y-%m')}: 中央値={np.median(arr):.2f}%, n={len(arr)}")
```

**⑤ 上位 N 件の投稿抽出**
```python
scored = []
for row in data_rows:
    val = to_pct(row[15])  # エンゲ率
    if val is not None:
        scored.append((val, row))
scored.sort(reverse=True)
for val, row in scored[:10]:
    print(f"{val:.2f}%  {row[0]}  {row[1][:50]}...")
```

**⑥ 相関分析（文字数×エンゲ率 など）**
```python
xs, ys = [], []
for row in data_rows:
    x = to_float(row[3])   # 文字数
    y = to_pct(row[15])    # エンゲ率
    if x is not None and y is not None:
        xs.append(x); ys.append(y)
corr = np.corrcoef(xs, ys)[0, 1]
print(f"相関係数: {corr:.3f}")
```

### STEP 4: レポート作成（レポート依頼時のみ）

1. 分析結果をまとめた Markdown を作成する
2. ファイル名: `YYYYMMDD_<内容を表す短いタイトル>.md`（例: `20260502_x_posting_analysis.md`）
3. 保存先: `outputs/reports/`
4. レポートの構成例:

```markdown
# X 投稿パフォーマンス分析レポート — <タイトル>

**作成日**: YYYY-MM-DD
**対象**: <分析対象の説明>（n=XXX件）

---

## 1. サマリー
（主要な発見を箇条書きで3〜5点）

## 2. 詳細分析
（表・数値・グラフへの参照）

## 3. 考察・アクション
（What → So What → Now What の流れで）
```

---

## 出力ルール

- **単発分析**: チャット上で結果を表・箇条書きで簡潔に示す。前置きは最小限
- **レポート**: ローカル保存パスをチャットで報告して終了
- グラフを生成した場合はチャット上で Read ツールで表示し、内容を解説する
- 率系の値は必ず % 表記で統一する（0.05 → 5% と表示）
- n 数（有効データ件数）を必ず明示する

---

## 注意事項

- インプレッションはカンマ区切り文字列（例: `"6,901"`）なので `replace(',','')` して数値変換すること
- 率系カラム（エンゲ率など）は値が `<= 1.0` なら小数表記とみなし 100 倍して % に統一
- matplotlib は `matplotlib.use('Agg')` をインポート直後に呼ぶこと（ヘッドレス環境）

