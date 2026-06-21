---
title: visual_infographic のスーパーニャンコ参照画像をローカル references/ 画像に変更
date: 2026-06-21
tags: [skill, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260621_visual_infographic_local_nyanko_ref/)

## 背景・動機

`/visual_infographic` は図解生成時に、キャラクター「スーパーニャンコ」の参照画像を NotebookLM のソースに追加して絵柄を安定させている。従来この参照画像は Google Drive 上のファイル（`1SHyiHZ8...`）を `drive_get.sh` でダウンロードしてから追加していた。

この方式は実行時に2つの環境依存で詰まった:

1. **Drive スコープ依存**: gws トークンに `drive` スコープが無いとダウンロードが 403 で失敗する。
2. **`file` コマンド依存**: Drive URL 経由の `add-source-file --url` は MIME 判定に `file --mime-type` を使うため、`file` 未インストール環境では FileNotFoundError になる。

`references/スーパーニャンコアイコン.png` に同一画像（244,983 バイト）がローカルで存在するため、これを `--file` で直接ソース追加すれば、Drive ダウンロードも `file` コマンドも不要になり、両方の詰まりを構造的に解消できる。

## 実施内容

- 共通変数を `NYANKO_URL`（Drive URL）から `NYANKO_REF="$ROOT/references/スーパーニャンコアイコン.png"` に変更。
- **再利用ブランチ**: ソース担保の `add-source-file --url "$NYANKO_URL"` を `add-source-file --file "$NYANKO_REF"` に変更。
- **新規作成ブランチ**: `make-infographic --extra-source-url`（notebook作成＋1枚目生成を兼ねる・Drive DL 経由）をやめ、`create`→`add-text`（原稿）→`add-source-file --file`（参照画像）→`infographic` ループ（全 N 枚）へ再構成。再利用ブランチと参照画像の追加方法・生成ループを統一した。
- 注意事項に「参照画像はローカル `references/スーパーニャンコアイコン.png` を `--file` で追加（Drive DL 不要・`file` コマンド非依存）」を明記。`--keep` 記述を `create` ベースに更新。

スクリプト（`notebooklm_manager.py`）は改変せず、既存サブコマンド（`create` / `add-text` / `add-source-file --file` / `infographic`）の組み合わせのみで実現した。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/visual_infographic/SKILL.md` | 参照画像をローカル `--file` 追加へ変更。新規作成ブランチを create→add→loop に統一。注意事項を更新 |

## 設計判断

- `notebooklm_manager.py` 側に `file` 不在フォールバックを実装する案もあったが、`--file`（ローカル）経路は拡張子から MIME を判定し `file` を使わないため、スクリプト改変なしでスキル定義の変更だけで解決できると判断した。
- 新規作成ブランチを `make-infographic` から `create`＋ループに変えたことで、参照画像を1枚目の生成前に確実にソースへ含められ、両ブランチのコードパスも揃った。

## 確認結果

- `references/スーパーニャンコアイコン.png` の存在とサイズ（244,983 バイト、Drive 版と同一）を確認。
- 変更後の SKILL.md に Drive URL 由来の参照（`NYANKO_URL` / Drive ID / `--extra-source-url` / `make-infographic`）が残っていないことを grep で確認。
- 本セッションで `add-source-file --file references/...` 経由のソース追加→5枚生成→アップロードが成功する経路は実証済み（同方式を手動実行で完走）。

## 今後の課題

- リモート環境（gws 不在）でのアップロード経路は引き続き Drive MCP ツールを使用する想定。参照画像の追加はローカルファイルなので影響なし。
