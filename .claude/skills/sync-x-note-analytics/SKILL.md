---
name: sync-x-note-analytics
description: outputs/X投稿一覧/note投稿一覧/note購入記録 を集約して「Xnote導線記録」シートを再生成する。W001 ごとの IMP・リンクCTR・購入CVR・売上を 1 行 1 投稿の集計シートにまとめる。
tools: Bash, mcp__mcp-gsheets__sheets_get_values
---

X→note 導線分析の集計シートを最新化するスキルです。実行すると `Xnote導線記録` シートが全件再生成されます。

ユーザーからの依頼: $ARGUMENTS

---

## データソース

| シート | 役割 |
|---|---|
| outputs (SS2: `1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc`) | 投稿記録（A=日時, B=URL, C=what_id, F=note_url） |
| X投稿一覧 (SS3: `1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c`) | X 指標（B=ポストURL, C=本文, K=IMP, AB=リンククリック） |
| note投稿一覧 (SS3) | note 指標（B=URL, C=タイトル, H=ビュー, I=スキ） |
| note購入記録 (SS3) | 購入生データ（E=記事タイトル, F=価格） |

書き込み先：`Xnote導線記録` シート（SS3）の A〜O 列。

---

## 前提条件

スクリプト実行前に以下が最新化されている必要がある：

- **X analytics**：`/update-x-analytics` を直近で実行済み（X投稿一覧 の AA:AC 列が最新）
- **note 統計**：`/record-note-posts` を直近で実行済み（note投稿一覧 の H/I 列が最新）
- **outputs**：W001 投稿には F 列に対応する note URL が入っていること（紐付かない投稿は集計対象外）

---

# STEP 1: 前提確認

ユーザーに 1 行で確認：

```
X analytics と note 統計は最新ですか？古ければ先に /update-x-analytics と /record-note-posts を実行してください。
（このまま進めるなら「ok」、止めるなら「待って」）
```

「待って」「stop」などの返答があれば終了。

---

# STEP 2: fetch_note_stats.py で note 統計を最新化（任意）

ユーザーが既に `/record-note-posts` を実行済みの場合はスキップ。未実行なら：

```bash
cd /root/xClaude
python3 scripts/fetch_note_stats.py --months 6 > /tmp/note_stats.json
```

注：このスクリプトは note の `_note_session_v5` Cookie に依存する。Cookie 期限切れの場合は view が 0 になる。

---

# STEP 3: 集計シート再生成

```bash
cd /root/xClaude
python3 scripts/sync_x_note_analytics.py
```

スクリプトは：
1. outputs から what_id=W001 の行を抽出（A=日時, B=URL, F=note_url）
2. X投稿一覧 で tweet ID マッチ → IMP/リンククリック/本文を取得
3. note投稿一覧 で note URL マッチ → タイトル/ビュー/スキを取得
4. note購入記録 で記事タイトル別に購入数・売上を集計
5. Xnote導線記録 シート A2:O{n+1} を全件上書き

出力例：

```
✅ Xnote導線記録 更新完了 (8件)
   平均CTR: 0.23%  平均CVR: 0.70%  累計売上: ¥3,660
```

---

# STEP 4: 結果サマリーをユーザーに報告

スクリプトの最終出力（W001 件数・平均CTR・平均CVR・累計売上）をそのまま 1 行でユーザーに報告する。

```
✅ Xnote導線記録 を更新しました（N件 / 平均CTR x.xx% / 平均CVR y.yy% / 累計売上 ¥Z）
   詳細はシートを確認: https://docs.google.com/spreadsheets/d/1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c/edit#gid=526280240
```

---

## 注意事項

- W001 投稿で outputs!F に note_url が入っていない投稿は **集計対象外**（行に出ない）
- note 価格は note購入記録から実勢平均を算出（売上 ÷ 購入数）。購入が無い記事は価格は空欄
- 売上 (M列) は実際の購入価格の合計。定価 × 部数ではない（割引・チップを反映した実勢値）
- スクリプトは A2:O1000 をクリアしてから書き込む。既存の手動編集は失われるので注意
- 過去 W001 で outputs に未記録の投稿（エンケラドス・海王星・ニューホライズンズ・ルメートル等）は、まず outputs に手動追加してから本スキルを実行
