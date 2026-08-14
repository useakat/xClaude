---
title: NotebookLM の Deep Research 生成報告書によるソース汚染を解消 — セッション履歴
date: 2026-08-14
sidebar:
  hidden: true
---

← [報告書へ戻る](../../reports/20260814_notebooklm_generated_report_contamination/)

# セッション履歴

> 2026-08-14 のセッション作業ログ。SOHO 販促原稿のファクトチェックで発覚した notebook のソース汚染を、特定・除去・再発防止するまで。

---

## よーん *(13:24 JST)*

その不正確な２次資料を特定して

### Claude *(13:25 JST)*

notebook に直接照会して、どのソースがその説明の出所か特定します。

*[ツール: `Bash`]*

特定できました。原因は notebook 内の**1件のソース**です。

*[ツール: `Bash`]*

特定できました。

## 犯人

**「太陽観測衛星SOHOにおける1998年の通信途絶事案と軌道・姿勢制御復旧プロセスの学術解析報告書」**

53件中、あの物理説明（バイアス角運動量→交差結合→ヨー変位→FPSSで逆算）を書いているのは **このソース1件だけ** でした。notebook 自身がそう答えています。

**これはウェブから取得した文献ではなく、Deep Research が生成した報告書がそのままソースとして取り込まれたものです。** 根拠は3点。

1. **他の52件が実在の機関・媒体名**（ESA、NASA、arXiv、CDAW、Physics World、Wikipedia 等）なのに、これだけが日本語の無名文献で、対応する原典が存在しない
2. **本文に `[cite: 18, 21]` という引用マーカーが露出している** — 生成AIが出力した中間テキスト特有の痕跡で、人間が書いた報告書には現れません
3. LaTeX 記法（`\(\omega_{roll}\)`、`\[\tau_{yaw} \approx \omega_{roll} \times H_{pitch}\]`）が混在した体裁

つまり **Deep Research の生成物が、その notebook 自身のソースになっていた**。check-fact-lim はそれを「一次ソース」として照合していたので、**AIの出力をAIが検証する循環**が起きていました。同じ誤りを2回出したのはこのためです。

## 正しい記述は notebook 内にもあった

**「SOHO - ASTRONET」**（ESA公式発表の転載と見られる）に、正確な説明が入っていました。

> the new software will now allow engineers to determine SOHO's drift by **measuring the slight changes in the speed of the so-called momentum wheels**. In a way, these wheels, which are normally used to impart the necessary force to point the spacecraft, **will be used as if they were gyroscopes**

The Register の ESA 運用担当者インタビューと完全に一致します。現行の本文（「円盤の回り方を読めば、どれだけ回ったか分かる」）はこちらに沿っており、**しかも「動かすための部品を、測るための部品として使う」という本文の核も、この公式表現とほぼ同じ言い回し**です。

なお notebook は両者の食い違いを「ASTRONET 側が簡略化した表現」と解釈していましたが、実際は逆で、生成報告書側が誤りです。

## 対処の提案

1. **当該ソースを notebook から削除する** — 残すと今後の check-fact-lim が同じ誤りを再生産します（削除はよーんの確認が要るのでご指示ください）
2. **`research_setup-sources` を点検する** — Deep Research の生成報告書をソースとして取り込む挙動なら、他の notebook でも同じ汚染が起きている可能性があります。ワンポイント解説（W003）も同じ仕組みで notebook を作っているので影響範囲は広めです

この2点、どう進めますか。

---

## よーん *(13:56 JST)*

両方すすめて

### Claude *(13:57 JST)*

まず汚染の発生源を特定するため、Deep Research の取り込み処理を調べます。

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`]*

原因が確定しました。

## 汚染のメカニズム

`vendor/notebooklm/_research.py` の `import_sources()` は、Deep Research の結果を取り込む際に **`result_type == 5`（＝生成された報告書エントリ）を、ウェブソースと一緒に notebook へ登録します**（`_build_report_import_entry`）。

```python
report_sources = [s for s in sources if s.get("result_type") == 5 and s.get("report_markdown")]
...
for report_source in report_sources:
    source_array.append(self._build_report_import_entry(...))   # ← 生成報告書をソース化
