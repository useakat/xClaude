---
title: reporter-weekly
description: X・note 運用の週報を作成し、docs/reports/weekly/ に保存する。スプレッドシートから週次集計値を取得し、日報をもとに「やったこと」「来週タスク」をAI生成する。
category: レポート生成
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

X・note 運用の週報を作成し、docs/reports/weekly/ に保存する。スプレッドシートから週次集計値を取得し、日報をもとに「やったこと」「来週タスク」をAI生成する。

## 詳細内容

あなたは X・note 運用の週報を自律的に作成するエージェントです。
**以下の STEP を順番に、自動的に実行してください。ユーザー入力を待たない。**

---

# STEP 1: 対象週の決定

引数があればその週の月曜日の日付（YYYY-MM-DD）として解釈する。なければ直近完了週（先週月〜日）を使用する。

```bash
python3 -c "
from datetime import datetime, timedelta, timezone
import sys

JST = timezone(timedelta(hours=9))
args = sys.argv[1:]
if args:
    base = datetime.strptime(args[0], '%Y-%m-%d').date()
    monday = base - timedelta(days=base.weekday())
else:
    today = datetime.now(JST).date()
    # 直近完了週の月曜（今週月曜の7日前）
    monday = today - timedelta(days=today.weekday() + 7)

sunday = monday + timedelta(days=6)
iso_week = monday.isocalendar()[1]
year = monday.year

print(f'monday={monday.strftime(\"%Y-%m-%d\")}')
print(f'sunday={sunday.strftime(\"%Y-%m-%d\")}')
print(f'monday_sheet={monday.strftime(\"%Y/%m/%d\")}')
print(f'sunday_sheet={sunday.strftime(\"%Y/%m/%d\")}')
print(f'week_id={year}-W{iso_week:02d}')
print(f'week_label={monday.strftime(\"%-m月%-d日\")}週')
print(f'prev_sunday_sheet={(monday - timedelta(days=1)).strftime(\"%Y/%m/%d\")}')
" -- "$1"
```

各変数を記憶する。

---

# STEP 2: 日次記録シートから週集計データ取得

日曜日の行に `週間インプ`・`noteフォロワ数` が集計される。
月曜日の前日（前週日曜）と当週日曜の `総フォロワ数`・`総フォロー数` の差分でフォロワー増減を計算する。

```bash
SPREADSHEET_ID="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
MONDAY_SHEET="[STEP1の monday_sheet]"
SUNDAY_SHEET="[STEP1の sunday_sheet]"
PREV_SUNDAY_SHEET="[STEP1の prev_sunday_sheet]"

gws sheets spreadsheets values get \
  --params "{\"spreadsheetId\": \"${SPREADSHEET_ID}\", \"range\": \"日次記録!A:AB\"}" \
  2>/dev/null | python3 -c "
import json, sys

monday_s  = '${MONDAY_SHEET}'
sunday_s  = '${SUNDAY_SHEET}'
prev_sun_s= '${PREV_SUNDAY_SHEET}'

d = json.load(sys.stdin)
rows = d.get('values', [])
header = rows[0] if rows else []

def idx(name):
    try: return header.index(name)
    except: return -1

def get_row(target_date):
    for row in rows[1:]:
        if row and row[0] == target_date:
            return row
    return None

def val(row, name, default=''):
    if not row: return default
    i = idx(name)
    if i < 0 or i >= len(row): return default
    return row[i].strip() if row[i] else default

prev_row   = get_row(prev_sun_s)
sunday_row = get_row(sunday_s)

# フォロワー数（当週日曜 → 前週日曜の差分）
fw_end    = val(sunday_row, '総フォロワ数')
fw_start  = val(prev_row,   '総フォロワ数')
fo_end    = val(sunday_row, '総フォロー数')
fo_start  = val(prev_row,   '総フォロー数')
note_end  = val(sunday_row, 'noteフォロワ数')
note_start= val(prev_row,   'noteフォロワ数')
weekly_imp= val(sunday_row, '週間インプ')

def diff(a, b):
    try: return str(int(a.replace(',','')) - int(b.replace(',','')))
    except: return ''

print(f'fw_end={fw_end}')
print(f'fw_start={fw_start}')
print(f'fw_diff={diff(fw_end, fw_start)}')
print(f'fo_end={fo_end}')
print(f'fo_start={fo_start}')
print(f'fo_diff={diff(fo_end, fo_start)}')
print(f'note_end={note_end}')
print(f'note_start={note_start}')
print(f'note_diff={diff(note_end, note_start)}')
print(f'weekly_imp={weekly_imp}')
"
```

