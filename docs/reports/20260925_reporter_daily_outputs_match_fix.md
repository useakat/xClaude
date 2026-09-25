---
title: reporter-daily の照合漏れを修正（outputs の日付形式・X の URL 表記の違い）
date: 2026-09-25
tags: [skill, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260925_reporter_daily_outputs_match_fix/)

## 背景・動機

9/24 分の日報を routine で作成した際、outputs シートから当日の投稿記録を取り出す STEP 3 が **0件**になった。原因は2つ。

1. **日付形式の違い** — SKILL は outputs の A列を `DATE_SHEET`（`2026/09/24`）で前方一致させる手順だったが、outputs の A列は `2026-09-24 12:00:06` のようにハイフン区切りで記録されている。他のシート（日次記録・X投稿一覧・Threads投稿一覧）はスラッシュ区切りのため、outputs だけが食い違っていた
2. **X の URL 表記の違い** — outputs は `https://x.com/i/web/status/…`、X投稿一覧は `https://twitter.com/i/web/status/…` と、同じ投稿でもドメインが異なる。SKILL は URL 文字列の一致で突合する手順だったため、日付の問題が無くても一致しない

どちらも、outputs と照合できない投稿はラベルが「その他」になる。つまり**すべての投稿の型（長文ストーリー・短文など）が判定できず「その他」になり**、note販促用の判定や型ごとの並び順も機能しなくなる。

9/24 の日報では実行中に気づき、手作業で照合して正しい型（短文）を付けたため、日報の内容には影響していない。

## 実施内容

`.claude/skills/reporter-daily/SKILL.md` の STEP 3 に以下を追記した。

- **outputs の照合日付を `DATE_ISO`（`2026-09-24`）に変更** — A列が `YYYY-MM-DD HH:MM:SS` 形式であること、`DATE_SHEET` で照合すると0件になり全投稿が「その他」になることを明記。念のため `DATE_SHEET` で始まる行があればそれも含める
- **X 投稿の URL 照合は URL 末尾の投稿番号（`/status/` の後ろの数字）で行う** — outputs は `x.com`、X投稿一覧は `twitter.com` 表記であることを明記し、STEP 4・STEP 5 のすべての X URL 照合に適用するとした

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/reporter-daily/SKILL.md` | STEP 3 の outputs 抽出を `DATE_ISO` 照合に変更し日付形式の注意を追記、X URL を投稿番号で照合するルールを追加 |

## 設計判断

**URL の投稿番号で照合する方式は、既存スキルに合わせた。** `reporter-weekly-ops` は既に「URL マッチは tweet ID 部分で行う（outputs は `x.com`、X投稿一覧は `twitter.com` 表記のため）」と定めていた。日報スキルだけ URL 文字列の一致のままだったため、同じ方式にそろえた。

**スラッシュ区切りの行も念のため拾う。** outputs への記録は複数のスキル・スクリプトが行っており、将来どこかがスラッシュ区切りで書き込む可能性を否定できない。どちらの形式でも取りこぼさないようにした。

## 確認結果

- 9/24 のデータで、`DATE_ISO` 照合により outputs から3行（X の短文1件・threads 2件）が抽出されること、X投稿一覧の `twitter.com/i/web/status/2102956206268764453` と outputs の `x.com/i/web/status/2102956206268764453` が投稿番号で一致し、what_id `z01`（短文）が付くことを確認
- SKILL.md を master に push し、`git diff HEAD origin/master` で master 上の内容とローカルが一致することを確認

## 今後の課題

- 過去の日報（STEP 3 がスラッシュ区切りの照合になって以降）で、本来の型ではなく「その他」になっている内訳がある可能性がある。必要なら遡って確認する
