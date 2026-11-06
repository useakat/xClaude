---
title: writer-xpromo
description: "W002 の公開済み note 記事をランダムに1本選び、140字の販促投稿（本文＋note 導線セルフリプ）を3案作ってよーんに選んでもらい、採用案を件名【note販促】の Gmail 下書きにする（X への投稿は行わない）"
category: コンテンツ制作
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

W002 の公開済み note 記事をランダムに1本選び、140字の販促投稿（本文＋note 導線セルフリプ）を3案作ってよーんに選んでもらい、採用案を件名【note販促】の Gmail 下書きにする（X への投稿は行わない）

## 詳細内容

W002（note 記事）の公開済み記事から 1 本を選び、その記事へ誘導する **140 字の X 販促投稿**を作る。
本文には note への誘導を書かず、**誘導はセルフリプ（1 文＋URL）に回す**。投稿は 20 時枠の cron（`run_xshort_post.sh` → 件名【note販促】 → what_id W007）が行う。

入力（`$ARGUMENTS`、任意）: W002 のフォルダ名（例 `2026-08-20_akatsuki`）。指定があればランダム選択を飛ばしてその記事を使う。

**Gmail 下書きは STEP 5 でよーんが採用案を選んだ後に 1 回だけ作る。選択を待たずに作らない。**

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
- [ ] 本文・リプに `[投稿文]` `[/投稿文]` `[リプ]` `[/リプ]` `[note_url]` の文字列が無い（`extract_tag.py` の早期クローズ防止）
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

# STEP 6: Gmail 下書きの作成（採用案確定後に 1 回だけ）

**下書きは 1 回だけ作り、作成後は触らない**（その後の手直しはよーんが Gmail 上で行う）。

1. 本文を `/tmp/xpromo_mail.txt` に Write する：

   ```
   記事: 【記事タイトル】
   フォルダ: projects/w002/【記事フォルダ】
   採用案: {A/B/C}（{場面の一言}）

   [note_url]
   【note URL】
   [/note_url]

   [投稿文]
   {採用案の本文}
   [/投稿文]

   [リプ]
   {採用案の導入1文}
   【note URL】
   [/リプ]
   ```

2. 件名用トピック要約を作る（本文の核心を名詞句で **10〜15 字以内**。例:「あかつき 満点を狙わない減速」）。
3. JST 日時を取得する: `TZ=Asia/Tokyo date '+%Y%m%d %H:%M:%S'`
4. 下書きを作成する（添付なし）：

   ```bash
   cd $(git rev-parse --show-toplevel) && bash scripts/create_gmail_draft.sh \
     --to useakat@gmail.com \
     --subject "【note販促】{トピック要約} {YYYYMMDD HH:MM:SS}" \
     --body-file /tmp/xpromo_mail.txt
   ```

   成功判定は `✓ 下書き作成完了 (id: …)`。gws の認証エラー（Precondition 等）が出たら `bash scripts/gws_auth.sh` の出力をそのままよーんに伝えて再認証してもらい、完了後に再実行する。

- 投稿枠: よーんが下書きを自分宛に送信すると、**20 時枠**（`run_xshort_post.sh`）が【自己開示】の次に【note販促】を探して W007 として投稿し、`[note_url]` を `outputs!F` に記録する。別の枠で出したいときは Gmail ラベル `6時投稿` / `12時投稿` / `17時投稿` を付ける（`post_by_label.sh` が件名を問わず拾う）。
- Threads への転載は cron が自動で行う（note リンク入りのセルフリプは Threads には転載しない仕様。2026-10-02）。

---

# STEP 7: 案の保存

3 案と採用案を `projects/w002/【記事フォルダ】/promo/YYYYMMDD_xpromo.md` に保存する（次回の【過去フォーカス】として使う）。同名ファイルがあれば `_v2`, `_v3` … を付けて上書きしない。

```markdown
# {記事タイトル} — X 販促（140字）YYYY-MM-DD

- note: 【note URL】
- 採用: {A/B/C}
- Gmail 下書き件名: 【note販促】{トピック要約} {YYYYMMDD HH:MM:SS}

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
✅ Gmail 下書き作成完了（件名: 【note販促】{トピック要約} {YYYYMMDD HH:MM:SS}）
✅ 保存: projects/w002/【記事フォルダ】/promo/YYYYMMDD_xpromo.md
対象外の記事: {フォルダ名: 理由} ／ なし
```
