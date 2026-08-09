---
title: NotebookLM ブラウザ内RPCブリッジに ask（ノートへの質問）を追加
date: 2026-08-09
tags: [infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260809_notebooklm_bridge_ask_command/)

## 背景・動機

[2026-08-06 の復旧](../20260806_notebooklm_browser_rpc_recovery/)で NotebookLM は使えるようになったが、実装したのは Deep Research を通す最小構成（`list` / `create` / `deep-research` / `list-sources`）だけで、**`ask`（集めたソースに基づく質問応答）は旧方式のまま**＝使えない状態だった。

W003 のクジラ投稿の制作中、Deep Research で 64 件のソースを集めた直後に「このソース群からトリビア候補を挙げさせたい」「『もっと強い心臓にすれば大きくなれるのでは？』という読者の素朴な疑問に、ソースに基づいて答えさせたい」という場面が出た。ここが空いていると、せっかく集めた一次情報が使えず Web 検索に戻ることになる。制作フロー（`research_trivia-source` の Step 4〜5）も `ask` 前提で書かれているため、埋めておく価値が高いと判断した。

## 実施内容

**通信経路の違いへの対応が要点だった。**
`ask` 以外の RPC はすべて `batchexecute` を叩くが、`ChatAPI.ask` だけは `GenerateFreeFormStreamed` という別エンドポイントを、`_core.rpc_call` を経由せず **`_core.get_http_client()` から直接** POST している。そのため `rpc_call` を差し替えただけでは通らない。

- `_FakeResponse` / `_FakeHttpClient` を追加し、httpx の最小互換（`post()` / `text` / `status_code` / `raise_for_status()`）を実装。ChatAPI が直接使う HTTP 層もブリッジ経由に委譲した。
- vendor 内の URL は旧ドメイン `notebooklm.google.com` にハードコードされている。ブラウザのページは新ドメイン `notebook.google.com` で動いているため、そのまま fetch すると別オリジンとなり CORS で失敗する（8/6 のプローブで実測済み）。`_FakeHttpClient.post()` で**新ドメインへ書き換え**てから送るようにした。
- `ChatAPI` が要求する補助（会話キャッシュ `get_cached_conversation` / `cache_conversation_turn` / `clear_conversation_cache`、`get_source_ids`）を `BridgeCore` に実装。`get_source_ids` は `SourcesAPI` を再利用してノート内の全ソースIDを返す（**async メソッド**である点に注意。同期で実装して `TypeError: object list can't be used in 'await' expression` を踏んだ）。
- 長文の質問を渡せるよう `ask <notebook_id> -` で標準入力から読む形に対応した（プロンプトが数十行になるため）。
- 出力は回答本文のみ（`result.answer`）。references まで出すと数百KB〜MBになりコンテキストを圧迫するため、既存 `notebooklm_manager.py` と同じ方針を踏襲した。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/notebooklm_browser_bridge.py` | `ask` サブコマンドを追加（+77行）。`_FakeResponse` / `_FakeHttpClient` 新設、`OLD_ORIGIN` の新ドメイン書き換え、`BridgeCore` に会話キャッシュと `get_source_ids`（async）を実装 |

## 設計判断

**なぜ ChatAPI を自前実装せず、HTTP 層だけ差し替えたか**
`ask` の応答はストリーミング形式で、本文・引用参照・会話IDの抽出（`_parse_ask_response_with_references`）が複雑。移植するとバグの温床になるため、8/6 と同じ方針で**通信層だけを差し替えて vendor の解析コードをそのまま使う**構成にした。結果、追加は 77 行で済んでいる。

## 確認結果

クジラの心拍のノート（`0d0a026a-…`／Deep Research で収集したソース64件）で実行：

- ソース群からのトリビア候補の抽出（4件。PNAS 原論文・Guinness・Royal Ontario Museum など出典付き）
- 「もっと強い心臓にすれば大きくなれるのでは？」への回答（アロメトリー則、心臓を大きくすると充填時間が短縮できず速く打てなくなる制約、浮上時心拍が理論上限 33〜37 bpm にほぼ一致、など。**ソースにある事実と研究チームの仮説を切り分けた回答**が返った）
- 心拍出量（1回拍出量・毎分の血液量）の数値確認。ソースに直接記載のない値は「計算値」と明示して返答された

いずれもヘッドレス＋ssh で完走。この回答を根拠に投稿本文のファクトを修正できた（誤って「心臓が限界だから大きくなれない」を締めに使っていた箇所の是正、および潜水中の心拍を「通常4〜8回／最低2回」と正確に書き分け）。

## 今後の課題

- 残る未移植は `add-source` / `add-text` / `infographic` など。画像生成は lovart に移行済みのため急がないが、必要になれば同じ要領で追加できる。
- 実行前に Windows 側で Chrome が別途起動していると、プロファイルのロックでブリッジ起動に失敗する。今回は `taskkill /IM chrome.exe /F` で解消した。頻発するようならブリッジ側に自動解放を入れる。
