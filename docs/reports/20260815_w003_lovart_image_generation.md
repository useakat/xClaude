---
title: W003 の画像生成を NotebookLM から Lovart へ移行
date: 2026-08-15
tags: [skill, workflow, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260815_w003_writer_xpost_migration/)

## 背景・動機

「太陽が明るくなる」投稿の制作でフロー7（画像生成）を実行したところ、spec が指す `/visual_infographic` が実行不能だった。原因は次の2点。

1. `/visual_infographic` は画像生成をすべて `scripts/notebooklm_manager.py` の `infographic` コマンドに依存しているが、この `notebooklm_manager.py` は cookie 認証方式で 2026-08-06 に廃止済み（実行すると `Authentication expired or invalid` で失敗する）
2. 後継のブラウザ内RPCブリッジ（`scripts/notebooklm_browser_bridge.py`）には `list` / `create` / `list-sources` / `delete-source` / `add-source` / `add-text` / `ask` / `deep-research` は移植済みだが、`infographic` サブコマンドは未移植のまま

W001（8/4）・W002（8/9）は既に画像生成を `/lovart` スキル（Lovart AI）へ移行済みで、W003 だけが廃止済みの経路に依存したまま取り残されていた状態だった。

## 実施内容

- W003 の spec.md フロー7を `/lovart` 呼び出しに全面書き換えた。手順は (1) `infographic_template/` の6型（step_flow/compare_contrast/radial/timeline/pyramid/checklist）から内容に合う5型を選びプロンプトを書く、(2) `/lovart` で5枚生成する（実機・実物の形状再現が必要なら参照画像を `upload`→`--attachments`、修正は `--thread-id` で同一スレッド反復）、(3) `draft/infographic_[連番].png`/`.md` のペアで保存、(4) 日本語が崩れる場合は文字数を減らすかテキストを後掛けする、という W001/W002 と同じ型に揃えた
- `/visual_infographic` は使わない旨と、その理由（cookie認証廃止・ブリッジ未移植）を spec に明記した
- 実運用で5パターンを生成。うち1パターン（timeline型）はテンプレートのラベル記法（「メインタイトル：」等）をそのまま画像内に描画してしまう不具合が発生し、ラベル語を描かない旨を明示して再生成し解消した
- ユーザー指摘により、もう1パターン（step_flow型）のステップ③に物理的な誤りが見つかった。「地球がハビタブルゾーンの外側に取り残される」という誤った位置関係で描かれていたが、正しくは「太陽が明るくなるとゾーンの内側の縁が地球を追い越して外側へ動き、地球はゾーンより内側（太陽に近い側）に取り残される」であり、プロンプトの文言修正（位置関係の明示的な訂正指示を追加）と再生成で対応した

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/w003/spec.md` | フロー7を `/lovart` 呼び出しに全面書き換え。`/visual_infographic` を使わない理由を明記 |

## 確認結果

「太陽が明るくなる」投稿で実運用し、以下を確認した。

- 参照画像（スーパーニャンコアイコン）のアップロードから5パターンの生成まで完走し、日本語テキストが崩れずに描画されることを確認
- ラベル記法の混入不具合を検出・修正し、再生成で解消を確認
- ユーザー指摘によるstep_flow型の位置関係誤りを修正し、3案の再生成すべてで正しい位置関係（地球がゾーンの内側・太陽寄りに取り残される）が描かれることを確認
- 採用した timeline 型（`infographic_04.png`）を `output/` に確定し、Gmail 下書き作成・Drive アップロードまで完走

## 今後の課題

- `infographic_template/` の型テンプレートはビジュアル指示（スーパーニャンコの容姿・配色等）が6ファイルすべてで重複しており、共通化の余地がある（今回は移行のスコープ外として手を付けていない）
- ブリッジへの `infographic` サブコマンド移植は依然未着手。今後 NotebookLM 側の図解生成が必要になった場合は改めて検討する
