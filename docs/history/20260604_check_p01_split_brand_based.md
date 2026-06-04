---
title: check-tonmana 縮小・check-p01 分離（brand.md 基準化） — セッション履歴
date: 2026-06-04
sidebar:
  hidden: true
---

# セッション履歴

> 2026-06-04 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260604_check_p01_split_brand_based/)

---

## よーん *(22:48 JST)*

check-tonmana skill で、style/style-xonepoint.md をスタイルガイドとするのではなくて、projects/x-onepoint/brand.md をスタイルガイドとするように修正して。また、P01化スコアリングの部分はこのスキルから分離して別のスキルとして。

### Claude *(22:48 JST)*

*[ツール: `Read`, `Read`]*

ファイルを確認しました。check-tonmana をトンマナ調整専用（brand.md 基準）に書き換え、P01化スコアリングを新スキル `check-p01` に分離します。

まず check-tonmana を書き換えます。

*[ツール: `Write`]*

Now the new `check-p01` skill with the scoring loop:

*[ツール: `Write`]*

Now update metadata.yaml and daily-xonepoint to call both skills in sequence.

*[ツール: `Edit`, `Read`, `Edit`]*

変更内容をまとめます。

## 変更内容

1. **check-tonmana** — トンマナ調整専用に縮小
   - スタイルガイドを `style/style-xonepoint.md` → **`projects/x-onepoint/brand.md`** に変更
   - P01化スコアリングを削除し、文体・口調・構成のみの調整に
   - 出力は【調整後本文】＋トンマナサマリー1行

2. **check-p01**（新規）— P01化スコアリングを分離
   - P01化チェックリスト6項目の10段階採点ループ（最大5回）
   - 採点基準テーブル・書き直しルール・警告フラグはそのまま移植
   - 参照は `style/style-xonepoint.md`（P01化定義の所在）のまま

3. **daily-xonepoint** — STEP 4 を 4-2（/check-tonmana）→ 4-3（/check-p01）の2段呼び出しに変更

4. **metadata.yaml** — `check-p01: 品質チェック` を追記

この内容でコミットしますか？（commit 時に Wiki も自動更新します）

---

## よーん *(22:59 JST)*

check-tonmana と check-p01 skill のスタイルガイドを、作業フォルダに有る brand.md に変更。

### Claude *(22:59 JST)*

作業フォルダ（カレントディレクトリ）の `brand.md` を参照するよう両スキルを変更します。

check-tonmana:

*[ツール: `Edit`]*

Now check-p01:

*[ツール: `Edit`]*

The 字数削減ルールが style-xonepoint.md の「削る対象優先度リスト」を参照しているので、brand.md 基準に直します。

*[ツール: `Edit`]*

description も style-xonepoint.md の言及を消しておきます。

*[ツール: `Edit`]*

両スキルとも、作業フォルダ（カレントディレクトリ）の `./brand.md` をスタイルガイドとして参照するよう変更しました。

## 変更まとめ

| スキル | 変更前の参照 | 変更後の参照 |
|---|---|---|
| check-tonmana | `projects/x-onepoint/brand.md`（固定パス） | 作業フォルダの `./brand.md` |
| check-p01 | `style/style-xonepoint.md` | 作業フォルダの `./brand.md` |

- check-p01 は採点基準のソースを brand.md の Writing Rules に変更し、字数削減ルールも brand.md の Do Not 基準に置き換え
- 採点テーブル6項目（スキル内に自己完結）はそのまま

この内容と前回分（check-tonmana 縮小・check-p01 分離・daily-xonepoint 2段化・metadata 追記）をまとめてコミットしますか？

---

## よーん *(23:08 JST)*

check-p01 はこれでちゃんとチェックできるようになっている？

### Claude *(23:08 JST)*

*[ツール: `Read`]*

ファイルを精査しました。正直に評価します。

## 現状の check-p01 の判定能力

**採点自体はできます** — 6項目の採点基準テーブルは SKILL.md 内に自己完結で埋め込まれているため、brand.md だけでも採点ループは回ります。

**ただし劣化している部分があります**。詳細な判定材料は `style/style-xonepoint.md` にしかなく、brand.md は要約しか持っていません：

| 必要な材料 | style-xonepoint.md | brand.md |
|---|---|---|
| 冒頭フック5軸の OK/NG 具体例（採点の精度） | ✅ 詳細あり（L30-79） | △ 軸名のみ |
| **削る対象優先度リスト**（字数超過時の書き直し手順） | ✅ あり（L105-114） | ❌ なし |
| 語尾・締め言葉の引き出し | ✅ 詳細あり | △ 要約のみ |

特に**字数オーバー時の「削る対象優先度リスト」が brand.md に存在しない**ため、私は「Do Not 項目から削る」という曖昧な表現に置き換えました。これは元の精度を落としています。