```

`scripts/notebooklm_browser_bridge.py` の `cmd_deep_research` はこれを無条件で呼んでいるため、**Deep Research が書いた要約レポートが、その notebook 自身の「ソース」になります**。以後 `check-fact-lim` はそれを一次資料として照合するので、AI の生成物を AI が検証する循環が成立していました。

これは `research_setup-sources` を使う全プロジェクト（W001/W002/W003）の notebook に共通して起きているはずです。

## 対処案

**① 当該ソースの削除**：ブリッジには削除コマンドがありません。vendor に削除APIがあるか確認します。

**② 再発防止**：`cmd_deep_research` に「生成報告書は取り込まない」フィルタを入れる（`--no-report` 相当をデフォルトに）。`scripts/` の編集になるため、着手前に確認をいただきます。

まず削除APIの有無を確認します。

*[ツール: `Bash`]*

削除API（`SourcesAPI.delete` / `DELETE_SOURCE`）は vendor 側に揃っています。ブリッジから呼べないだけです。

両方を実現するには `scripts/notebooklm_browser_bridge.py` の編集が必要です（CLAUDE.md により事前確認します）。提案は次の2点です。

**① `delete-source` サブコマンドを追加**
```
python3 scripts/notebooklm_browser_bridge.py delete-source <notebook_id> <source_id>
```
既存の `SourcesAPI.delete()` を呼ぶだけの薄い追加。これで汚染ソースを削除できます。合わせて `list-sources` にソースIDを表示させます（現在はタイトルのみでIDが分からず、削除対象を指定できないため）。

**② `deep-research` が生成報告書を取り込まないようにする**
`cmd_deep_research` で `import_sources` に渡す前に `result_type == 5`（報告書エントリ）を除外します。既定で除外し、必要なら `--with-report` で従来動作に戻せるようにします。これが再発防止の本体です。

この2点、`scripts/notebooklm_browser_bridge.py` を編集してよいですか。

承認いただければ、続けて次を実施します。

- SOHO notebook から当該ソースを削除し、削除後に同じ質問を投げて**誤った説明が出なくなること**を確認
- 他プロジェクトの notebook（W002/W003 の既存 notebook）に同種の生成報告書ソースが混入していないか棚卸し

なお本文自体は一次情報に沿った現行版で正しいので、原稿の修正は発生しません。

---

## よーん *(14:35 JST)*

OK

### Claude *(14:35 JST)*

*[ツール: `Read`, `Read`]*

`list-sources` にID表示を追加し、`delete-source` を新設します。

*[ツール: `Edit`]*

Deep Research が生成報告書を取り込まないようにします。

*[ツール: `Bash`, `Edit`, `Bash`, `Edit`, `Bash`]*

ドキュメントの使い方欄にも新コマンドを追記します。

*[ツール: `Edit`]*

実装完了。SOHO notebook の汚染ソースを特定して削除します。

*[ツール: `Bash`, `Bash`]*

削除できました。誤った説明が出なくなったか検証します。

*[ツール: `Bash`]*

汚染が解消されました。同じ質問に対し、**誤った説明は完全に消え**、NASA の当時の運用ブログという一次資料で裏付けられた回答に変わっています。

> "Tomorrow we will **spin up the four reaction wheels** to get an accurate **roll rate determination**..."（NASA運用ブログ 1999年1月19日）

太陽センサーによるロール逆算については「**どのソースにも存在しません**」と明確に否定されました。現行の本文（円盤の回り方を読む）が正しいことが確定です。

Wikipedia からも決定的な裏付けが出ました。

> "SOHO is distinguished by being the **first three-axis-stabilized spacecraft to use its reaction wheels as a kind of virtual gyroscope**"

他プロジェクトの notebook も棚卸しします。

*[ツール: `Bash`]*

24件の notebook を順に検査します（ブリッジは直列実行が必要なため1件ずつ）。

*[ツール: `Bash`]*

W001/W002 は全7件クリーンでした。W003 も検査します。

*[ツール: `Bash`, `Bash`]*

もう1件、汚染を検出しました。W003「探査機の手ブレ対策」に**同じ生成報告書が2つ重複**しています。

正体を確認します。

*[ツール: `Bash`]*

同一パターンを確定できました。**著者・発行機関・出典URLなし**、`[cite: 1, 2, 3]` マーカーあり、LaTeX 記法あり、`SOURCE_CONTENT_TYPE_MARKDOWN` 形式 — SOHO の汚染ソースと完全に一致します。

重複2件を削除します。

*[ツール: `Bash`]*

両方の対処が完了しました。

## ① 汚染ソースの削除

| notebook | 削除したソース | 結果 |
|---|---|---|
| SOHO（W001/W002） | 太陽観測衛星SOHOにおける…学術解析報告書 | 53 → 52件 |
| 探査機の手ブレ対策（W003） | ボイジャー2号の海王星遭遇における…多角的高精度解析（**重複2件**） | 87 → 85件 |

**SOHO は削除後の再照会で汚染解消を確認済み**です。同じ質問に対し誤った説明は完全に消え、NASA の当時の運用ブログが根拠として返るようになりました。

> "Tomorrow we will **spin up the four reaction wheels** to get an accurate **roll rate determination**..."（NASA運用ブログ 1999年1月19日）

さらに太陽センサーによるロール逆算は「**どのソースにも存在しません**」と明示的に否定され、現行本文の正しさが確定しました。

## ② 全notebook 棚卸し（24件）

**汚染は2件のみ**でした。W001/W002 の7件、W003 の残り15件はすべてクリーンです。

汚染された2件はいずれも **Deep Research を実行した notebook** で、ソース数が多いもの（53件・87件）でした。W003 の多く（2件程度の小さい notebook）は `research_trivia-source` 経由で生成報告書の取り込みが発生していません。

## ③ 再発防止（実装済み）

`scripts/notebooklm_browser_bridge.py` を修正しました。

- **`deep-research` が生成報告書（`result_type == 5`）を既定で取り込まない**。取り込み時は理由付きで stderr に表示。従来動作は `--with-report` で選択可能
- **`list-sources --ids`** でソースIDを表示（削除対象を特定するため）
- **`delete-source <notebook_id> <source_id>`** を新設
- docstring に発生経緯と対処法を記載

## 検出パターン（今後の判定材料）

生成報告書は次の特徴を持ちます。

1. 著者名・発行機関・出典URLがない
2. 本文に `[cite: 1, 2, 3]` 形式のマーカーが露出
3. LaTeX 記法（`\(30.06 \text{ AU}\)`、`$$E = ...$$`）が混在
4. 日本語の長い解説的タイトル（「…の多角的高精度解析」「…学術解析報告書」）
5. `SOURCE_CONTENT_TYPE_MARKDOWN` 形式

---

原稿自体は一次情報に沿った現行版（698字）で正しく、修正は発生していません。

次にできることは、`scripts/` の変更のコミット、`/record` への記録、そして中断していた `/check-brand` です。どれから進めますか。

---

## よーん *(15:51 JST)*

scripts/ の変更のコミットから進めて

### Claude *(15:51 JST)*

*[ツール: `Bash`, `Bash`]*

確認が必要な点が出ました。`notebooklm_browser_bridge.py` の差分に、**私が書いていない変更が混ざっています**。

`cmd_add_source`（URL でソース追加）と `cmd_add_text`（テキストでソース追加）の2コマンドです。私が編集を始める前から作業ツリーに存在していた未コミット変更で、HEAD には入っていません。別セッションの作業と思われます（このセッション中、別の Claude セッションが同じリポジトリで動いていたことを確認済みです）。

同じファイル内で私の変更（`delete-source` / `--ids` / `--with-report`）と混在しているため、機械的には分離できません。

`scripts/send_note_draft.py` にも無関係な未コミット変更（+17/-3行）があります。こちらは別ファイルなので、コミット対象から外せます。

進め方の候補です。

**A. bridge の変更をまとめて1コミットにする（推奨）**
`add-source` / `add-text` も同じブリッジの機能拡張で、内容的にも矛盾しません。コミットメッセージに「add-source/add-text は別セッションの作業を同梱」と明記して履歴に残します。`send_note_draft.py` は対象外。

**B. 私の変更だけを分離してコミットする**
`add-source` / `add-text` を一時的に取り除いてコミットし、その後戻す、という手順になります。作業ツリーを一度壊すので、別セッションが同ファイルを編集中だと衝突する危険があります。

**C. 別セッションの作業内容を確認してから決める**
`add-source` / `add-text` が完成しているか（動作確認済みか）不明なため、未完成のものをコミットすると不完全な状態が master に載ります。

私の推奨は **A** です。追加された2コマンドは既存の `SourcesAPI` を呼ぶだけの薄い実装で、構文チェックも通っており、壊れている様子はありません。ブリッジのソース操作コマンド群（追加・一覧・削除）が一度に揃う形になります。

どれで進めますか。

---

## よーん *(15:59 JST)*

1

### Claude *(15:59 JST)*

*[ツール: `Bash`]*

---

## よーん *(15:59 JST)*

[Request interrupted by user for tool use]

A

### Claude *(15:59 JST)*

案A で進めます。`notebooklm_browser_bridge.py` のみをコミットします。

*[ツール: `Bash`]*

`send_note_draft.py` は未ステージのままです。コミットします。

*[ツール: `Bash`]*

コミットしました（`6313c13`）。`send_note_draft.py` は別セッションの作業なので未コミットのまま残しています。

**push はまだです。** master への push と `/record` への記録、どちらも実施しますか。

なお記録に値する内容だと考えています。今回の一件は個別のバグではなく、**リサーチ基盤の検証ループが閉じていた**という構造的な問題で、`/check-fact-lim` を使う全プロジェクト（W001/W002/W003/Z01）に影響していました。判別点も特定できているので、報告書に残す価値があります。

その後、中断している SOHO 原稿の `/check-brand` に戻れます。

---

## よーん *(16:26 JST)*

push & record

### Claude *(16:26 JST)*

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`]*

