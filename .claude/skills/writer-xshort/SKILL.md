---
name: writer-xshort
description: 4シート（onePointNeta/noteNeta/newsTopics/thoughts）からランダムに1件ネタを選び、135-140文字のX投稿文を作成してGmail下書きを作成する。ユーザー確認なし全自動。
tools: Bash, mcp__mcp-gsheets__sheets_get_values
---

4シートからランダムにネタを1件選び、135-140文字のX投稿文を生成してGmail下書きを作成する。**全STEPを自動で実行する。ユーザーの確認・承認は不要。**

---

# STEP 1: 4シートのデータ取得

SS1（`1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM`）から以下4シートを取得する（ヘッダー行を除く全行が対象。ステータスによるフィルタは行わない）：

```
sheets_get_values(spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM", range="onePointNeta!A:K")
sheets_get_values(spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM", range="noteNeta!A:G")
sheets_get_values(spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM", range="newsTopics!A:G")
sheets_get_values(spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM", range="thoughts!A:C")
```

各シートから取得する主要列：

| シート       | ID/No 列  | 使用する内容列                              |
|-------------|-----------|---------------------------------------------|
| onePointNeta | A(No)     | B(テーマ), E(仕組みのポイント)              |
| noteNeta     | A(No)     | B(タイトル案), E(危機の内容)                |
| newsTopics   | A(No)     | C(タイトル), D(概要), E(ポイント)           |
| thoughts     | A(ID)     | B(内容)                                     |

ヘッダー行（1行目）を除いた全データ行をプールとして把握する。

---

# STEP 2: ランダム選択

4シートの全データ行を1つのプールに集約し、python3 でランダムな1件を選択する：

```bash
python3 -c "import random; import sys; n=int(sys.argv[1]); print(random.randint(0, n-1))" {全行数}
```

全行数 N = （onePointNeta の行数）+（noteNeta の行数）+（newsTopics の行数）+（thoughts の行数）

取得したランダムインデックスに対応する行がどのシートの何行目かを特定し、以下を記憶する：

- **【ソースシート】**: シート名（例: `onePointNeta`）
- **【ネタ番号】**: 選択行の A列値（No または ID）
- **【ネタ内容】**: 選択行の主要テキスト（上表の「使用する内容列」を結合したもの）

---

# STEP 3: 135-140文字の投稿文生成

`brand.md` の共通ルールに準拠した 135-140文字のX投稿文を生成する。

## 文体ルール（短文専用）

- **文字数**: 厳密に **135-140字**（改行・空白を含む総文字数）
- **構成**（3パート）:
  1. **フック**（1-2文）: 常識を裏切る/驚かせる事実・視点。「実は〜」「〇〇は△△だ」形式推奨
  2. **核心**（1-2文）: 仕組みや背景をコンパクトに。数値・固有名詞を具体的に
  3. **締め**（1文）: 日常接続または詩的余韻。感嘆だけで終わらない
- **口調**: 言い切り調（「〜だ」「〜である」）。感嘆符・です体は使わない
- **NG**: ハッシュタグ、CTA（「フォローしてね」等）、「——」ダッシュ2連、曖昧な表現

## ソース別の書き方

- **onePointNeta**: テーマ・仕組みポイントを使い、日常の物・感覚を入り口にする
- **noteNeta**: 人物名・危機・逆転のドラマを圧縮して語る。タイトルをそのまま使わない
- **newsTopics**: 概要・ポイントから「今」の驚きや発見を届ける
- **thoughts**: 内容そのままではなく、宇宙・物理の文脈に接続・昇華した投稿にする

## 文字数チェック

生成後、python3 で実文字数を計測する：

```bash
python3 -c "text='''（生成した投稿文）'''; print(len(text))"
```

135-140字の範囲外なら再生成する（最大2回。2回試みても外れる場合は最も近いものを採用）。

---

# STEP 4: Gmail 下書き作成

## 4-1: 本文ファイル作成

以下の形式で一時ファイル `/tmp/xshort_mail.txt` に Write する：

```
ソース: {ソースシート}[{ネタ番号}]

[投稿文]

{生成した投稿文}

[/投稿文]
```

## 4-2: 件名用トピック要約を生成

生成した投稿文の核心キーワードを名詞句で **10-15字以内** にまとめる（例:「スマホGPS 相対性理論」「はやぶさ エンジン復活」）。

## 4-3: JST 日時を取得

```bash
TZ=Asia/Tokyo date '+%Y%m%d %H:%M:%S'
```

## 4-4: Gmail 下書き作成

```bash
bash scripts/create_gmail_draft.sh \
  --to useakat@gmail.com \
  --subject "【X短文投稿】{トピック要約} {YYYYMMDD HH:MM:SS}" \
  --body-file /tmp/xshort_mail.txt
```

成功判定は `✓ 下書き作成完了` の出力で行う。

---

# STEP 5: 完了報告

以下を出力して終了する：

```
✅ ネタ選択完了（ソース: {ソースシート}[{ネタ番号}] / {ネタ概要30字以内}）
✅ 投稿文生成完了（{実文字数}字）
✅ Gmail 下書き作成完了（件名: 【X短文投稿】{トピック要約} {YYYYMMDD HH:MM:SS}）

---
【生成した投稿文】

{投稿文本文}
```
