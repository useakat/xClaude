---
title: GetRepliesAndQuotes GAS スクリプト新設
date: 2026-05-21
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

リプライ・引用RTをしたアカウントを把握し、反応者分析や交流施策に活用するため。X API の制約上、メンション API（直近7日分）と quote_tweets API（任意投稿ごと）を組み合わせることで、リプライと引用RT を網羅的に収集する仕組みが必要だった。

## 実施内容

- `gas/GetRepliesAndQuotes.js` を新設
  - メンション API からセルフリプを除外したリプライを取得
  - 自分の投稿ごとに `quote_tweets` API を呼び出して引用RTを収集（`url:` 検索演算子は quote attachment URL に一致しないため使用不可と判明し、エンドポイント方式に変更）
  - 重複排除（ポストURL の status ID で照合）して「リプ・引用一覧」シートに追記
- `expansions=author_id` と `user.fields=username,name` を追加し、アカウントID（`@username` 形式）・アカウント名（表示名）を取得してシートに記録
- 列構成: A=投稿日時 / B=アカウントID / C=アカウント名 / D=ポストURL / E=ポスト本文 / F=ポスト種類 / G=親ポストURL
- 毎日 AM 4:00（JST）の自動実行トリガー設定ヘルパー（`setupDailyTrigger` / `deleteDailyTrigger`）を実装

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `gas/GetRepliesAndQuotes.js` | 新規作成（リプライ・引用RT収集 GAS スクリプト） |

## 設計判断

- **引用RT取得に quote_tweets API を使用**: `url:` 検索演算子は引用RTの添付 URL にマッチしないため、自分の投稿IDを列挙して各投稿の `quote_tweets` エンドポイントを個別に呼び出す方式を採用
- **リプライ取得はメンション API**: `in_reply_to_post_id:` による検索は OAuth 1.0a で 403 になるため、メンション API（直近 `DAYS_BACK` 日分）で代替。セルフリプは `author_id` 判定で除外
- **アカウントID は `@username` 形式**: 数値 ID より可読性が高く、X プロフィールへのアクセスに直接使用できるため

## 確認結果

GAS エディタから `updateRepliesAndQuotes` を手動実行し、「リプ・引用一覧」シートに B=`@username`・C=表示名 を含む7列でデータが追記されることを確認。

## 今後の課題

- `DAYS_BACK=2` の重複排除で漏れがないか、長期運用で確認する
- 引用RT取得は自分の投稿数に比例してAPI呼び出し数が増えるため、投稿数が増えた場合はバッチ分割を検討
