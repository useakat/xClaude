---
name: writer-xpromo
description: W002 の公開済み note 記事をランダムに1本選び、140字の販促投稿（本文＋note 導線セルフリプ）を3案作ってよーんに選んでもらい、採用案を予約ファイル（`outputs/scheduled-posts/w007/`）にして push する（postcal が金曜 6:00 枠に自動登録。X への投稿は行わない）
tools: Bash, Read, Write, mcp__mcp-gsheets__sheets_get_values
---

W002（note 記事）の公開済み記事から 1 本を選び、その記事へ誘導する **140 字の X 販促投稿**を作る。
本文には note への誘導を書かず、**誘導はセルフリプ（1 文＋URL）に回す**。投稿は、予約ファイルを VPS の `postcal_import.py` が postcal に登録（**既定は金曜 6:00 枠**。埋まっていれば翌週の金曜）し、既存の 6 時枠 cron が what_id W007 として行う。

入力（`$ARGUMENTS`、任意）: W002 のフォルダ名（例 `2026-08-20_akatsuki`）。指定があればランダム選択を飛ばしてその記事を使う。

**予約ファイルは STEP 5 でよーんが採用案を確定した後に作る。選択を待たずに作らない。Gmail 下書きは作らない（2026-11-19 に予約ファイル方式へ変更）。**

---

# STEP 0: 前提ファイルの読み込み

以下を Read してから始める（CLAUDE.md の規則）：

- `brand.md`（人格・言葉遣い・共通 NG）
- `plan.md`（執念＝中身、驚き＝技法）
- `style/hook-patterns.md`（冒頭フックの型①〜⑤）

---

# STEP 1: 候補プールの作成

対象は `projects/w002/` 直下の `YYYY-MM-DD_<slug>/` フォルダのうち、**記事正本 `output/index.md` があり、note の公開 URL が分かるもの**。

```bash
cd $(git rev-parse --show-toplevel) && python3 - <<'PY'
import re, pathlib
root = pathlib.Path("projects/w002")
for d in sorted(root.iterdir()):
    if not re.match(r"\d{4}-\d{2}-\d{2}_", d.name): continue
    idx = d / "output" / "index.md"
    url = ""
    for f in (d / "note-record.md", d / "README.md"):
        if f.exists():
            m = re.search(r"https://note\.com/takaesu7431/n/n[0-9a-f]+", f.read_text(encoding="utf-8"))
            if m: url = m.group(0); break
    title = ""
    if idx.exists():
        title = idx.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
    print(f"{d.name} | {'index.md' if idx.exists() else '-'} | {url or '-'} | {title}")
PY
```

- URL がローカルで解決できないフォルダは、`note投稿一覧` シートでタイトル照合する：
  `sheets_get_values(spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c", range="note投稿一覧!B:C")`（B=記事URL、C=タイトル。`output/index.md` の H1 または `note-record.md` の `title:` と前方一致で突き合わせる）
- `output/index.md` が無いフォルダは**対象外**にし、完了報告に列挙する（遡及作成フォルダなど）。
- `output/index.md` はあるが URL がどこにも無いフォルダ（公開直後で `note投稿一覧` 未反映など）は**プールに残す**。その記事が選ばれたら STEP 2 で note の公開 URL をよーんに尋ね、返事を待ってから進む（勝手に URL を推測しない）。
- **直近の販促を避ける**: `sheets_get_values(spreadsheetId="1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc", range="outputs!A:H")` を取得し、F列（note_url）が候補の URL と一致する行（what_id は問わない。W001＝長文販促・W007＝本スキル）のうち、A列の日時が **14 日以内**のものがあればその記事を今回の抽選から外す。全記事が外れる場合はこの規則を無視して全記事を対象にし、その旨を報告する。
- **未投稿の予約も避ける**: `outputs/scheduled-posts/w007/*.md` の front-matter `note_url` が候補の URL と一致し、まだ投稿されていない（postcal の status が queued。迷ったら `post.usephys.net` で確認）ものがあれば、その記事も今回の抽選から外す（同じ記事の販促が重複して予約されるのを防ぐ）。

---

# STEP 2: 記事の選択

- `$ARGUMENTS` にフォルダ名があればそれを使う（プール外でも `output/index.md` と URL があれば可）。
- 無ければランダムに 1 本選ぶ：

```bash
python3 -c "import random,sys; print(random.choice(sys.argv[1:]))" {プールのフォルダ名を空白区切りで}
```

選んだフォルダを **【記事フォルダ】**、タイトルを **【記事タイトル】**、URL を **【note URL】** として記憶する。

---

# STEP 3: 記事と過去の販促の読み込み

