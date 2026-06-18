---
title: mcp-gsheets 認証修正・record-note-posts cron 追加 — セッション履歴
date: 2026-06-18
sidebar:
  hidden: true
---

# セッション履歴

> 2026-06-18 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260618_mcp_gsheets_auth_fix_and_cron/)

---

### Claude *(15:53 JST)*

既存の実行スクリプトのパターンを確認します。

CLAUDE.md のルールに従い、スクリプト作成前に内容を確認します。

以下を作成します：

**`scripts/run_record_note_posts.sh`**
```bash
#!/bin/bash
export PATH="/usr/local/bin:$PATH"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_PATH="$REPO_ROOT/logs/record_note_posts.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S JST')] $*" | tee -a "$LOG_PATH"; }

log "record-note-posts 開始"

cd "$REPO_ROOT"
claude -p --model opus "/record-note-posts" >> "$LOG_PATH" 2>&1

log "record-note-posts 完了"
```

**crontab に追加する行**
```
0 3 * * * /bin/bash /root/xClaude/scripts/run_record_note_posts.sh
```

作成して crontab に追加してよいですか？

## よーん

はい

### Claude

完了しました。毎朝 3:00 に `record-note-posts` が実行されます。ログは `logs/record_note_posts.log` に記録されます。

MCP の認証パス設定に問題があります。`settings.json` を確認します。

4行目の `${HOME}` が展開されていないのが原因です。絶対パスに修正します。

`settings.json` の編集が自動モードでブロックされました。

**問題**: `GOOGLE_APPLICATION_CREDENTIALS` の `${HOME}` が agent/cron コンテキストで展開されず、Sheets の認証に失敗しています。

**修正内容**（1行だけ）:
```
"${HOME}/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json"
→
"/root/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json"
```

`.claude/settings.json` の4行目を手動で変更するか、許可をいただければ編集します。

修正しました。再度スクリプトを実行します。

2回目は正常に完了しました。

- **新規追加**: 1件（「SCEをAUXに〜アポロ12号」 ビュー77 / スキ5 / スキ率6.49%）
- settings.json の修正が反映され、Sheets への書き込みも成功しています。

master に push しました。コンフリクトは `GOOGLE_APPLICATION_CREDENTIALS` の絶対パスを優先して解決しています。

---

## よーん *(07:36 JST)*

備考: リモート環境では Google Sheets 認証情報（gcp/ フォルダ）が存在しないため、ポスト数・引用・リプライ数は取得できませんでした。

remote session から上記の報告があります。google sheets の認証情報については以前も修正を行っていますが、それがまた変更されていると思います。変更ログを調べて、ローカルでもリモートでも mcp-gsheets が動くような修正計画を立ててください。まだ修正はしないで。

### Claude *(07:36 JST)*

変更ログと現在の設定を調べます。経緯が掴めました。計画を作成します。

---

## 状況整理

**認証の変遷（問題の根本）**

| 日付 | 変更内容 |
|---|---|
| 2026-06-04 | `settings.json` に `GOOGLE_APPLICATION_CREDENTIALS` を追加（ファイルパス方式） |
| 2026-06-07 | それがリモートで壊れるため **削除**（`GOOGLE_SERVICE_ACCOUNT_KEY` 方式に戻した） |
| 2026-06-15 昨日 | cron で Sheets が動かなかったため **再追加** → またリモートが壊れた |

**3つの実行コンテキストと認証状態**

| コンテキスト | `GOOGLE_APPLICATION_CREDENTIALS` | `GOOGLE_SERVICE_ACCOUNT_KEY` | 結果 |
|---|---|---|---|
| ローカル対話 | なし（削除後） | `.bashrc` が設定 ✓ | ✓ 動く |
| ローカル cron | なし（削除後） | `.bashrc` は非実行 → **未設定** | ✗ 壊れる |
| リモート | `settings.json` が `/root/xClaude/gcp/…`（存在しない）を指す | クラウド環境が設定 ✓ | ✗ 壊れる |

**根本原因**: Google Auth Library は `GOOGLE_APPLICATION_CREDENTIALS` を `GOOGLE_SERVICE_ACCOUNT_KEY` より優先する。ローカル cron は `.bashrc` を読まないため `GOOGLE_SERVICE_ACCOUNT_KEY` が未設定になる。

---

## 修正計画

**方針**: `GOOGLE_SERVICE_ACCOUNT_KEY` を唯一の認証手段とし、全コンテキストで確実に設定する。`GOOGLE_APPLICATION_CREDENTIALS` は `settings.json` から削除。

**変更ファイル**（修正のみ、新規作成なし）:

| ファイル | 変更内容 |
|---|---|
| `.claude/settings.json` | `env.GOOGLE_APPLICATION_CREDENTIALS` を削除（昨日の変更を revert） |
| `scripts/run_record_note_posts.sh` | `GOOGLE_SERVICE_ACCOUNT_KEY` を明示的に export する1行を追加 |
| `scripts/run_mond_letter_reply.sh` | 同上 |

**各 cron スクリプトに追加する共通行**:
```bash
export GOOGLE_SERVICE_ACCOUNT_KEY="$(cat /root/xClaude/gcp/charming-well-464402-u4-2cfb7bddf343.json 2>/dev/null)"
```

（`.bashrc` の112行目と同じ内容。ファイルが存在しないリモートでは空文字になり、クラウド環境の env を上書きしない）

修正を実施してよいですか？

---

## よーん *(07:40 JST)*

はい

### Claude *(07:41 JST)*

まず全 cron スクリプトを確認してから修正します。

`post_from_email.sh` は `claude -p` を使わないので、mcp-gsheets に関係する claude を呼ぶスクリプトは `run_mond_letter_reply.sh` と `run_record_note_posts.sh` の2本だけです。この2本と `settings.json` を修正します。

**1. settings.json から GOOGLE_APPLICATION_CREDENTIALS を削除**

**2. run_mond_letter_reply.sh に GOOGLE_SERVICE_ACCOUNT_KEY export を追加**

**3. run_record_note_posts.sh に同様の追加**

動作確認します。Sheets への書き込みが成功しています。commit & push します。

master に push しました。

**まとめ**:
- `settings.json` から `GOOGLE_APPLICATION_CREDENTIALS` を削除（リモートで壊れる原因）
- `run_mond_letter_reply.sh` / `run_record_note_posts.sh` に `GOOGLE_SERVICE_ACCOUNT_KEY` の明示 export を追加（ローカル cron 向け）
- ローカルテストで Sheets 書き込み（更新1件）が正常動作を確認