**master に push しました**（`9a8bc34`）。退避した変更を戻します。

*[ツール: `Bash`]*

両方の stash を復元しました（残っている `stash@{0}` は以前からある別物なので触れていません）。

`/record` に進みます。

*[ツール: `Skill`]*

---

## よーん *(16:27 JST)*

Skill /record is already loaded above; instructions unchanged.

### Claude *(16:27 JST)*

*[ツール: `Bash`, `Bash`]*

`9a8bc34` のみが未記録です。候補を提示します。

---

**変更ログ候補（未記録）**

以下の変更が記録されていません。記録するものを選んでください：

1. **NotebookLM の Deep Research 生成報告書によるソース汚染を解消（検証ループの循環を遮断）** — `check-fact-lim` が誤った物理説明を2度出力した原因が、Deep Research の生成報告書が notebook 自身のソースになり「AIの出力をAIで検証する循環」に陥っていたことと判明。取り込みを既定で停止し、`delete-source` を新設。全24 notebook を棚卸しして汚染2件を削除
   - 関連コミット: `9a8bc34 fix(notebooklm): Deep Research の生成報告書をソース化しないよう変更＋ソース削除コマンドを追加`
   - 変更ファイル: `scripts/notebooklm_browser_bridge.py`
   - 関連する過去の変更: NotebookLM ブリッジのチャット応答間引き（8/11）、ブリッジに排他ロックと後始末を追加（8/11）、ブラウザ内RPCブリッジに ask を追加（8/9）、知識ある読者チェック check-critic を新設（8/10）

（記録するなら「1」、不要なら「スキップ」と言ってください。）

---

この一件は、`/check-critic` と一次情報の突き合わせが無ければ誤った物理をそのまま投稿していた事例でもあります。報告書には、8/10 に新設した check-critic が初めて実運用で効いた記録としても残せます。

---

## よーん *(16:40 JST)*
