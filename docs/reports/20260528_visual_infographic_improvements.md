---
title: "visual_infographic 改善: 即アップロード方式・スーパーニャンコ参照・notebooklm_manager 修正"
date: 2026-05-28
tags: [skill, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../history/20260528_visual_infographic_improvements_session/)

## 背景・動機

`/visual_infographic` スキルの運用中に以下の問題と改善要件が発生した。

1. **スーパーニャンコ参照画像が生成に反映されない** — 参照画像を `--extra-source-url` に渡していたが、Drive URL を `add_website` で登録していたため画像として認識されず、生成画像にスーパーニャンコが描かれないケースがあった。
2. **Drive 画像ソースで 400 エラー** — `add_file` で Drive 画像を登録する際に拡張子を付与しようとして 400 エラーが発生していた。
3. **全枚数生成完了後にまとめてアップロード** — 生成中に途中でエラーが起きると、完了分もアップロードされずに終わるリスクがあった。
4. **中心放射型レイアウトのバブル配置に規則がなかった** — 読者の視線を意識した配置ルールが未定義で、情報の流れがバラバラになりがちだった。

## 実施内容

### 中心放射型の視線フロー・スーパーニャンコ参照画像対応（commit 7cb9d9b）
- SKILL.md の中心放射型パターンの説明に「読者の視線が左上→左下→右上→右下と流れるよう設計する（導入→問題→解決の鍵→結論の順）」のルールを追加
- スーパーニャンコ参照画像を `--extra-source-url "$NYANKO_URL"` でノートブックのソースに追加する手順を SKILL.md に明記
- `notebooklm_manager.py` の `make-infographic` コマンドに `--extra-source-url` オプションを実装（Drive URL を `add_file` で登録）
- `drive_put.sh` の関連整備

### 1枚生成ごとに Drive へ即アップロードする方式に変更（commit 78bb4bc）
- SKILL.md の Step 5 を「全枚数まとめてアップロード」から「1枚生成完了後すぐにアップロード→ローカル削除」のポリシーに変更
- `upload_pair()` ヘルパー関数を定義し、PNG と MD をセットでアップロード後にローカル削除する処理を整理
- Drive URL を `PNG_URLS` / `MD_URLS` 配列に蓄積し、最後の Gmail 通知で一括列挙する構造に変更

### notebooklm_manager: Drive 画像ソースの add_file 切替と拡張子付与バグ修正（commits 9a649f6・4265414）
- `--extra-source-url` で渡した Drive URL の登録先を `add_website` → `add_file` に変更（画像として正しく認識させるため）
- Drive 画像ソースに拡張子を付与しようとして発生していた 400 エラーを修正（拡張子付与処理を削除）
- `drive_get.sh` の関連修正

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `.claude/skills/visual_infographic/SKILL.md` | 中心放射型視線フロールール追加・スーパーニャンコ参照画像手順明記・即アップロード方式への変更 |
| `scripts/notebooklm_manager.py` | `--extra-source-url` オプション追加・Drive URL を `add_file` で登録・400 エラー修正 |
| `scripts/drive_get.sh` | notebooklm_manager との連携修正 |
| `scripts/drive_put.sh` | 関連整備 |

## 設計判断

- **即アップロード方式**: 生成中断時のリスクを減らすため、1枚完成ごとに Drive 保存する方式を採用。ローカルに PNG が残り続けないためディスク管理も簡潔になる。
- **`add_file` 採用**: Drive 上の画像ファイルを NotebookLM のソースとして登録する場合は `add_website` ではなく `add_file` が正しい API エンドポイント。

## 確認結果

修正後の `/visual_infographic` スキルで「オリンポス山」「皮膚細胞」テキストを各3枚・追加3枚（計12枚）生成し、以下を確認：
- スーパーニャンコが生成画像に描画される
- 1枚生成完了ごとに Drive アップロード＋ローカル削除が実行される
- 全枚数完了後に Gmail 通知が届く
- 400 エラーが発生しない
