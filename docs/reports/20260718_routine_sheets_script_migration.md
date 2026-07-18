---
title: routine の Sheets 読み取りをサービスアカウント認証スクリプトに移行（リモート許可プロンプト対策の決着）
date: 2026-07-18
tags: [infra, bugfix]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/) ｜ [セッション履歴→](../../history/20260718_routine_sheets_script_migration/)

## 背景・動機

7/18 朝の日報 routine（reporter-daily）で、`sheets_get_values` の実行許可プロンプトが**三たび**表示された。7/15（完全一致5ルールを settings.json に登録）・7/16（settings.local.json を git 配布）・7/17（接続待機スクリプト追加。本報告書に統合）と対策を重ねたが、いずれも効かなかったことになる。

セッション内で徹底調査を行い、以下を確定させた：

- **接続タイミング説（7/17 仮説）の棄却**：MCP 接続ログで mcp-gsheets は 00:53:25 に接続完了。拒否された呼び出しは 00:53:36〜39 で、接続完了の11秒後。7/17 に追加した `wait_mcp_gsheets.sh` は正常動作していたが、プロンプトは出た。
- **設定ファイル不参照の実証**：`settings.json`・`settings.local.json` の両方に完全一致ルールが存在する状態で、テスト呼び出し（1セル読み取り）が発行から結果まで34秒かかった（自動許可なら1秒未満。手動 Allow 待ちの時間）。**リモート（managed）環境では、リポジトリ内のどの設定ファイルの MCP ツール許可ルールも参照されない**。
- **7/16 の切り分けテストの交絡**：「settings.local.json なら効く」の根拠は Always allow クリック後の無プロンプト動作だったが、クリックは「ファイル書き込み」と「セッション内承認」の両方を行う。効いていたのはセッション内承認で、git 配布したファイル単体では効かない（7/17・7/18 と新品コンテナで2日連続実証）。
- **「6月は動いていた」の説明**：日報 routine は5月上旬からリモートで運用されていたが、当時の許可ルールは無効形式（`mcp__*`）のみ。それでもプロンプトなしで動いていた＝当時のリモート環境は MCP ツールの許可プロンプト自体を課していなかった。7月中旬からの変化はハーネス側の挙動変更。
- **Web 裏取り**：公式ドキュメント（routines）には「routine 実行中は許可モード選択も承認プロンプトも無い」と明記されており、現在の挙動はドキュメントと矛盾する。同症状は GitHub Issue #61097（2026年5月）で報告済みで、Anthropic メンバーが「対処されるはず」と返答している（コネクタ経路の話だが、Always allow が無視される構図は同じ）。

以上から「リポジトリ側の設定でプロンプトを抑止する」路線は打ち切り、7/16 報告書の案C（構造的対策）である**スクリプト移行**を実施した。gws CLI はユーザー OAuth（ブラウザ認証・ローカル限定）のためリモート無人実行には使えないが、リモート環境には mcp-gsheets が使っているサービスアカウント鍵（`GOOGLE_SERVICE_ACCOUNT_KEY` 環境変数）が既に配布されており、これを直接使う Python スクリプトなら認証もプロンプトも問題にならない（routine の Bash 実行は5月以降プロンプトなしの実績）。

## 実施内容

**7/17 分（接続待機。結果的に本件の根本対策ではなかったが記録として残す）**

- `scripts/wait_mcp_gsheets.sh` 新設：SessionStart hook（リモート限定）で mcp-gsheets サーバープロセスの起動を待ってからセッションを開始させる（TIMEOUT 45秒・検出後バッファ3秒）

**7/18 分（スクリプト移行）**

