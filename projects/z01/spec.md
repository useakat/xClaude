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
- 本文フォーマット（`[投稿文]`〜`[/投稿文]` は投稿テキストのみを囲む。cron 投稿フローの `extract_tag.py` がこのタグ間を抽出するため、候補類はタグの外に置く）:

```
ソース: {ソースシート}[{ネタ番号}]

[フォーカス候補]

{/writer-xpost のフォーカス3候補＋「## 決定」}

[/フォーカス候補]

[冒頭フック候補]

{/writer-xpost の冒頭フック型別候補＋「## 決定」}

[/冒頭フック候補]

[投稿文]

{生成した投稿文}

[/投稿文]
```

## Rules

### 制作フロー（この spec.md を正として実行する。`/writer-xshort` スキルは廃止予定で使わない）

#### STEP 1: ソースシートをランダムに決定
SS1 の 4 シート（`onePointNeta` / `noteNeta` / `newsTopics` / `thoughts`）から、**等確率で 1 シートをランダムに選ぶ**：

```bash
python3 -c "import random; print(random.choice(['onePointNeta','noteNeta','newsTopics','thoughts']))"
```

- シートを先に等確率で選ぶことで、行数の多いシート（noteNeta など）への偏りを避け、各シートが均等に選ばれるようにする。
- 選んだシート名を **【ソースシート】** として記憶する。

#### STEP 2: 選んだシートからランダムに 1 行を取得
1. 選んだシートのデータだけを取得する（ステータスによるフィルタは行わない）。範囲は次のとおり：

   | シート       | 取得範囲          | ID/No 列 | 使用する内容列                      |
   |-------------|-------------------|----------|-------------------------------------|
   | onePointNeta | `onePointNeta!A:K` | A(No)    | B(テーマ), E(仕組みのポイント)      |
   | noteNeta     | `noteNeta!A:G`     | A(No)    | B(タイトル案), E(危機の内容)        |
   | newsTopics   | `newsTopics!A:G`   | A(No)    | C(タイトル), D(概要), E(ポイント)   |
   | thoughts     | `thoughts!A:C`     | A(ID)    | B(内容)                             |

   ```
   sheets_get_values(spreadsheetId="1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM", range="{選んだシートの取得範囲}")
   ```

2. ヘッダー行（1 行目）を除いたデータ行数を数え、その範囲で **ランダムに 1 行**を選ぶ：

   ```bash
   python3 -c "import random, sys; n=int(sys.argv[1]); print(random.randint(0, n-1))" {データ行数}
   ```

3. 選んだ行について以下を記憶する：
   - **【ネタ番号】**: 選択行の A 列値（No または ID）
   - **【ネタ内容】**: 選択行の主要テキスト（上表の「使用する内容列」を結合）

#### STEP 3: 投稿文生成（`/writer-xpost` を使う）
投稿文の作成は `/writer-xpost` スキルに委ねる。STEP 2 で選んだネタをテーマとして、文字数範囲 135〜140 字を指定して呼び出す：

```
/writer-xpost
テーマ: {STEP 2 の【ネタ内容】}
文字数: 135〜140字
```

- `/writer-xpost` は本作業フォルダ（z01）の `spec.md`・`plan.md`・`brand.md` を読み込み、投稿文を作成する。
- `/writer-xpost` の出力（フォーカス候補・冒頭フック候補・投稿内容）のうち、**投稿内容** を投稿文として採用する。本フローでは draft への保存は不要（Gmail 下書きが成果物のため、保存はスキップしてよい）。

#### STEP 4: ファクトチェック（`/check-fact` を使う）
採用した投稿文を `/check-fact` でファクトチェックする（テキスト入力モード）：

```
/check-fact {STEP 3 で採用した投稿文}
```

- 明確な事実誤り（数値・固有名詞・年代・因果の誤り）があれば訂正を反映する。
- 訂正で字数が 135〜140 字から外れた場合は、`brand.md` の削る対象優先度に従って範囲内に収め直す。

#### STEP 5: ブランド適合チェック（`/check-brand` を使う）
ファクトチェック済みの投稿文を `/check-brand` でブランド適合チェックする：

```
/check-brand brand.md {ファクトチェック済みの投稿文}
```

- `brand.md` の採点基準で全項目が基準を満たすまで該当箇所を書き直す（採点ループ）。最後にトンマナ調整する。
- 事実は変えない。字数 135〜140 字を維持する。

#### STEP 6: Gmail 下書き作成
1. フォーカス候補、冒頭フック候補、本文を `/tmp/xshort_mail.txt` に Write する（Naming の本文フォーマット）。
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

#### STEP 7: 完了報告
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
- ネタは「未使用」フィルタをかけず、選んだシートの全データ行を対象に選ぶ（高頻度運用のため在庫を絞らない）。
- 反応の良かったネタは plan.md の方針に従い W001 / W002 / W003 へ昇格候補とする（昇格判断は本フロー外で実施）。

## Verification
- テキスト字数が **135〜140 字**に収まっている（`python3 -c "print(len('''…'''))"` で確認）。
- `/check-fact` を通過している（事実誤りが訂正済み）。
- `/check-brand` のブランド適合チェックを通過している（採点基準を満たす）。
- `brand.md`（Writing Rules / Do Not）と矛盾しない。
- `plan.md` の目的（反応観測・高頻度・テキストのみ）に沿う。
- Gmail 下書きの本文が `[投稿文]`〜`[/投稿文]` の開き・閉じ両タグで囲まれている。
- ハッシュタグ・絵文字・CTA・画像が含まれていない。
