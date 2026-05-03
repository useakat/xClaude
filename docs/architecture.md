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
├── database/            参照用アーカイブ（読み取り専用・更新不要）
├── unused-scripts/      廃止済みスクリプト（アーカイブ）
├── scripts/             自動化スクリプト群（Gmail/Drive は gws CLI 経由）
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
    ├── mcp-gsheets ──→ Google Sheets（SS1/SS2）← 唯一の正データ
    │
    └── scripts/（bash/Python）
            ↓
        gws CLI
            ├── Gmail（下書き作成・送信）
            └── Drive（ファイル同期）
                            ↓
                    outputs/（原稿）→ X 投稿
```

## 設計原則

**データベースの実体は Google Sheets**
`database/*.csv` は参照用アーカイブで更新不要。Sheets が唯一の正データ。スキルは mcp-gsheets ツールを直接呼び出して読み書きする。

**Google サービス連携**
- Sheets: mcp-gsheets MCP ツール（`sheets_get_values` / `sheets_append_values` / `sheets_update_values`）
- Gmail・Drive: `gws` CLI（シェルスクリプト経由）

**スクリプト化優先**
データ I/O・API 呼び出し・git 操作など繰り返し実行する処理はスクリプト化する。Claude はコンテンツ生成と判断に集中する。

## 認証

| サービス | 認証方式 | 設定場所 |
|---|---|---|
| Gmail / Drive | gws CLI トークン | `~/.config/gws/` |
| Google Sheets | サービスアカウント鍵 | `.mcp.json` → `gcp/*.json` |

mcp-gsheets の認証は `.mcp.json` で設定する。ローカルセッションは `GOOGLE_APPLICATION_CREDENTIALS`（ファイルパス）、クラウドセッションは `GOOGLE_SERVICE_ACCOUNT_KEY`（JSON 文字列）。
