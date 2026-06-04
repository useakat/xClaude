---
title: reporter-monthly
description: X・note 運用の月報を作成し、docs/reports/monthly/ に保存する。スプレッドシートから月次集計値・note売上を取得し、日報・週報をもとに総評と翌月改善計画をAI生成する。Xクリエイター収益は 0円 をデフォルトで保存（実値判明後に手動更新）。
category: レポート生成
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

X・note 運用の月報を作成し、docs/reports/monthly/ に保存する。スプレッドシートから月次集計値・note売上を取得し、日報・週報をもとに総評と翌月改善計画をAI生成する。Xクリエイター収益は 0円 をデフォルトで保存（実値判明後に手動更新）。

## 詳細内容

あなたは X・note 運用の月報を自律的に作成するエージェントです。
**以下の STEP を順番に、自動的に実行してください。ユーザー入力を待たない。**

---

# STEP 1: 対象月の決定

引数（YYYY-MM 形式）があればその月を使用する。なければ直近完了月（先月）を使用する。

```bash
python3 -c "
from datetime import datetime, timedelta, timezone
import sys

JST = timezone(timedelta(hours=9))
args = sys.argv[1:]
if args:
    d = datetime.strptime(args[0], '%Y-%m').date().replace(day=1)
else:
    today = datetime.now(JST).date()
    d = (today.replace(day=1) - timedelta(days=1)).replace(day=1)

import calendar
last_day = calendar.monthrange(d.year, d.month)[1]
end = d.replace(day=last_day)

print(f'month_id={d.strftime(\"%Y-%m\")}')
print(f'month_label={d.strftime(\"%Y年%-m月\")}')
print(f'month_jp={d.month}月')
print(f'start_sheet={d.strftime(\"%Y/%m/%d\")}')
print(f'end_sheet={end.strftime(\"%Y/%m/%d\")}')
print(f'start_iso={d.strftime(\"%Y-%m-%d\")}')
print(f'end_iso={end.strftime(\"%Y-%m-%d\")}')
" -- "$1"
```

各変数を記憶する。

---

# STEP 2: 日次記録シートから月次データ取得

月初と月末の `総フォロワ数`・`総フォロー数`・`noteフォロワ数` を取得する。
月末の前日（前月末）の値も取得してフォロワー増減を計算する。

```bash
SPREADSHEET_ID="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
START_SHEET="[STEP1の start_sheet]"
END_SHEET="[STEP1の end_sheet]"

gws sheets spreadsheets values get \
  --params "{\"spreadsheetId\": \"${SPREADSHEET_ID}\", \"range\": \"日次記録!A:AB\"}" \
  2>/dev/null | python3 -c "
import json, sys
from datetime import datetime, timedelta

start_s = '${START_SHEET}'
end_s   = '${END_SHEET}'

d = json.load(sys.stdin)
rows = d.get('values', [])
header = rows[0] if rows else []

def idx(name):
    try: return header.index(name)
    except: return -1

def get_row(target):
    for row in rows[1:]:
        if row and row[0] == target:
            return row
    return None

def val(row, name, default=''):
    if not row: return default
    i = idx(name)
    if i < 0 or i >= len(row): return default
    return row[i].strip() if row[i] else default

# 月初の前日（前月末）を計算
start_dt = datetime.strptime(start_s, '%Y/%m/%d').date()
prev_day  = (start_dt - timedelta(days=1)).strftime('%Y/%m/%d')

prev_row  = get_row(prev_day)
end_row   = get_row(end_s)

# 月末が未記録の場合は最終記録行を使う
if not end_row:
    end_dt = datetime.strptime(end_s, '%Y/%m/%d').date()
    for row in reversed(rows[1:]):
        if not row: continue
        try:
            dt = datetime.strptime(row[0], '%Y/%m/%d').date()
            if dt.year == end_dt.year and dt.month == end_dt.month:
                end_row = row
                break
        except: continue

fw_end    = val(end_row,  '総フォロワ数')
fw_start  = val(prev_row, '総フォロワ数')
note_end  = val(end_row,  'noteフォロワ数')
note_start= val(prev_row, 'noteフォロワ数')

def diff(a, b):
    try: return str(int(a.replace(',','')) - int(b.replace(',','')))
    except: return ''

print(f'fw_end={fw_end}')
print(f'fw_start={fw_start}')
print(f'fw_diff={diff(fw_end, fw_start)}')
print(f'note_end={note_end}')
print(f'note_start={note_start}')
print(f'note_diff={diff(note_end, note_start)}')

# 当月・前月のポスト数合計
def sum_posts(y, m):
    total = 0
    for row in rows[1:]:
        if not row: continue
        try: dt = datetime.strptime(row[0], '%Y/%m/%d').date()
        except: continue
        if dt.year == y and dt.month == m:
            try: total += int(row[idx('ポスト数')] or 0)
            except: pass
    return total

target_dt = datetime.strptime(start_s, '%Y/%m/%d').date()
prev_dt   = (target_dt - timedelta(days=1))
posts_this = sum_posts(target_dt.year, target_dt.month)
posts_prev = sum_posts(prev_dt.year,   prev_dt.month)
print(f'posts_this={posts_this}')
print(f'posts_prev={posts_prev}')
"
```