1. **記事正本を全文 Read する**: `projects/w002/【記事フォルダ】/output/index.md`。事実・人物名・年月日・数値・装置の帰属・呼称はすべてここを正とする。**ここに無い事実・発言・心情を足さない**。
2. **分割設計ブリーフ**（あれば）: `projects/w002/【記事フォルダ】/draft/funnel-brief.md` の「note の売り（有料の引き）」「あえて出さない核」を読み、**何を見せて何を伏せるか**の参考にする。
3. **過去の販促投稿（重複回避）**:
   - STEP 1 で取得した `outputs` の行のうち F列＝【note URL】の行（W001・W007）から B列の投稿 URL を集め、tweet ID で `sheets_get_values(spreadsheetId="1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c", range="X投稿一覧!B:C")`（B=ポストURL、C=本文）を引いて本文を読む。
   - `outputs/scheduled-posts/w007/*.md` のうち `note_url` が【note URL】のもの（予約済み・投稿済みの確定稿）があれば、`## 投稿文` を読む。
   - `projects/w002/【記事フォルダ】/promo/*.md`（本スキルの過去出力。未投稿の案も含む）があれば読む。
   - 過去に使った **場面・切り口・フック型** を **【過去フォーカス】** として記憶する。無ければ「なし」。

---

# STEP 4: 3 案の作成

記事の中から**互いに別の場面**を 3 つ選び、それぞれ本文（140 字）とセルフリプ（1 文＋URL）を書く。

## 本文のルール

- **字数**: 改行・空白を含めて **135〜140 字**。必ず `python3 -c "print(len('''…'''))"` で実測する（1 字でも超えたら削る）。
- **構成**: ①冒頭フック 1 文（`style/hook-patterns.md` の①逆説・②知識提示・③場面描写を優先。読者の「当たり前」が覆る落差を必ず入れる）→ ②場面（年月日・固有名・数値を具体的に。主人公の探査機・人物は名前で呼び、初出で一言補足）→ ③締め（言い切り。疑問形で終わらない）。
- **本文に note への誘導を書かない**（「note に書きました」「続きは」「詳しくは」、URL、ハッシュタグはすべて禁止）。誘導はセルフリプだけ。
- **1 案に驚きは 1 つ**。記事の有料部分の核（funnel-brief の「note の売り」）は、1 案で 1 つまで。核心のオチ（最終結果の数値や決定的な種明かし）は伏せてよく、伏せた分はセルフリプの導入 1 文で「〜までを note に書いています」と回収する。
- **3 案は別の場面・別のフック型**にし、**【過去フォーカス】と重ならない**場面にする（同じ場面を同じ角度で使わない）。
- 事実の表現は記事のまま（数値を丸めない・言い換えで強めない）。人物の発言は記事に引用があるものだけ。
- `brand.md` の共通ルール・NG 表現に従う（ひらがなで開くのは接続詞・助詞のみ、「——」禁止、曖昧表現禁止、反応誘導禁止、転換語の乱用禁止）。1 人称・2 人称は基本的に無主語。

## セルフリプのルール

- **その案のフォーカスに合わせた導入 1 文**＋改行＋**【note URL】（生 URL）**。投稿時に `post_to_x.py` が `xpost.usephys.net` の転送リンクへ自動変換するので、URL は加工しない。
- 導入文は「〜を note に書いています。」の形を基本とし、本文で伏せたものを指す（例:「その20分28秒のブレーキと、そこまでの5年間を note に書いています。」）。長い宣伝文にしない。
- 過去の販促のセルフリプと同じ文面にしない。

## 提示前の自己点検（全案）

- [ ] 字数 135〜140（実測値を控える）
- [ ] 本文に note・URL・ハッシュタグ・反応誘導が無い
- [ ] 各事実が `output/index.md` のどの段落に基づくか手元で確認した（記事に無い事実が無い）
- [ ] 3 案の場面・フック型が互いに違い、【過去フォーカス】と重ならない
- [ ] 本文・リプに行頭 `## `（レベル2見出し）や `=====` だけの行が無い（`postcal_import.py` のセクション切り出し・リプ分割を壊さないため）
- [ ] 締めが疑問形でない。「——」が無い

---

# STEP 5: よーんに提示して選択を待つ（**必ず停止する**）

以下の形式で提示し、**採用案の返事があるまで次の STEP に進まない**。修正指示が来たら本文を直して字数を実測し直し、再提示して再び待つ。

```
記事: 【記事タイトル】（projects/w002/【記事フォルダ】）
note: 【note URL】
過去の販促: {n}件（{YYYY-MM-DD: 場面の一言} …）／なし

A案（{実測字数}字）｜{場面・フック型の一言}
> {本文}
セルフリプ：
> {導入1文}
> 【note URL】

B案（{実測字数}字）｜…
C案（{実測字数}字）｜…

採用案（A/B/C）または修正点をお知らせください。
```

---

# STEP 6: 予約ファイルの作成と push（採用案確定後）

Gmail 下書きは作らない。確定稿を**予約ファイル（Markdown）**として書き、master へ push する。VPS の `scripts/postcal_import.py`（systemd timer・10 分ごと）がこれを読み、**販促（`kind: promo`）は金曜 6:00 の最寄りの空き枠**に予約として登録する（既に埋まっていれば翌週の金曜）。登録された予約は `post.usephys.net` に表示され、6 時枠の cron が X → セルフリプ → Threads の順に投稿する。**本スキルでは投稿は一切行わない。**

