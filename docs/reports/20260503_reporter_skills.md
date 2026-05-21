---
title: reporter スキル追加
date: 2026-05-03
tags: [skill, workflow]
---

← [変更ログへ](../changelog/)

## 背景・動機

X・note 運用の日次データ（フォロワー数・投稿数・インプレッション等）は Google Sheets に自動収集されているが、それをもとにした日報・週報・月報の作成は手動だった。記録の継続性と品質の安定のため、スキルとして自動化した。

## 実施内容

- `reporter-daily` スキルを新設：日次記録・投稿一覧シートから当日データを取得し、特記事項を AI 生成して `docs/reports/daily/YYYY-MM-DD.md` に保存
- `reporter-weekly` スキルを新設：週集計データ・当週日報・前月報「次月への改善」を参照し、やったこと・来週タスクを AI 生成して `docs/reports/weekly/YYYY-WXX.md` に保存
- `reporter-monthly` スキルを新設：月次フォロワー増減・note 売上を集計し、総評・良かったこと・次月改善計画を AI 生成して `docs/reports/monthly/YYYY-MM.md` に保存
- `docs/reports/daily/`, `weekly/`, `monthly/` の各 `index.md` を作成
- gws CLI の `gws sheets spreadsheets values get` を `settings.json` の `permissions.allow` に追加

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/reporter-daily/SKILL.md` | 新規作成（7ステップ：日付決定→シート取得→投稿一覧取得→特記事項生成→保存→インデックス更新→コミット）|
| `.claude/skills/reporter-weekly/SKILL.md` | 新規作成（8ステップ：週決定→集計データ取得→日報読込→前月報読込→コンテンツ生成→保存→インデックス更新→コミット）|
| `.claude/skills/reporter-monthly/SKILL.md` | 新規作成（9ステップ：月決定→フォロワー取得→note売上集計→日報週報読込→翌月目標算出→コンテンツ生成→保存→インデックス更新→コミット）|
| `docs/reports/daily/index.md` | 新規作成（日報インデックス）|
| `docs/reports/weekly/index.md` | 新規作成（週報インデックス）|
| `docs/reports/monthly/index.md` | 新規作成（月報インデックス）|
| `.claude/settings.json` | `gws sheets spreadsheets values get *` を `permissions.allow` に追加 |

## 設計判断

- **データ取得は gws CLI + Python インライン処理**：CLAUDE.md の「Google サービス連携は gws CLI 統一」ルールに従い、gws CLI で JSON を取得し Python で日付フィルタ・集計を行う方式にした
- **Xクリエイター収益は常に空欄**：X API に収益取得エンドポイントがないため、月報の該当フィールドは `（未記入）` で固定し、ユーザーが手動記入する運用とした
- **来週タスクは前月報から逆算**：週報の「来週タスク」は直近の月報「次月への改善」セクションを参照して月次目標から逆算する設計にした

## 確認結果

スキルが `/reporter-daily`, `/reporter-weekly`, `/reporter-monthly` で呼び出せることを確認。