取得した値を記憶する。

---

# STEP 3: note購入記録シートから当月売上を集計

```bash
SPREADSHEET_ID="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
START_SHEET="[STEP1の start_sheet]"
END_SHEET="[STEP1の end_sheet]"

gws sheets spreadsheets values get \
  --params "{\"spreadsheetId\": \"${SPREADSHEET_ID}\", \"range\": \"note購入記録!A:G\"}" \
  2>/dev/null | python3 -c "
import json, sys
from datetime import datetime

start_s = '${START_SHEET}'
end_s   = '${END_SHEET}'
start = datetime.strptime(start_s, '%Y/%m/%d').date()
end   = datetime.strptime(end_s,   '%Y/%m/%d').date()

d = json.load(sys.stdin)
rows = d.get('values', [])
header = rows[0] if rows else []

total = 0
details = []
for row in rows[1:]:
    if not row or len(row) < 6: continue
    try:
        dt = datetime.strptime(row[0], '%Y/%m/%d').date()
    except: continue
    if start <= dt <= end:
        try:
            price = int(row[5].replace(',',''))
            title = row[4] if len(row) > 4 else ''
            total += price
            details.append(f'{title}: {price}円')
        except: pass

print(f'note_sales={total}')
print(f'note_sales_fmt={total:,}')
for d in details:
    print(f'  - {d}')
"
```

`note_sales` を記憶する。

---

# STEP 4: 当月の日報・週報を読み込む

```bash
REPO_ROOT=$(git -C /root/xClaude rev-parse --show-toplevel)
START_ISO="[STEP1の start_iso]"
END_ISO="[STEP1の end_iso]"

python3 -c "
from datetime import datetime, timedelta
from pathlib import Path

start = datetime.strptime('${START_ISO}', '%Y-%m-%d').date()
end   = datetime.strptime('${END_ISO}',   '%Y-%m-%d').date()
repo  = Path('${REPO_ROOT}')

# 日報
daily_texts = []
d = start
while d <= end:
    f = repo / 'docs/reports/daily' / f'{d}.md'
    if f.exists():
        daily_texts.append(f.read_text())
    d += timedelta(days=1)

# 週報
weekly_texts = []
for f in sorted((repo / 'docs/reports/weekly').glob('????-W??.md')):
    text = f.read_text()
    # 週の月曜日を推定してフィルタ
    try:
        stem = f.stem  # e.g. 2026-W18
        year, wnum = int(stem.split('-W')[0]), int(stem.split('-W')[1])
        from datetime import date
        mon = date.fromisocalendar(year, wnum, 1)
        if start <= mon <= end:
            weekly_texts.append(text)
    except: pass

print('=== 日報 ===')
print('\n---\n'.join(daily_texts) if daily_texts else '(日報なし)')
print('\n=== 週報 ===')
print('\n---\n'.join(weekly_texts) if weekly_texts else '(週報なし)')
"
```

取得したテキストを記憶する。

---

# STEP 4.5: W001/W003 の過去3ヶ月推移集計