取得した値を記憶する。

週内の合計投稿数・引用数も取得する：

```bash
SPREADSHEET_ID="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c"
MONDAY_SHEET="[STEP1の monday_sheet]"
SUNDAY_SHEET="[STEP1の sunday_sheet]"

gws sheets spreadsheets values get \
  --params "{\"spreadsheetId\": \"${SPREADSHEET_ID}\", \"range\": \"日次記録!A:F\"}" \
  2>/dev/null | python3 -c "
import json, sys
from datetime import datetime, timedelta

monday_s = '${MONDAY_SHEET}'
sunday_s = '${SUNDAY_SHEET}'
mon = datetime.strptime(monday_s, '%Y/%m/%d').date()
sun = datetime.strptime(sunday_s, '%Y/%m/%d').date()

d = json.load(sys.stdin)
rows = d.get('values', [])
header = rows[0] if rows else []

def idx(name):
    try: return header.index(name)
    except: return -1

total_posts = 0
total_quotes = 0
for row in rows[1:]:
    if not row: continue
    try:
        dt = datetime.strptime(row[0], '%Y/%m/%d').date()
    except: continue
    if mon <= dt <= sun:
        try: total_posts  += int(row[idx('ポスト数')] or 0)
        except: pass
        try: total_quotes += int(row[idx('引用数')] or 0)
        except: pass

print(f'total_posts={total_posts}')
print(f'total_quotes={total_quotes}')
"
```

---

# STEP 3: 当週の日報を読み込む

`docs/reports/daily/` から当週（月〜日）の日報ファイルを読み込む。

```bash
REPO_ROOT=$(git -C /root/xClaude rev-parse --show-toplevel)
MONDAY="[STEP1の monday]"
SUNDAY="[STEP1の sunday]"

python3 -c "
from datetime import datetime, timedelta
from pathlib import Path

monday = datetime.strptime('${MONDAY}', '%Y-%m-%d').date()
sunday = datetime.strptime('${SUNDAY}', '%Y-%m-%d').date()
daily_dir = Path('${REPO_ROOT}/docs/reports/daily')

contents = []
d = monday
while d <= sunday:
    f = daily_dir / f'{d}.md'
    if f.exists():
        contents.append(f.read_text())
    d += timedelta(days=1)

print('\n---\n'.join(contents) if contents else '(日報ファイルなし)')
"
```

取得した日報テキストを記憶する。

---

# STEP 4: 前月報から「次月への改善」を読み込む

```bash
REPO_ROOT=$(git -C /root/xClaude rev-parse --show-toplevel)
MONDAY="[STEP1の monday]"

python3 -c "
from datetime import datetime
from pathlib import Path

monday = datetime.strptime('${MONDAY}', '%Y-%m-%d').date()
monthly_dir = Path('${REPO_ROOT}/docs/reports/monthly')

# 当月または前月の月報を探す（直近のものを優先）
candidates = sorted(monthly_dir.glob('????-??.md'), reverse=True)
for f in candidates:
    try:
        ym = datetime.strptime(f.stem, '%Y-%m').date().replace(day=1)
        if ym <= monday.replace(day=1):
            text = f.read_text()
            # 「次月への改善」セクションを抽出
            if '次月への改善' in text:
                start = text.index('次月への改善')
                print(text[start:start+1000])
            else:
                print('(次月への改善セクションなし)')
            break
    except:
        continue
else:
    print('(月報ファイルなし)')
"
```

