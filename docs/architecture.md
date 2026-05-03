---
title: アーキテクチャ
description: xClaude プロジェクトの全体構造とコンポーネントの役割
---

## フォルダ構成

```
xClaude/
├── .claude/
│   ├── skills/          Claude スキル定義（/skill-name で呼び出す）
│   ├── agents/          自律エージェント定義
│   ├── settings.json    チーム共通設定（権限・MCP サーバー）
│   └── settings.local.json  個人ローカル設定
│
├── database/            CSV データベース（Google Sheets の実体）
├── scripts/             自動化スクリプト群
├── style/               文体・口調スタイル定義
├── outputs/             生成成果物
├── docs/                このドキュメント（Wiki）
├── starlight/           Wiki ビルド設定（Starlight）
└── logs/                実行ログ
```

## コンポーネントの関係

```
ユーザー / cron
    ↓
Claude Code（スキル実行）
    ↓
scripts/（bash/Python）  ←→  Google Workspace（gws CLI）
    ↓
database/（CSV）  ←→  Google Sheets
    ↓
outputs/（原稿）  →  Gmail 下書き / X 投稿
```

## 設計原則

**Google サービス連携**
Gmail・Drive の連携は `gws` CLI（シェルスクリプト経由）で実装する。Sheets の読み書きは mcp-gsheets MCP ツール（`sheets_get_values` / `sheets_append_values` / `sheets_update_values`）を使う。

**スクリプト化優先**
データ I/O・API 呼び出し・git 操作など繰り返し実行する処理はスクリプト化する。Claude はコンテンツ生成と判断に集中する。

**データベースの実体は Google Sheets**
`database/*.csv` は参照用アーカイブで更新不要。Sheets が唯一の正データ。

## 認証

外部サービスの認証は `~/.config/gws/` に統一されている。`gcp/` 配下のトークン類は `scripts/sync_to_drive.py` のみが使用する。
