---
title: daily-xonepoint
description: X ワンポイント投稿の全工程を全自動実行するスキル
---

## 概要

ネタ選定から Gmail 下書き作成まで、ユーザー入力なしで全工程を自動実行する。  
毎朝 6:00 に cron で自動起動される。

## 実行ステップ

| STEP | 内容 |
|---|---|
| 1 | ネタ在庫確認（10件未満なら自動補充） |
| 2 | ネタ選定 → 投稿原稿作成 |
| 3 | `/check-fact` でファクトチェック |
| 4 | `outputs/drafts/` にファイル保存 → git push |
| 5 | Gmail 下書き作成（`scripts/create_gmail_draft.sh` 経由） |
| 6 | ユーザー承認後にインフォグラフィック生成（手動） |

## STEP 5 の仕組み

gws CLI ベースのスクリプトで Gmail 下書きを作成する。

```bash
bash scripts/create_gmail_draft.sh \
  --to useakat@gmail.com \
  --subject "【ワンポイント解説】YYYYMMDD HH:MM:SS の原稿ができました" \
  --body-file "<一時ファイルパス>"
```

## 関連ファイル

- `.claude/skills/daily-xonepoint/SKILL.md` — スキル定義
- `.claude/agents/daily-xonepoint.md` — エージェント定義
- `scripts/create_gmail_draft.sh` — Gmail 下書き作成スクリプト