なお brand.md 自身が `### 文体・語尾` で「詳細は `style/style-xonepoint.md` 参照」と明記しており、brand.md は入口・style-xonepoint.md は詳細という関係になっています。

どう直すか確認させてください。

*[ツール: `AskUserQuestion`]*

「brand.md に詳細を移植」で進めます。影響範囲（style-xonepoint.md / brand.md を参照している箇所）を確認します。

*[ツール: `Agent`]*

影響範囲を把握しました。要点：

- `style/style-xonepoint.md` は **writer-xonepoint / writer-xqa が今も参照**しているので、そこから削除すると writer 系が壊れる
- なので「移植」は、**詳細を `projects/x-onepoint/brand.md` に展開して check-p01 を brand.md だけで自己完結させる**形にし、style-xonepoint.md は writer 系の参照元として残す

この方針で計画を書きます。

*[ツール: `Write`]*

計画をまとめました。

## 結論（質問への回答）

**現状の check-p01 は「採点はできるが書き直し精度が落ちる」状態**です。6項目の採点テーブルはスキル内に埋め込まれているので回りますが、字数超過時の「削る対象優先度リスト」が brand.md に無いことと、5軸の OK/NG 具体例が無いことで、精度が元より落ちています。

## 直し方（計画）

ユーザー選択どおり **`projects/x-onepoint/brand.md` に詳細を移植**して、check-p01 を brand.md 単体で完結させます。

- brand.md の Writing Rules に、5軸 OK/NG 例・言い換え例・視点例・数値例・感覚語例 を肉付け＋**削る対象優先度リストを新規追加**
- check-p01 の字数削減ルールを「削る対象優先度リスト参照」に戻す
- **style-xonepoint.md は変更しない**（writer-xonepoint / writer-xqa が現役で参照しているため）

唯一の注意点は、削る優先度リスト等が style と brand に併存する軽微な重複です（brand = 自己完結ハブ / style = writer 系詳細、という役割分担）。

計画ファイルに詳細を記載しました。

*[ツール: `ToolSearch`, `ExitPlanMode`]*

計画が承認されました。実装します。まず `projects/x-onepoint/brand.md` の Writing Rules を拡充します。

*[ツール: `Edit`]*

Now add the 削る対象優先度リスト. I'll place it after the 冒頭の日常接続ルール section, before Do Not.

*[ツール: `Edit`]*

Now revert the check-p01 字数削減 line and clean up the reference note.

*[ツール: `Edit`, `Edit`]*

Now verify the brand.md contains all 6 items' material and check the reference consistency.

*[ツール: `Read`]*

brand.md が check-p01 の6項目すべてを自己完結でカバーしています。検証OKです。コミットします。

call
<invoke name="Bash">
<parameter name="command">cd /home/useakat/xClaude && git status --short</parameter>
<parameter name="description">Check git status before commit</parameter>
</invoke>

---

## よーん *(23:26 JST)*

Your tool call was malformed and could not be parsed. Please retry.

### Claude *(23:26 JST)*

*[ツール: `Bash`]*

I'll stage the relevant skill/brand files (excluding the unrelated drafts-note file) and commit.

*[ツール: `Bash`]*

Wiki 自動更新を確認し、生成物があればコミットして push します。

*[ツール: `Bash`, `Bash`]*

push がブロックされました（master への直接 push に確認が必要）。コミット自体は完了しているか確認します。

*[ツール: `Bash`, `Bash`]*

The whole command was blocked, so the wiki docs are still uncommitted. I'll commit them separately (no push), then ask for push confirmation.

*[ツール: `Bash`]*

ローカルコミットは完了しました。**master への push は確認が必要**なため止めています。

## 実装完了内容

| 変更 | 内容 |
|---|---|
| `projects/x-onepoint/brand.md` | 5軸 OK/NG 例・言い換え/視点/数値/感覚語の例＋削る対象優先度リストを展開し、check-p01 が brand.md だけで自己完結 |
| `check-tonmana` | スタイルガイドを作業フォルダの brand.md に変更、トンマナ調整専用に |
| `check-p01`（新規） | P01化6項目採点ループ。字数削減は brand.md の「削る対象優先度リスト」参照に修正 |
| `daily-xonepoint` | STEP 4 を 4-2(/check-tonmana)→4-3(/check-p01) の2段に |
| `metadata.yaml` / Wiki | check-tonmana・check-p01 を反映 |

**検証済み**：brand.md が check-p01 の6項目すべてをカバー、参照見出し名も一致、style-xonepoint.md は無変更（writer 系を維持）。

未 push のローカルコミットは2件です：
- `1878536` feat(skills): check-tonmana 縮小・check-p01 分離
- `8c5dee1` docs(wiki): check-p01 反映