- `scripts/sheets_values.py` 新設：Sheets 読み書き CLI（`get` / `append` / `update`）。認証は `GOOGLE_SERVICE_ACCOUNT_KEY` 環境変数優先・ローカルでは gcp/ の鍵ファイルにフォールバック（`record_output.py` と同じ方式）。IPv4 固定・依存の自動ブートストラップ付き。出力は JSON
- `scripts/sheets_pydeps_install.sh` 新設：gspread / google-auth / cryptography をバージョン固定で `~/.cache/xclaude-pydeps/` に冪等インストール（`mcp_gsheets_install.sh` と同じマーカー方式）
- `.claude/settings.json`：SessionStart hook にリモート限定の依存事前ウォームを追加。`Bash(python3 *scripts/sheets_values.py *)` を許可リストに追加
- `.claude/skills/reporter-daily/SKILL.md`：Sheets 読み取り7箇所を MCP ツール呼び出しから `sheets_values.py` に置き換え。冒頭に「MCP ツールは使わない」方針を明記
- `CLAUDE.md`：「routine / リモートのシート読み書きは sheets_values.py を使う」例外ルールを追記

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/wait_mcp_gsheets.sh` | 新設（7/17）。mcp-gsheets 接続待機（SessionStart hook 用） |
| `scripts/sheets_values.py` | 新設。Sheets 読み書き CLI（サービスアカウント認証・get/append/update） |
| `scripts/sheets_pydeps_install.sh` | 新設。Python 依存の冪等インストール（バージョン固定・キャッシュ焼き込み対応） |
| `.claude/settings.json` | SessionStart hook 2件追加（接続待機・依存事前ウォーム）＋ sheets_values.py の Bash 許可 |
| `.claude/skills/reporter-daily/SKILL.md` | Sheets 読み取りを全て sheets_values.py 呼び出しに置き換え |
| `CLAUDE.md` | routine / リモートの Sheets アクセス例外ルールを追記 |
| `.gitignore` | 依存インストールログを除外 |

## 設計判断

- **gws CLI 移行案は不採用**：gws はユーザー OAuth（ブラウザ認証）でトークンがローカルにしか無く、リモートの無人実行では認証できない（5/24 報告書の既知制約）。サービスアカウントは鍵だけで認証が完結し無人実行向き。対象シートは mcp-gsheets 用に共有済みなので追加設定も不要
- **mcp-gsheets は廃止しない**：ローカル対話セッションでは従来どおり MCP ツールを使う（CLAUDE.md に使い分けを明記）。将来 Anthropic 側で許可挙動が修正されれば routine も戻せる
- **cryptography を依存に同梱**：リモートコンテナのシステム版 cryptography が壊れており（pyo3 panic）、google-auth がそれを掴んで落ちるため、固定バージョンを同梱してパス先頭で上書きする
- **依存はバージョン固定＋キャッシュディレクトリ方式**：mcp_gsheets_install.sh で実績のあるパターンを踏襲。SessionStart hook（同期実行）でコンテナキャッシュに焼き込まれ、2回目以降は即スキップ

## 確認結果

- リモートコンテナで実測：コールド（依存インストール込み）6.8秒・ウォーム1.7秒で `get` が成功（日次記録シートの実データ取得を確認）
- 許可プロンプトは出ない（Bash 経由のため）
- 明朝（7/19 実行・7/18 分）の日報 routine が新方式の初回実地検証となる

## 今後の課題

- **明朝の日報 routine の完走確認**（プロンプトなしで docs/reports/daily/ まで生成されるか）
- **書き込み系（append / update）の実テスト**：実装済みだが本番シートを汚さないため未実施。書き込みを行う routine / agent（record-note-posts 等）を移行する際にテストする
- **他の routine / スキルの移行**：writer-xshort 等、Sheets を読む routine 系スキルはまだ MCP ツール参照のまま。日報 routine の実績を見てから順次移行する
- **Anthropic 側の修正観測**：Issue #61097 の経過を見て、リモートの許可挙動が修正されたら方針を再検討する
- `wait_mcp_gsheets.sh` は本件の根本対策ではなかったが、接続安定化としては無害なので残置
