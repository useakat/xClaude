# sync-to-sheets

`database/` の CSV ファイルを Google Sheets に同期する（gws CLI 使用）。

## 実行コマンド

```bash
bash $(git rev-parse --show-toplevel)/scripts/sync_to_sheets.sh
```

## 同期対象

**スプレッドシート① `1zCT0Kv0Q0qr83c6e_jQxUJeUQ1Y8iz0Zlm_0U5RMaEM`**

| CSVファイル | Sheetsシート名 |
|------------|--------------|
| `database/onePointNeta.csv` | onePointNeta |
| `database/noteNeta.csv` | noteNeta |
| `database/newsTopics.csv` | newsTopics |

**スプレッドシート② `1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc`**

| CSVファイル | Sheetsシート名 |
|------------|--------------|
| `database/persona.csv` | persona |
| `database/pain.csv` | pain |
| `database/what.csv` | what |

各シートを `values clear` で全件クリアし、CSV の内容で `values update`（一方向同期）。

## 認証

gws の OAuth 認証（`https://www.googleapis.com/auth/spreadsheets` スコープ必須）。
スプレッドシートは認証ユーザー（useakat@gmail.com）と共有されている必要がある。

## 注意

`~/.config/gws/credentials.json`（旧スコープのみの平文認証情報）が存在すると、gws の直接 API がそれを優先して使い 404 エラーになる。
存在する場合は削除すること。gws は `credentials.enc`（暗号化、フルスコープ）にフォールバックする。

## 完了後の報告

スクリプトの出力をそのまま報告する。
