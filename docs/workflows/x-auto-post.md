---
title: X 自動投稿フロー
description: cron → Gmail → X 投稿 の自動化フロー解説
---

## フロー全体図

```
毎朝 6:00 cron
    ↓
daily-xonepoint エージェント起動
    ↓
ネタ選定 → 原稿作成 → ファクトチェック
    ↓
outputs/drafts/ に保存 + git push
    ↓
Gmail 下書き作成（scripts/create_gmail_draft.sh）
    ↓
ユーザーがメールを確認・承認
    ↓
【ワンポイント解説】件名のメールを送信
    ↓
x-post-from-email エージェント
    ↓
[投稿文] タグを抽出 → X に投稿
```

## cron 設定

```bash
# /etc/cron.d/ または crontab
0 6 * * * /path/to/scripts/run_xonepoint_post.sh
```

## Gmail → X 投稿の仕組み

`scripts/post_from_email.sh` が定期実行され、「【ワンポイント解説】」で始まる未読メールを検索し、本文の `[投稿文]...[/投稿文]` タグ内のテキストを抽出して X に投稿する。

```bash
bash scripts/post_from_email.sh \
  "【ワンポイント解説】" \
  W003 \
  x_post_xonepoint.log
```

## 投稿済み判定

投稿後、対象メールに `W003`（投稿済みラベル）を付与する。次回実行時にラベル付きメールはスキップされる。
