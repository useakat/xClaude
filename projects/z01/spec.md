# Production Spec — X 短文投稿（Z01）

## Media (生成する媒体)
- X 投稿テキスト（**140 字テキストのみ**。画像なし）

## Input (読み込むファイル)
- `../../plan.md`
- `../../brand.md`（共通ブランド定義）
- `plan.md`（本プロジェクトの目的・ターゲット）
- `brand.md`（本プロジェクトの表現ルール）
- Google Sheets SS1（spreadsheetId: `1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM`）の 4 シート — ネタプール
  - `onePointNeta` / `noteNeta` / `newsTopics` / `thoughts`

## Output (保存先)
- **Gmail 下書き**（投稿は行わず、下書きを作成するだけ）。
- ローカル成果物は残さない（一時ファイル `/tmp/xshort_mail.txt` のみ）。

## Format
- **テキスト**: 常体（だ／のだ調）、3 パート構成（フック→核心→締め。`brand.md` 参照）。
- **文字数**: 厳密に **135〜140 字**（改行・空白を含む総文字数）。
- ハッシュタグ・絵文字・CTA・画像なし。

## Naming

### Gmail 下書き
- 件名: `【X短文投稿】{トピック要約 10〜15 字} YYYYMMDD HH:MM:SS`
- 本文フォーマット:

```
ソース: {ソースシート}[{ネタ番号}]

[投稿文]

{生成した投稿文}

[/投稿文]
```

## Rules

### 制作フロー（この spec.md を正として実行する。`/writer-xshort` スキルは廃止予定で使わない）

#### STEP 1: 4 シートのデータ取得
SS1 から以下 4 シートを取得する（ヘッダー行を除く全行が対象。ステータスによるフィルタは行わない）:

```
sheets_get_values(spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM", range="onePointNeta!A:K")
sheets_get_values(spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM", range="noteNeta!A:G")
sheets_get_values(spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM", range="newsTopics!A:G")
sheets_get_values(spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM", range="thoughts!A:C")
```

各シートから使用する列:

| シート       | ID/No 列 | 使用する内容列                      |
|-------------|----------|-------------------------------------|
| onePointNeta | A(No)    | B(テーマ), E(仕組みのポイント)      |
| noteNeta     | A(No)    | B(タイトル案), E(危機の内容)        |
| newsTopics   | A(No)    | C(タイトル), D(概要), E(ポイント)   |
| thoughts     | A(ID)    | B(内容)                             |

ヘッダー行（1 行目）を除いた全データ行を 1 つのプールとして把握する。

#### STEP 2: ランダム選択
4 シートの全データ行を 1 つのプールに集約し、python3 でランダムな 1 件を選ぶ:

```bash
python3 -c "import random, sys; n=int(sys.argv[1]); print(random.randint(0, n-1))" {全行数}
```

全行数 N =（onePointNeta 行数）+（noteNeta 行数）+（newsTopics 行数）+（thoughts 行数）。
取得したインデックスがどのシートの何行目かを特定し、以下を記憶する:
- **【ソースシート】**: シート名（例: `onePointNeta`）
- **【ネタ番号】**: 選択行の A 列値（No または ID）
- **【ネタ内容】**: 選択行の主要テキスト（上表の「使用する内容列」を結合）

#### STEP 3: 135〜140 字の投稿文生成
`brand.md`（Writing Rules / Do Not）に準拠した X 投稿文を生成する。
- 構成: フック → 核心 → 締めの 3 パート。
- ソース別の書き方は `brand.md`「ソース別の書き方」に従う。

生成後、python3 で実文字数を計測する:

```bash
python3 -c "text='''（生成した投稿文）'''; print(len(text))"
```

135〜140 字の範囲外なら再生成する（最大 2 回。2 回試みても外れる場合は最も近いものを採用）。

#### STEP 4: Gmail 下書き作成
1. 本文を `/tmp/xshort_mail.txt` に Write する（Naming の本文フォーマット）。
2. 件名用トピック要約を生成する（投稿文の核心キーワードを名詞句で **10〜15 字以内**。例:「スマホGPS 相対性理論」）。
3. JST 日時を取得する: `TZ=Asia/Tokyo date '+%Y%m%d %H:%M:%S'`
4. Gmail 下書きを作成する:

```bash
bash scripts/create_gmail_draft.sh \
  --to useakat@gmail.com \
  --subject "【X短文投稿】{トピック要約} {YYYYMMDD HH:MM:SS}" \
  --body-file /tmp/xshort_mail.txt
```

成功判定は `✓ 下書き作成完了` の出力で行う。

#### STEP 5: 完了報告
以下を出力して終了する:

```
✅ ネタ選択完了（ソース: {ソースシート}[{ネタ番号}] / {ネタ概要30字以内}）
✅ 投稿文生成完了（{実文字数}字）
✅ Gmail 下書き作成完了（件名: 【X短文投稿】{トピック要約} {YYYYMMDD HH:MM:SS}）

---
【生成した投稿文】

{投稿文本文}
```

### その他
- **投稿は一切行わない。Gmail 下書きを作成するだけ。**（X 投稿は cron 定時実行のみ）
- 画像は生成・添付しない（テキストのみ）。
- ネタは「未使用」フィルタをかけず全行プールから選ぶ（高頻度運用のため在庫を絞らない）。
- 反応の良かったネタは plan.md の方針に従い W001 / W002 / W003 へ昇格候補とする（昇格判断は本フロー外で実施）。

## Verification
- テキスト字数が **135〜140 字**に収まっている（`python3 -c "print(len('''…'''))"` で確認）。
- `brand.md`（Writing Rules / Do Not）と矛盾しない。
- `plan.md` の目的（反応観測・高頻度・テキストのみ）に沿う。
- Gmail 下書きの本文が `[投稿文]`〜`[/投稿文]` の開き・閉じ両タグで囲まれている。
- ハッシュタグ・絵文字・CTA・画像が含まれていない。
