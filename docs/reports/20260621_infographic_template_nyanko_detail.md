---
title: infographic_template 6型をスーパーニャンコ詳細定義に更新
date: 2026-06-21
tags: [style, infra]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260621_infographic_template_nyanko_detail/)

## 背景・動機

W003（X ワンポイント解説）のインフォグラフィックは `projects/w003/infographic_template/` の6型テンプレートを基に `/visual_infographic` がプロンプトを生成する。従来テンプレートのキャラクター指定は「額に赤いハート、卒業帽、赤いマントの青いネコ」という簡略版で、生成画像ごとにスーパーニャンコの細部（耳の内側・チーク・W字口・タッセル・ベルトのバックル等）がぶれていた。よーんから提供されたスーパーニャンコの詳細定義を全テンプレートに統一適用し、見た目の一貫性を担保する。

あわせて、図解生成の実行時に判明した2つの環境的な詰まりを解消した。

## 実施内容

- `infographic_template/` の6型すべて（`radial` / `checklist` / `compare_contrast` / `pyramid` / `step_flow` / `timeline`）の「キャラクター指定」行を、簡略版から詳細版へ差し替え。
  - 詳細版に含めた要素: 鮮やかな青の体／耳は青・内側は明るい黄／顔は明るい黄・額の赤いハート／細い黒線のW字口／両頬のオレンジのチーク／黒い卒業角帽＋右に黄色いタッセル／首元で結ぶ赤いマント／赤いベルト＋中央に黄色い正方形バックル／ぬいぐるみの質感。
- **gws を Drive スコープ付きで再認証**: 図解の参照画像DLとアップロードに必要な `https://www.googleapis.com/auth/drive` が欠けていた（403 insufficient scopes）。従来6スコープを保持したまま drive を追加。`scripts/gws_auth.sh` でブラウザ認証を実施。
- **`file` コマンドを導入**: `notebooklm_manager.py` が Drive URL 由来の画像ソース追加時に `file --mime-type` で拡張子を判定するが、環境に未インストールだった（FileNotFoundError）。`apt-get install -y file` で導入。今回の実行は参照画像をローカル `.png` でDLし `--file` 経路（拡張子判定）で回避したが、恒久対策として導入した。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `projects/w003/infographic_template/radial.md` | キャラクター指定をスーパーニャンコ詳細版へ差し替え |
| `projects/w003/infographic_template/checklist.md` | 同上 |
| `projects/w003/infographic_template/compare_contrast.md` | 同上 |
| `projects/w003/infographic_template/pyramid.md` | 同上 |
| `projects/w003/infographic_template/step_flow.md` | 同上 |
| `projects/w003/infographic_template/timeline.md` | 同上 |

（gws 再認証は `~/.config/gws/` のトークン更新、`file` 導入はシステムパッケージのためリポジトリ差分はなし）

## 確認結果

- 更新後のテンプレートを基に `/visual_infographic` で5枚（compare_contrast / radial / pyramid / checklist / step_flow）を生成し、スーパーニャンコ参照画像をソースに含めた状態で全枚 Drive アップロードまで成功。
- gws: `gws auth status` で drive を含む7スコープを確認。`gws drive files get` で参照画像メタデータ取得に成功。
- `file`: `/usr/bin/file`（file-5.46）導入、`file --mime-type -b <png>` が `image/png` を返すことを確認。

## 今後の課題（任意）

- `file` 未導入環境（リモート/別ホスト）でも動くよう、`notebooklm_manager.py` 側で `file` 不在時に `mimetypes`/`python-magic` へフォールバックする余地がある（今回はスクリプト改変を避け環境導入で対応）。
