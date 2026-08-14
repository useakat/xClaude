---
title: NotebookLM の Deep Research 生成報告書によるソース汚染を解消（検証ループの循環を遮断）
date: 2026-08-14
tags: [bugfix, infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md#2026-08-14) ｜ [セッション履歴→](../../history/20260814_notebooklm_generated_report_contamination/)

## 背景・動機

SOHO のジャイロレス運用を題材にした W001 販促原稿の制作中、`/check-fact-lim`（notebook のソースだけを根拠にするファクトチェック）が、**同じ誤った物理説明を2度出力した**。

原稿の核心は「壊れた姿勢センサーの代わりに、リアクションホイールの回転数から機体の回転量を求めた」という仕組みである。これに対し check-fact-lim は次の別方式を「正しい仕組み」として提示し、原稿の書き換えを求めてきた。

> ホイールを高速定常回転させてバイアス角運動量（コマの効果）を作り、機体がロールすると角運動量の交差結合で直交するヨー軸にズレが生じる。そのズレをファインポインティング太陽センサー（FPSS）で検出してロールレートを逆算する。

一方、一次情報は明確に逆を述べていた。

> "The momentum vector in the spacecraft can be constructed from **the wheel speed measurements**. The angular change in the transverse component is the amount the spacecraft has rolled." / "**Pitch and yaw** are measured with the Fine Pointing Sun Sensor."
> — ESA 運用担当者 Ton van Overbeek（The Register, 2020-07-29）

`/check-critic`（知識ある読者チェック・2026-08-10 新設）も、独立に同じ指摘（「太陽センサーはロールを読めない。ロールの読み取り役はホイールの回転数」）を出していた。**check-critic と一次情報の突き合わせが無ければ、誤った物理をそのまま投稿していた。**

notebook に「どのソースがこの説明の出所か」を照会したところ、53件中**1件のソースだけ**が該当した。それが Deep Research の生成報告書だった。

## 原因

`vendor/notebooklm/_research.py` の `import_sources()` は、Deep Research の結果を取り込む際に **`result_type == 5`（＝生成された報告書エントリ）もソースとして登録する**。

```python
report_sources = [s for s in sources
                  if s.get("result_type") == 5 and s.get("report_markdown")]
...
for report_source in report_sources:
    source_array.append(self._build_report_import_entry(...))  # 生成報告書をソース化
```

`scripts/notebooklm_browser_bridge.py` の `cmd_deep_research` はこれを無条件で呼んでいたため、**Deep Research が書いた要約レポートが、その notebook 自身の「ソース」になっていた**。以後 `check-fact-lim` はそれを一次資料として照合するので、**AI の生成物を AI が検証する循環**が成立していた。

生成報告書は次の特徴を持つ（今後の判別点）。

1. 著者名・発行機関・出典URLが記載されていない
2. 本文に `[cite: 1, 2, 3]` 形式の引用マーカーが露出している（生成AIの中間出力の痕跡）
3. LaTeX 記法（`\(30.06 \text{ AU}\)`、`$$E = ...$$`）が混在している
4. 日本語の長い解説的タイトル（「…学術解析報告書」「…の多角的高精度解析」）
5. `SOURCE_CONTENT_TYPE_MARKDOWN` 形式

## 実施内容

- **`deep-research` が生成報告書を既定で取り込まないよう変更**（`result_type == 5` を除外）。除外時は理由を stderr に表示し、従来動作は `--with-report` で選択可能とした
- **`list-sources --ids`** を追加（source_id を併記。削除対象の特定に必要）
- **`delete-source <notebook_id> <source_id>`** を新設（vendor の `SourcesAPI.delete()` を呼ぶ薄い実装）
- docstring に発生経緯・判別点・対処法を記載
- **全24 notebook を棚卸し**し、汚染2件を削除
  - SOHO（W001/W002 共用）: 「太陽観測衛星SOHOにおける1998年の通信途絶事案と軌道・姿勢制御復旧プロセスの学術解析報告書」1件（53→52件）
  - 探査機の手ブレ対策（W003）: 「ボイジャー2号の海王星遭遇における極限姿勢制御と運動補償技術の多角的高精度解析」**重複2件**（87→85件）

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/notebooklm_browser_bridge.py` | deep-research の報告書除外・`--with-report`・`list-sources --ids`・`delete-source` 新設・docstring 追記 |

※ 同コミットには別セッションの未コミット作業（`add-source` / `add-text`）が同梱されている。

## 設計判断

- **既定で除外し、オプトインで残した**：生成報告書は読み物としては有用なので完全削除はせず、`--with-report` で取り込める余地を残した。ただし check-fact-lim の照合先としては不適切なため、既定は除外側に倒した。
- **vendor は変更しない**：`_research.py` はライブラリ側の実装であり、更新で上書きされうる。呼び出し側（ブリッジ）でフィルタする方が保守が楽と判断した。
- **削除は手動確認を挟む**：`delete-source` は ID 指定の1件削除に留め、パターンマッチでの一括削除は実装しなかった。正当な日本語ソースを巻き込む危険があるため。

## 確認結果

- 汚染ソース削除後、SOHO notebook に同じ質問を再照会し、**誤った説明が完全に消えた**ことを確認。回答は NASA の当時の運用ブログを根拠とするものに変わった
  > "Tomorrow we will **spin up the four reaction wheels** to get an accurate **roll rate determination**..."（1999年1月19日）
- 太陽センサーによるロール逆算については「**どのソースにも存在しません**」と明示的に否定された
- Wikipedia ソースからも裏付けを確認：`"the first three-axis-stabilized spacecraft to use its reaction wheels as a kind of virtual gyroscope"`
- 汚染は24件中2件のみ。いずれも Deep Research を実行しソース数が多い notebook（53件・87件）だった。`research_trivia-source` 経由の小規模 notebook（2件程度）では発生していない

## 今後の課題

- 生成報告書の混入を**検知する仕組み**は入れていない（今回は手動棚卸し）。今後 Deep Research を回した notebook は、判別点1〜5 で目視確認する運用とする
- 今回のような「notebook 自体が誤っている」ケースは check-fact-lim 単独では検出できない。**check-critic の指摘を一次情報で裏取りする工程（各 spec の 6.6）が機能した初の実運用例**であり、この工程は省略しないこと