`/analyze-x-posts` スキルを以下のプロンプトで呼び出し、投稿タイプ別の月別トレンド表を生成する。

```
/analyze-x-posts W001（長文ストーリー）とW003（ワンポイント解説）について、過去3ヶ月（[前々月label]・[前月label]・[当月label]）の月別推移表を2つ（W001とW003で別々）作成してください。

列は「投稿数・IMP合計・IMP平均（IQRの1.5倍超を外れ値として除外）・フォロー増合計・フォロー増平均（IQR外れ値除外）」としてください。
※ 合計は外れ値込み、平均のみ外れ値除外。

【データソース】
① outputs シート（スプレッドシートID: 1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc）
  - 列A: 日時、列B: X投稿URL、列C: what_id（W001/W003等）
  - このシートで各URLの投稿タイプを特定してください。

② X投稿一覧シート（スプレッドシートID: 1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c）
  - IMP・フォロー増等のパフォーマンス指標を持っています。
  - 投稿URLで①と突合し、W001/W003の指標を取得してください。

【当月（[当月label]）の推計方法】
当月1日〜15日の投稿のみを使ってIMP平均・フォロー増平均を算出し、それに当月の総投稿数（[posts_this]本）を乗じてIMP合計・フォロー増合計の推計値を出してください。当月は表で「[当月label]（推計）」と明記してください。
```

返ってきた W001・W003 それぞれの推移表を記憶する（STEP 6 のコンテンツ生成の分析材料として使用）。

---

# STEP 5: 翌月マネタイズ計画ファイルの読み込み

STEP 1 の month_id から翌月を算出し、対応するマネタイズ計画ファイルを Read する。

```bash
python3 -c "
from datetime import datetime, timedelta
import sys

month_id = '[STEP1の month_id]'  # 例: 2026-05
d = datetime.strptime(month_id, '%Y-%m').date()
next_m = d.replace(day=28) + timedelta(days=4)  # 翌月の1日を確実に取得
next_m = next_m.replace(day=1)
print(f'next_month_file={next_m.strftime(\"%Y%m\")}_monetization.md')
print(f'next_month_label={next_m.strftime(\"%Y年%-m月\")}')
"
```

算出したファイル名で計画ファイルを Read する：

```
REPO_ROOT/docs/plans/[next_month_file]
```

ファイルが存在する場合、以下を抽出して記憶する：
- `## 目標` テーブル（note 月間収益 / X 月間IMP の数値）
- note の価格・月間本数（`## 2. note 計画` 等から「¥980」「月4本」等）
- X 投稿頻度（`## 1. X 投稿計画` 等から週本数・枠構成）
- 主要 KPI・施策（誘導モデル・計測指標等、次月改善の根拠になる情報）

**ファイルが存在しない場合**：「翌月のマネタイズ計画が未策定」と記憶し、STEP 6 の次月改善は方針レベルのみ記述する。

---

# STEP 6: 月報コンテンツの生成

STEP 4 で読み込んだ日報・週報の内容をもとに、以下を生成する。

## 文体ルール
- 1人称: 「僕」
- 箇条書き: 「・」
- 想定読者: コンサルグループ「AGARU」のメンバー（マネタイズコンサルタント視点）
- NG: 過激・否定的・攻撃的・不快・自慢（達成を素直に喜ぶのは適度にOK）

## 量・粒度のルール
- 総評: 2〜3文・150字程度（「足場を組み直す月」のようなまとめ語感は避け、率直に書く）。**前月比のポスト数（posts_prev→posts_this）を具体アンカーとして含めること**を推奨。構成例：(a) その月のテーマ → (b) 具体的にできたこと（ポスト数の前月比など） → (c) 次に向けた焦点。
- ▼良かったこと: 5〜6項目に統合（同じ事実を分割しない。例：複数の高インプ投稿は1項目にまとめる）
- ▼悪かったこと: 3〜4項目。「実行レベルの細部（時間管理・ツール不具合など）」ではなく「構造的・戦略的な問題」を優先
- ▼次月への改善: 3〜5項目。**STEP 5 で取得した計画ファイルの目標値・価格・本数・投稿頻度を具体数字として本文に明記する**（計画ファイルが存在する月のみ。ない月は方針レベルに留める）