> **更新ルール**: 予約ファイルは、**投稿が実行される（postcal の status=posted）までは、修正に合わせて同じファイル（同じ `uid`）を上書きして再 push してよい**（`uid` をキーに既存予約の本文・リプを更新する。枠は動かない）。新しい `uid` のファイルを増やさない。投稿済みになったら変更しない。**1 回の販促につき予約ファイルは 1 つ。**

1. トピック要約を決める（本文の核心を名詞句で **10〜15 字以内**。例:「ボイジャー2号 天王星への道」）。初回だけ `uid` を生成：`python3 -c "import uuid;print(uuid.uuid4().hex)"`。JST 日時：`TZ=Asia/Tokyo date '+%Y%m%d_%H%M%S'`。
2. `outputs/scheduled-posts/w007/<YYYYMMDD_HHMMSS>_<topicスラッグ>.md` に Write する（スラッグは空白を `_`、記号は除去）。形式：

   ```
   ---
   uid: <32桁hex・以降固定>
   project: w007
   what_id: W007
   kind: promo
   threads_enabled: true
   note_url: "【note URL】"
   source: "w002/【記事フォルダ】"
   topic: "{トピック要約}"
   created: "{YYYY-MM-DD HH:MM:SS} JST"
   ---

   ## 投稿文

   {採用案の本文（確定稿だけ）}

   ## セルフリプ

   {採用案の導入1文}
   【note URL】

   ## 記録

   - 記事: 【記事タイトル】（projects/w002/【記事フォルダ】）
   - 採用案: {A/B/C}（{場面・フック型の一言}）
   ```

   - `kind: promo` が金曜 6:00 の既定枠を決める（`what_id` は W007）。
   - `note_url` は必須。投稿後に outputs シートの note_url 列へ記録される。セルフリプの URL は生 URL のままにする（投稿時に `post_to_x.py` が `xpost.usephys.net` の転送リンクへ自動変換する）。
   - `source` は `noteNeta[..]` / `newsTopics[..]` の形ではないため、outputs の neta 列は `postcal[予約id]` になる（販促では SS1 の更新は不要）。
   - **枠を変えたいとき**だけ front-matter に `post_date: YYYY-MM-DD` と `slot: 6|12|17|20` を**両方**書く（新規登録時のみ有効。指定枠が埋まっていると登録されずエラーメールが届く）。登録後に日時を変えるなら `post.usephys.net` で編集する。
3. **commit & push**: 予約ファイルと STEP 7 の保存ファイルを master へ。**対象ファイルを明示する**（他セッションの未コミット変更を巻き込まない）：

   ```bash
   cd $(git rev-parse --show-toplevel) && bash scripts/commit_and_sync.sh \
     "post(w007): 販促の予約ファイルを追加（{トピック要約}）" \
     outputs/scheduled-posts/w007/<file>.md \
     projects/w002/【記事フォルダ】/promo/YYYYMMDD_xpromo.md
   ```

   push が認証エラー／非 fast-forward のときは `git fetch origin master` → origin/master に乗せ直して push、または GitHub MCP で master へ push する。**push しないと VPS のインポーターに届かない。** push 先は master と報告する。
4. 登録は VPS のインポーターが行うため、push 直後は `post.usephys.net` に出ない（最長 10 分）。

- Threads への転載は cron が自動で行う（note リンク入りのセルフリプは Threads には転載しない仕様。2026-10-02）。

---

# STEP 7: 案の保存

3 案と採用案を `projects/w002/【記事フォルダ】/promo/YYYYMMDD_xpromo.md` に保存する（次回の【過去フォーカス】として使う）。同名ファイルがあれば `_v2`, `_v3` … を付けて上書きしない。

```markdown
# {記事タイトル} — X 販促（140字）YYYY-MM-DD

- note: 【note URL】
- 採用: {A/B/C}
- 予約ファイル: outputs/scheduled-posts/w007/<file>.md（uid={uid}）

## A案（{字数}字）｜{場面・フック型}
{本文}

セルフリプ: {導入1文}

## B案 …
## C案 …
```

---

# STEP 8: 完了報告

```
✅ 記事選択（projects/w002/【記事フォルダ】 / 【記事タイトル】）
✅ 採用案 {A/B/C}（{実測字数}字）
✅ 予約ファイル作成・push 完了（outputs/scheduled-posts/w007/{ファイル名} / uid={uid}）→ master
✅ 保存: projects/w002/【記事フォルダ】/promo/YYYYMMDD_xpromo.md
※ 枠は VPS の postcal_import.py が金曜 6:00 の最寄りの空き枠に自動割当（post.usephys.net で確認）。
対象外の記事: {フォルダ名: 理由} ／ なし
```
