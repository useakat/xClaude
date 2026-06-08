# CLAUDE.md — {project description} プロジェクト

## 起動時のルール

**このフォルダで作業を始める前に必ず `spec.md` を Read すること。**
`spec.md` には、このプロジェクトの制作仕様（媒体・入力・出力・フォーマット・制作フロー）が定義されている。

## リサーチ運用ルール

調べ物をするときは、次の順序で行う。

1. **まず notebook のソースに当たる** — `notebook-id.md` の notebook に NotebookLM で問い合わせる。数値・仕組みなど精密な事実は、該当ソースを WebFetch で原文確認する。
2. **分からなければ WebSearch / WebFetch** で調べる。
3. **新たに信頼できるソースが見つかったら notebook に追加する** — 関連性・信頼度の基準を満たすものに限る。**追加前に既存ソース一覧を確認し、重複を作らない**（重複確認は `client.sources.list(notebook_id)` で可能）。
