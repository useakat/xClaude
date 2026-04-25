# sync-to-sheets

`database/` の CSV ファイルを Google Sheets に同期する。

## 実行コマンド

```bash
uv run $(git rev-parse --show-toplevel)/scripts/sync_to_sheets.py
```

## 認証の準備（初回のみ）

以下のいずれかが必要：

**方法A: 環境変数（推奨）**
`.env` に以下を追加：
```
GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT=（GCPサービスアカウントJSONの内容をそのまま）
```

**方法B: GCPファイル**
`gcp/charming-well-464402-u4-a7fefbac9372.json` をプロジェクトルートに配置。

## 同期対象

| CSVファイル | Sheetsシート名 |
|------------|--------------|
| `database/onePointNeta.csv` | onePointNeta |
| `database/noteNeta.csv` | noteNeta |
| `database/newsTopics.csv` | newsTopics |

シートの内容を全件クリアしてCSVの内容で上書きする（一方向同期）。