---

# STEP 5: 週報コンテンツの生成

STEP 3 の日報内容と STEP 4 の「次月への改善」をもとに、以下を生成する。

## ④ 今週やったこと・達成したこと

- 日報の各セクション（note / X / threads / 特記事項）から重複なく箇条書きで整理
  - 2026-07-25 以降の日報は媒体別4セクション構成。それ以前は「④ 特記事項」に全てまとまった旧形式で、どちらも混在しうる
- **投稿はプロジェクト（ワンポイント解説・ストーリー長文・短文投稿など）ごとにまとめる**
  - **見出し行に本数とインプ合計を書く**（threads は「インプ」ではなく「views」で表記する）
  - 例: 「・ワンポイント解説 2本（合計 3,500インプ）\n　・「タイトル」（インプXX・いいねXX）\n　・「タイトル」（インプXX・いいねXX）」
  - threads の例: 「・ワンポイント解説 3本（合計 14,248views）」
  - 同じプロジェクトの投稿が1本だけの場合も同様の形式でまとめる
  - 合計は日報に記録された各投稿の数値を単純合算する。日報が存在しない日の投稿は数値不明として合計に含めず、その旨を明記する
- 投稿以外（ツール整備・フロー改善など）は個別の箇条書きで続ける
- 1人称「僕」、箇条書き「・」
- NG: 過激・否定的・攻撃的・自慢（達成を素直に喜ぶのは適度にOK）

## ⑤ 来週やるべきタスク

- 前月報の「次月への改善」をもとに書く
- 行数は問わないが、**各行に来週やるべき行動を1つずつ簡潔に書く**
- 行動レベルで書く（「1日2投稿」「note記事公開」など）
- 月報がない場合は日報から推論して書く

---

# STEP 6: ファイル保存

以下のパスに週報ファイルを保存する：
`[REPO_ROOT]/docs/reports/weekly/[week_id].md`

## ファイルフォーマット

```markdown
---
title: 週報 [week_label]
---

## 【週報　[week_label]】

① フォロワー数
　・X: [fw_start]名 → [fw_end]名（+[fw_diff]）
　・note: [note_start]名 → [note_end]名（+[note_diff]）

② フォロー数
　・X: [fo_start]名 → [fo_end]名（+[fo_diff]）

③ オリジナルポスト数：[total_posts]件（目標: 14件）

④ インプレッション：[weekly_imp]（目標: 50万）

⑤ 今週やったこと・達成したこと

・[AI生成]

⑥ 来週やるべきタスク：

・[AI生成]
```

---

# STEP 7: インデックス更新

`docs/reports/weekly/index.md` の末尾（または適切な位置）に追記する（既存の場合はスキップ）：

```markdown
- [[week_id]]([week_id].md)
```

---

# STEP 8: Git コミット & GitHub MCP プッシュ

**8-1. ローカルコミット**

```bash
bash $(git -C /root/xClaude rev-parse --show-toplevel)/scripts/commit_and_sync.sh \
  "report(weekly): [week_label]の週報を追加"
```

**8-2. GitHub MCP で master にプッシュ**

`git diff HEAD~1 --name-only` で変更ファイル一覧を取得し、各ファイルを Read ツールで読み込む。その後 `mcp__github__push_files` ツールで master に直接プッシュする：

- owner: `useakat`
- repo: `xClaude`
- branch: `master`
- files: 変更ファイルの path と content のリスト
- message: `report(weekly): [week_label]の週報を追加`

---

# 完了報告

```
✅ 週報作成完了: [week_label]
   X フォロワー: [fw_start] → [fw_end]（+[fw_diff]）
   週間インプ: [weekly_imp]
   保存先: docs/reports/weekly/[week_id].md
```

保存したファイルを Read ツールで読み込み、内容をそのまま表示する。
