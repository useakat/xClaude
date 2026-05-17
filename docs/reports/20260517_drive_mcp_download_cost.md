---
title: Drive MCP download_file_content のトークン・実行時間コスト検証
date: 2026-05-17
tags: [infra, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md)

## 背景

`update-x-analytics` エージェントの高速化リファクタリング後、Drive CSV の取得方法として2つの方式を比較していた。

- **スクリプト方式**：`fetch_x_analytics_csv.py` が Anthropic プロキシに直接 HTTP POST し、base64 デコード・パースまでスクリプト内で完結させる
- **Drive MCP 方式**：エージェントが `download_file_content` を呼び出し、返ってきた base64 を Write ツールでファイルに保存する

「Drive MCP を使う方が保守性が高い」という観点から MCP 方式を試したところ、著しいパフォーマンス差が生じた。その原因を体系的に検証した。

---

## 実験設計

`test-drive-csv-header` エージェントを作成し、処理ステップを段階的に追加しながらトークン消費・ツール呼び出し回数・実行時間を計測した。

対象ファイル：`account_analytics_content_2026-05-04_2026-05-17.csv`（約 24KB、base64 換算 約 32KB）

---

## 実験結果

| 方式 | トークン | ツール呼び出し | 実行時間 |
|---|---|---|---|
| ① ファイル名のみ（search_files） | 17,704 | 2回 | 19秒 |
| ② ダウンロードのみ（download_file_content） | 45,841 | 5回 | 37秒 |
| ③ ダウンロード＋デコード（Bash で Python） | 47,648 | 4回 | 33秒 |
| ④ ダウンロード＋Write＋デコード | 99,839 | 23回 | **1518秒（25分）** |
| ⑤ スクリプト方式（fetch_x_analytics_csv.py） | ～数百（完了メッセージのみ） | 1回 | 数秒 |

---

## 原因分析

### download_file_content が重い理由

`download_file_content` は base64 エンコードされたファイル本体を `tool_result` としてそのまま返す。この tool_result は **必ず LLM コンテキストを通過する**。

```
download_file_content → base64 32KB → tool_result → LLM コンテキストに載る（+約28,000トークン）
```

②と①のトークン差が約 28,000 であることが、24KB CSV の base64（≒ 32,000 文字）がそのままコンテキストに乗っていることの証拠。

### Write ツールで保存すると破綻する理由

Write ツールの呼び出しには `content` パラメータとして base64 文字列を LLM が**再度生成**する必要がある。

```
tool_result（download）: base64 32KB → コンテキストに載る
         ↓
tool_use（Write）:       content=<base64 32KB> → コンテキストにもう一度載る（2倍）
```

④では 23 回のツール呼び出しが発生し 25 分かかった。エージェントが base64 の途中でパディングずれを起こして迷走したためで、大きなバイナリデータを LLM 経由で扱うことの構造的な問題が顕在化した。

### スクリプト方式が速い理由

```
LLM → Bash("python3 fetch_x_analytics_csv.py")
         ↓
      スクリプトが MCP プロキシに直接 HTTP POST
         ↓
      base64 → Python メモリ → デコード → /tmp/x_analytics_map.json
         ↓（LLM を一切通らない）
LLM ← "✅ 保存しました（76件）"（数十バイト）
```

LLM に返るのは小さい完了メッセージのみ。base64 はスクリプトのメモリ内で完結するため、コンテキストへの影響はゼロ。

### 自動ディスク保存機能について

Claude Code にはツール出力が 25,000 トークンを超えた場合にディスクへ自動保存してパス参照に置き換える機能があるとされる。しかし、本リモートセッション環境では `tool-results/` ディレクトリが存在せず、この自動最適化は動作していないことを確認した。

また、Drive MCP の `download_file_content` ツール定義（`tools/list`）を直接確認したところ、`_meta["anthropic/maxResultSizeChars"]` アノテーションは設定されておらず、意図的なバイパスも行われていなかった。

---

## read_file_content との違い

| | `download_file_content` | `read_file_content` |
|---|---|---|
| 返す形式 | base64 エンコードされたバイナリ | 自然言語テキスト |
| 大きいファイル | フル取得（重い） | 自動で切り詰め |
| 対応形式 | 全ファイル | Google Docs / PDF / 画像など限定 |
| CSV | 対応 | **非対応** |

CSV は `read_file_content` の対応形式外のため、`download_file_content` しか選択肢がなかった。これが重さの根本原因。

---

## 結論

**Drive MCP は「ファイルを探す・メタデータを取る・内容を LLM に把握させる（小さいファイル限定）」にはよいが、「ファイル本体を LLM 経由でダウンロードして保存する」用途には向いていない。実ファイルを扱うなら LLM 文脈を経由せずディスクへ直接落とす経路を使うべき。**

具体的には：

| 用途 | 推奨手段 |
|---|---|
| ファイル名・更新日時の取得 | Drive MCP `search_files` |
| ファイル内容を LLM に理解させる（小さいファイル） | Drive MCP `read_file_content` |
| ファイル本体をディスクに保存する | スクリプトが MCP プロキシに直接 HTTP POST |

---

## 適用した対策

`update-x-analytics` エージェントの Drive CSV 取得を `fetch_x_analytics_csv.py`（スクリプト方式）に戻した。これにより実行時間 302秒→46秒・ツール呼び出し 10回→4回を維持している。
