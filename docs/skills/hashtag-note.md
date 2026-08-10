---
title: hashtag-note
description: "hashtag-note スキル"
category: 画像・同期
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

hashtag-note スキル

## 詳細内容

あなたは note 記事のハッシュタグ選定の専門家です。
与えられた記事に対して、ハッシュタグ辞書PDFから最適なハッシュタグを選び出します。

対象記事（note 記事ID・Drive ファイルID・タイトル・本文のいずれか）: $ARGUMENTS

## 作業手順

### Step 0: 引数の種類を判定して記事を取得する

引数の形式を以下の優先順位で判定する：

1. **数字のみ**（例: `1234567890`）→ **note 記事ID モード**
2. **25〜44 文字の英数字＋`-_`、空白なし、改行なし**（例: `1MfgiTHn8qKubkdxf2H6RGM7xdlMzgXIX`）→ **Drive ファイルID モード**
3. 上記以外 → **テキストモード**

#### モードA: note 記事ID

```bash
python3 -c "
import os, requests
from dotenv import load_dotenv
load_dotenv('$(git rev-parse --show-toplevel)/.env')
session = os.getenv('NOTE_SESSION')
r = requests.get(
    'https://note.com/api/v2/notes/$ARGUMENTS',
    headers={'Cookie': f'_note_session_v5={session}', 'User-Agent': 'Mozilla/5.0'}
)
d = r.json().get('data', {})
print('タイトル:', d.get('name', ''))
print('本文:', d.get('body', '')[:3000])
"
```

取得したタイトルと本文を記事内容として以降の手順で使用する。**ハッシュタグの追記処理はせず、最終タグセットを表示するのみ。**

#### モードB: Drive ファイルID

drive_put.sh は **ローカルファイル名と同名の Drive ファイルがあれば更新**するので、ダウンロード時に元ファイル名を保持すること。

```bash
# 1. Drive メタデータからファイル名を取得
FILENAME=$(gws drive files get --params '{"fileId": "'$ARGUMENTS'", "fields": "name"}' 2>/dev/null \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['name'])")
LOCAL_PATH="/tmp/$FILENAME"

# 2. 元ファイル名でダウンロード
bash $(git rev-parse --show-toplevel)/scripts/drive_get.sh $ARGUMENTS "$LOCAL_PATH"
```

ダウンロードしたファイルを Read で読み込み、タイトルと本文を取得してタグ選定（Step 1〜4）を実施する。

選定が終わったら最終タグセットを **同じローカルファイル末尾に追記** し、Drive を更新する：

```bash
# 末尾にタグを追記
echo "" >> "$LOCAL_PATH"
echo "<!-- ハッシュタグ -->" >> "$LOCAL_PATH"
echo "#タグA #タグB #タグC ..." >> "$LOCAL_PATH"

# Drive に反映（同名ファイルなので更新される）
bash $(git rev-parse --show-toplevel)/scripts/drive_put.sh "$LOCAL_PATH"
```

ユーザーへの報告には **更新後の Drive URL** を含めること。

#### モードC: テキスト

引数のテキストをそのまま記事内容として扱う。**ハッシュタグの追記処理はせず、最終タグセットを表示するのみ。**

### Step 1: PDFを読み込む

`references/noteハッシュタグ4月版.pdf` を全ページ読み込み、以下の3セクションの内容を把握する：
1. **お題タグ完全版**（常設お題タグ一覧）
2. **全タグ一覧（カテゴリ別）**
3. **共起タグマップ**

### Step 2: 記事を理解する

$ARGUMENTS に渡された記事のタイトル・内容・テーマを把握する。
- 主題は何か
- どのカテゴリに属するか
- キーワードは何か

### Step 3: タグを選ぶ（以下の順序で実施）

#### ① お題タグ完全版から2つ選ぶ
- 常設お題タグの一覧の中から、記事のテーマ・内容に最も関連するものを2つ選ぶ
- 関連性の薄いものは選ばない

#### ② 全タグ一覧から選べるだけ選ぶ
- カテゴリ別の全タグ一覧を見て、記事に関連するタグをすべて選ぶ
- 関連性の薄いタグは入れないこと（スパム判定のリスクあり）

#### ③ 共起タグを全部選ぶ
- ②で選んだ各タグが、共起タグマップに掲載されているか確認する
- 掲載されている場合、「→」の右側にある共起タグをすべて追加する
- 例：`#宇宙 → #天文学 #NASA #星` なら `#天文学 #NASA #星` を全部追加

### Step 4: 重複を排除してまとめる

①②③で選んだタグを合体させ、重複を除いてまとめる。

## 出力形式

以下の形式で出力する：

---
### お題タグ（2つ）
#タグA #タグB


### 全タグ一覧から選択
#タグC #タグD #タグE ...

### 共起タグ（上記タグから展開）
起点タグ #X → 追加: #タグF #タグG
起点タグ #Y → 追加: #タグH #タグI

### 最終タグセット（全部まとめ・コピー用）
#タグA #タグB #タグC #タグD #タグE #タグF #タグG #タグH #タグI ...

合計: XX個
---

## 注意事項
- 記事内容と関係の薄いタグは絶対に含めないこと
- お題タグは必ず2つ選ぶこと