## 戦略転換の判定（最重要）
次月への改善を生成する前に、当月実績から以下を判定する：
1. 前月「次月への改善」で挙げた施策はワークしたか？（数値が動いたか）
2. ワークしていない施策があれば、踏襲ではなく「やめる／路線を変える」を選択肢に入れる
3. 当月初めて顕在化した構造的問題（例：マネタイズ計画の不在）があれば、それを最優先タスクにする

「前月の改善案を継続する」前提で書かない。実績を見て路線を再評価してから書く。

## ◆ 1か月を振り返って総評
その月を一言で表すナラティブな文（2〜3文）。数値の羅列ではなく、月の「意味」や「流れ」を語る。前月比ポスト数（posts_prev→posts_this）を具体アンカーとして含めることを推奨。

## ▼ 良かったこと、できたこと
- 数値で表れる達成（インプ・フォロワー・売上など）
- 数値に表れない収穫（気づき・学び・仕組み化・習慣化など）を両方含める
- STEP 4.5 で取得した W001/W003 推移表の数値（IMP変化・フォロー増）を根拠として活用する

## ▼ 悪かったこと、できなかったこと
- 事実ベースで淡々と書く。自己攻撃・言い訳なし
- STEP 4.5 の推移表でポスト数・IMP が伸びていない部分があれば構造的問題として記述する

## ▼ 次月への改善、やるべきこと
- STEP 5 で計画ファイルを読み込めた場合：`## 目標` の数値（note収益・X IMP）・note 価格と本数・X 投稿頻度を具体数字として明記する
- STEP 5 で計画ファイルがない場合：方針レベルのみ記述し「翌月のマネタイズ計画が未策定」と添える
- 来月の残り週数を意識した現実的な計画にする

---

# STEP 7: ファイル保存

以下のパスに月報ファイルを保存する：
`[REPO_ROOT]/docs/reports/monthly/[month_id].md`

## ファイルフォーマット

```markdown
---
title: 月報 [month_label]
---

## ＜[month_label]度結果＞

◆ フォロワー数
　・X: [fw_end]人（+[fw_diff]）
　・note: [note_end]人（+[note_diff]）

◆ マネタイズ
　・Xクリエイター収益: [x_revenue]円
　・note（有料記事）: [note_sales_fmt]円
　合計: [total]円

◆ 1か月を振り返って総評

[AI生成：総評]

▼ 良かったこと、できたこと

・[AI生成]

▼ 悪かったこと、できなかったこと

・[AI生成]

▼ 次月への改善、やるべきこと

・[AI生成：翌月計画ファイルの目標・価格・本数・投稿頻度に基づく具体数字＋方針。計画ファイルがない月は方針レベルのみ]
```

---

# STEP 8: インデックス更新

`docs/reports/monthly/index.md` の適切な位置に追記する（既存の場合はスキップ）：

```markdown
- [[month_label]]([month_id].md)
```

---

# STEP 9: Git コミット & GitHub MCP プッシュ

**9-1. ローカルコミット**

```bash
bash $(git -C /root/xClaude rev-parse --show-toplevel)/scripts/commit_and_sync.sh \
  "report(monthly): [month_label]の月報を追加"
```

**9-2. GitHub MCP で master にプッシュ**

`git diff HEAD~1 --name-only` で変更ファイル一覧を取得し、各ファイルを Read ツールで読み込む。その後 `mcp__github__push_files` ツールで master に直接プッシュする：

- owner: `useakat`
- repo: `xClaude`
- branch: `master`
- files: 変更ファイルの path と content のリスト
- message: `report(monthly): [month_label]の月報を追加`

---

# 完了報告

```
✅ 月報作成完了: [month_label]
   X フォロワー: [fw_start] → [fw_end]（+[fw_diff]）
   note売上: [note_sales_fmt]円
   Xクリエイター収益: [x_revenue]円（取得不可の場合は 0円。実値が判明後に手動更新）
   保存先: docs/reports/monthly/[month_id].md
```

保存したファイルを Read ツールで読み込み、内容をそのまま表示する。
