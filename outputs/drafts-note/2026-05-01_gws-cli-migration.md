# Anthropic MCP から gws CLI へ──Google Workspace 連携を一から作り直した話

Claude Code から Gmail・Drive・Google Sheets を扱うために、最初は Anthropic 公式の Google ワークスペース MCP を使っていた。便利だったが、運用するうちに「これでは無理だ」と気づく場面が次々に出てきた。

最終的に、すべてを Google 公式の CLI ツール **`gws`（googleworkspace/cli）** に置き換えた。スコープの制約から解放され、スクリプトもシンプルになった。同じ移行を考えている人のために、何にハマって何で抜けたかをまとめておく。

## なぜ MCP では足りなかったか

Anthropic が提供している Google MCP は、ブラウザベースの OAuth で簡単に認証できる代わりに、**スコープが固定**されている。

たとえば Gmail MCP は `gmail.readonly` しか持っていない。メールを読むことはできるが、ラベルを付ける（`gmail.modify`）こともアーカイブすることもできない。「メール起点で X 投稿を自動化する」みたいな、読み取った後に処理済みフラグを立てたい用途では致命的だった。

Google Sheets MCP も同様で、`mcp-google-sheets` と `mcp-gsheets` の2系統を試したが、どちらもサービスアカウント前提でユーザー個人の Sheets には触れない。CSV を Sheets に同期するスクリプトとは別系統で動くため、データの実体が二箇所に分散する。

「読み書きできる」と「思った範囲で読み書きできる」の差が大きかった。

---

## gws CLI とは

`gws` は Google が公式に出している Google Workspace 用 CLI で、Drive・Gmail・Calendar・Sheets・Docs など、ほぼすべての API を一つのバイナリから叩ける。Google Discovery Service からコマンド面を動的生成しているので、「gws drive files list」「gws gmail users messages list」のように、API のリソースパスがそのままコマンドになる。

GitHub: `googleworkspace/cli`

ユーザー OAuth で認証すれば、自分のアカウントで好きなスコープを取れる。Claude のセッションから直接呼べるので、MCP サーバーを起動しておく必要もない。

---

## 移行の流れ

1. **gws をインストール**（Linux musl 版を使った。GLIBC 2.39 が要求される gnu 版は古い Ubuntu で動かない）
2. **GCP プロジェクトで OAuth クライアント ID を作成**してデスクトップアプリ用 JSON をダウンロード
3. **`gws auth login` でユーザー OAuth**（リモートサーバーの場合は SSH トンネルでブラウザに飛ばす）
4. **既存スクリプトの MCP 呼び出しを `gws` コマンドに置き換え**

順番としては Gmail → Drive → Sheets で進めた。Gmail はラベル付けの解放が一番の動機だったので最優先。Drive は画像同期、Sheets は CSV 同期で使う。

### Gmail：ラベル付けが一発で動くようになった

```bash
gws gmail users threads modify \
  --params '{"userId": "me", "id": "THREAD_ID"}' \
  --json '{"addLabelIds": ["Label_103"], "removeLabelIds": ["INBOX"]}'
```

「投稿済み」ラベルを付けて受信トレイから外す、という操作が1コマンドで終わる。MCP では絶対にできなかった処理だ。

### Drive：アップロード API が `+upload` ヘルパーで簡潔に

```bash
gws drive +upload /path/to/file.png --parent FOLDER_ID
```

ヘルパーコマンド（先頭に `+`）は、よく使う処理を簡略化したラッパーになっている。生 API を叩く `gws drive files create --upload ...` よりも書く量が半分になる。

### Sheets：clear → update でフルリプレース同期

CSV を Sheets に丸ごと同期する処理は、「シートを全件クリア → CSV の内容で上書き」というパターンで書ける。

```bash
gws sheets spreadsheets values clear \
  --params '{"spreadsheetId": "SS_ID", "range": "シート名"}' \
  --json '{}'

gws sheets spreadsheets values update \
  --params '{"spreadsheetId": "SS_ID", "range": "シート名", "valueInputOption": "RAW"}' \
  --json '{"values": [["a","b"],["c","d"]]}'
```

これで gspread+サービスアカウントでやっていた処理が、追加ライブラリなしの bash + Python（標準ライブラリのみ）で書けるようになった。

---

## 詰まったポイント：「Sheets だけ全部 404」

Sheets 移行中に、不可解な現象に遭遇した。

- `gws sheets +read`（ヘルパー）→ ✅ 動く
- `gws sheets +append`（ヘルパー）→ ✅ 動く
- `gws sheets spreadsheets values get/clear/update`（直接 API）→ ❌ すべて 404 エラー

同じスプレッドシートを同じ URL で叩いているのに、ヘルパーは動いて直接 API は動かない。Drive と Gmail の直接 API は普通に動く。Sheets だけが直接 API で全部 404。

#### 原因

gws は認証情報を二箇所に保存している。

- `~/.config/gws/credentials.json`（平文）
- `~/.config/gws/credentials.enc`（暗号化）

`gws auth login` を実行したとき、新しいスコープ（Sheets）は `credentials.enc` には保存されたが、以前から残っていた `credentials.json` のリフレッシュトークンは古いスコープ（Gmail のみ）のままだった。

そして gws の直接 API コマンドは、`credentials.json` が存在するとそちらを優先して使う仕様になっていた。Gmail スコープしかないトークンで Sheets API を叩くと、Google は「権限がない」ではなく **「リソースが存在しない」（404）** を返す。情報漏洩を防ぐための仕様らしい。

ヘルパーコマンドは別経路で `credentials.enc` を見にいくので、こちらは Sheets スコープを持ったトークンで動いていた。

#### 解決

`credentials.json` を削除するだけ。これで gws は `credentials.enc`（フルスコープ）にフォールバックして、直接 API も動くようになった。

```bash
rm ~/.config/gws/credentials.json
rm ~/.config/gws/token_cache.json
```

スコープを足すたびにこのファイルが古くなる可能性があるので、`gws auth login` 後は意識的に削除するのが安全。

---

## 移行して何が変わったか

- **MCP サーバー定義が消えた**：`mcp-google-sheets`, `mcp-gsheets` の2行を `settings.json` から削除しただけで、依存関係が一気に減った
- **権限境界が自分のアカウントで揃った**：サービスアカウントとユーザーアカウントの権限差を意識する必要がなくなった
- **API ドキュメントが直接活きる**：Google 公式リファレンスのリソースパス・パラメータをそのまま `--params` に書ける
- **CLI なのでログが残せて再現性が高い**：MCP のブラックボックス感がない

「Anthropic がラップしてくれている便利なやつ」より、「Google が公式で出している素のやつ」のほうが結果的に扱いやすい場面はある、という当たり前の学びを得た。MCP は導入の敷居が低い反面、踏み込むと天井が低い。`gws` は最初の認証だけ少し面倒だが、踏み込んでも天井がない。

最終的に、Gmail のラベル運用も、Drive の画像同期も、Sheets の CSV 同期も、「同じ CLI を叩く」というシンプルな構図に揃った。日々の運用がだいぶ静かになった。

---

## 参考情報

- googleworkspace/cli: GitHub リポジトリ `googleworkspace/cli`
- Google Sheets API リファレンス: developers.google.com/workspace/sheets/api
- Google Drive API リファレンス: developers.google.com/workspace/drive/api
- Gmail API リファレンス: developers.google.com/workspace/gmail/api
