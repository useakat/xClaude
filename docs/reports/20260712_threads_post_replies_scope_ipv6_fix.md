---
title: Threads 自動投稿の不具合修正（threads_manage_replies 再認証＋record_output の IPv6 ハング解消）
date: 2026-07-12
tags: [bugfix, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260712_threads_post_replies_scope_ipv6_fix/)

## 背景・動機

前日構築した【threads投稿】cron の初回実行（07-12 07:00）で、①500字超の分割・返信チェーン投稿ができない ②outputs シートへの記録がない ③「投稿済み」ラベル付与＋アーカイブがされない、の3症状が発生した。原因を調査し修正した。

## 原因（2つ）

### (a) 返信作成権限 `threads_manage_replies` の不足（症状①③の根本）
- ログ: 本文1/2 は投稿成功、本文2/2（`reply_to_id` 付き返信）で `code 10: "Application does not have permission for this action"`。
- 権限プローブで確定: `threads_publishing_limit?fields=quota_usage`（通常投稿系）は成功、`fields=reply_quota_usage`（返信系）は同じ code 10。
- 現行トークン（`threads_basic, threads_content_publish, threads_manage_insights`）に**返信作成に必要な `threads_manage_replies` が無かった**（計画時に「返信も content_publish で可」と誤認）。
- 症状③は①の連鎖（投稿失敗で exit 1 → ラベル/記録工程に未到達）。

### (b) record_output.py の IPv6 接続ハング（症状②の根本）
- 再認証後の再テストで投稿・ラベルは成功したが、`record_output.py` が 60 秒超ハング → ラッパーの timeout(300s) で kill（exit 124）され outputs 未記録。
- 切り分け: gws ラベル付与 0.8 秒 / record_output 60 秒超。`sheets.googleapis.com` 等が **AAAA（IPv6）のみで解決**され、この VPS は IPv6 不通のため gspread の接続がハング（graph.threads.net で起きたのと同種）。当日 06:00 の z01 記録が通っていたのは接続順の運＝**間欠性**で、X 系 cron にも同じリスクがあった。

## 実施内容

1. **暫定対処**: 対象メールに「投稿済み」ラベルを付与し、修正前の cron 重複投稿を防止（後に解除して再テスト）。
2. **再々認証**: Meta アプリに `threads_manage_replies` を追加し、`scope=threads_basic,threads_content_publish,threads_manage_replies,threads_manage_insights` で認可→交換（認可コード失効対策として認可→ `--code` 即時交換の手順）。`reply_quota_usage` プローブ成功（0/1000）で権限を確認。
3. **record_output.py に IPv4 固定パッチ**: `socket.getaddrinfo` を IPv4 優先に差し替え（threads 系スクリプトと同じ3行）。
4. **再テスト**: `run_threads_post.sh` 実行 → 本文2件＋リプ1件の分割スレッド投稿成功 → ラベル/アーカイブ成功 → （修正後）record_output 1.6 秒で成功。欠損していた outputs 行も実 permalink で補完。
5. 孤児投稿（初回失敗時に本文1のみ公開されたもの）はユーザーが Threads アプリで手動削除。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/record_output.py` | IPv4 固定パッチ（`socket.getaddrinfo` を IPv4 優先化）を追加 |
| `gcp/threads_token.json`（gitignore） | `threads_manage_replies` 付き長期トークンに更新 |

## 確認結果

- 分割スレッド投稿: 本文2件＋リプ1件が正しく返信チェーンで投稿（permalink 取得）。
- ラベル/アーカイブ: `投稿済み` 付与＋INBOX 解除を確認。
- outputs 記録: IPv4 修正後 1.6 秒で記録成功（`['2026-07-12 10:33:55', permalink, 'threads']`）。
- `reply_quota_usage` プローブ成功（返信権限あり）。

## 教訓・今後の課題

- **Threads の返信作成（reply_to_id）には `threads_manage_replies` が必要**（content_publish だけでは不可）。スコープ変更時は再認証が必要。
- **この VPS は IPv6 不通**で、googleapis / graph.threads.net など AAAA 優先解決のホストで python の接続が間欠的にハングする。**googleapis を直接叩く python スクリプトには IPv4 固定パッチを標準装備**するのが安全（今回 record_output.py に適用。他の gspread/googleapis 利用スクリプトは症状が出たら同パッチ）。
- 部分失敗時（スレッド途中で失敗）の孤児投稿は手動削除運用。自動リカバリは未実装（必要になったら検討）。