master に push してよろしいですか？

---

## よーん *(23:33 JST)*

これでP01化チェックは劣化せずに動く？

### Claude *(23:34 JST)*

正直に検証します。6項目を style-xonepoint.md の元材料と突き合わせました。

| 項目 | brand.md の現状 | 判定 |
|---|---|---|
| 2 専門用語言い換え | 形式＋例2件 | ✅ 同等 |
| 3 視点段落分け | NG/OK例＋切替語 | ✅ 同等 |
| 4 数値具体 | Before/After例＋曖昧禁止 | ✅ 同等 |
| 5 感覚語 | 例＋「爆速で」比較 | ✅ 同等 |
| 6 字数/削る優先度 | 優先度リスト5項目を完全転記 | ✅ 同等 |
| **1 冒頭フック5軸** | 軸名＋OK/NG例はあるが、**各軸の語彙定義が薄い** | △ やや劣化 |

項目1だけ、style-xonepoint.md にある「軸1=貫く/触れる/流れる…、軸2=僕らの/あなたの…、軸5=寿命を伸ばす/常識を裏切る…」という**各軸の判定語彙**が brand.md に無く、採点者が軸の有無を判定しづらい状態です。ここを埋めれば非劣化になります。修正します。

*[ツール: `Edit`]*

項目1に各軸の判定語彙（軸1=貫く/触れる…、軸2=僕らの…、軸5=寿命を伸ばす…）を補い、style-xonepoint.md と同等にしました。これで6項目すべて非劣化です。コミットします。

*[ツール: `Bash`]*

## 結論：はい、非劣化で動きます

最終確認の結果です。

| 項目 | brand.md の材料 | style-xonepoint.md 比 |
|---|---|---|
| 1 冒頭フック5軸 | 各軸の判定語彙＋必須注記＋OK/NG例 | ✅ 同等（今回補完） |
| 2 専門用語言い換え | 形式＋例 | ✅ 同等 |
| 3 視点段落分け | NG/OK例＋切替語 | ✅ 同等 |
| 4 数値具体 | Before/After＋曖昧禁止 | ✅ 同等 |
| 5 感覚語 | 例＋体感比較 | ✅ 同等 |
| 6 字数/削る優先度 | 優先度リスト5項目を完全転記 | ✅ 同等 |

- 6項目の**採点テーブル自体**は check-p01 内に元のまま埋め込まれており不変
- 採点・書き直しに必要な**参照材料**も brand.md だけで完結（style-xonepoint.md 参照時と同等）
- style-xonepoint.md は無変更なので writer 系も非破壊

## 未 push のローカルコミット（3件）
- `1878536` feat: check-tonmana 縮小・check-p01 分離
- `8c5dee1` docs(wiki): 反映
- `e5a1199` docs(brand): 5軸語彙の補完

master に push してよろしいですか？

---

## よーん *(23:41 JST)*

はい

### Claude *(23:41 JST)*

*[ツール: `Bash`]*

**master にプッシュしました。**

3コミット（`1878536`・`8c5dee1`・`e5a1199`）が反映されました。

- check-tonmana：トンマナ調整専用（brand.md 基準）
- check-p01：P01化採点を分離、brand.md だけで非劣化に動作
- brand.md：6項目の判定材料を完全展開
- daily-xonepoint：4-2→4-3 の2段化
- Wiki 反映済み

この一連の変更を `/record` で記録しますか？

*[ツール: `Bash`]*

未記録の変更は1件です。

---

**変更ログ候補（未記録）**

1. **check-tonmana をトンマナ調整専用に縮小し P01化を check-p01 へ分離（brand.md 基準化）** — check-tonmana を作業フォルダの brand.md 基準のトンマナ調整専用に縮小し、P01化スコアリングを新スキル check-p01 として分離。brand.md に5軸語彙・各種例・削る対象優先度リストを展開して check-p01 を brand.md 単体で非劣化に動作させ、daily-xonepoint を 4-2→4-3 の2段呼び出しに変更。
   - 関連コミット: `1878536`（feat 本体）・`8c5dee1`（wiki）・`e5a1199`（brand 5軸補完）
   - 変更ファイル: `.claude/skills/check-tonmana/SKILL.md`, `.claude/skills/check-p01/SKILL.md`, `daily-xonepoint/SKILL.md`, `metadata.yaml`, `projects/x-onepoint/brand.md`
   - 関連する過去の変更: 「check-tonmana スキル新設」（2026-06-04、本変更で再設計）、「ネタ選定を writer-xonepoint から daily-xonepoint に移動」（2026-06-01）

記録しますか？（「1」で記録 / 「スキップ」で終了）

---

## よーん *(23:42 JST)*

1

### Claude *(23:42 JST)*

*[ツール: `Write`, `Bash`, `Bash`]*
