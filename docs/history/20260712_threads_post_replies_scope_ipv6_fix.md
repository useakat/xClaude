---
title: Threads 自動投稿の不具合修正（replies スコープ＋IPv6 ハング） — セッション履歴
date: 2026-07-12
sidebar:
  hidden: true
---

# セッション履歴

> 2026-07-12 のセッション作業ログ。

← [報告書へ戻る](../../reports/20260712_threads_post_replies_scope_ipv6_fix/)

---

## よーん *(09:13 JST)*

今朝の threads 自動投稿で以下の不具合を発見

* メールから threads に投稿する時に、本文が500文字以上の時の分割、返信チェーンでの投稿ができていない。
* 投稿した際の outputs シートへの追加ができていない。
* 投稿したメールに「投稿済み」ラベルを貼ってアーカイブすることができていない

原因を調べて報告して。まだ修正はしないで。

### Claude *(09:14 JST)*

今朝の実行ログを確認します。

*[ツール: `Bash`, `WebFetch`]*

抽出が曖昧なので、返信管理の権限ページで確認します。

*[ツール: `WebFetch`, `Bash`]*

原因を特定しました。plan ファイルに調査結果を記録してから報告します。

*[ツール: `Write`, `AskUserQuestion`, `Edit`, `ExitPlanMode`]*

まず【即時】重複防止：対象メールに「投稿済み」ラベルを付与します。

*[ツール: `Bash`]*

✅ **暫定対処 完了**：対象メールに「投稿済み」ラベルを付与し、cron クエリのヒットが 0 件になりました（12:00 の重複投稿は起きません。INBOX には残っているので後で再テストに使えます）。

## 次：権限修正（再々認証）— よーんのブラウザ操作

**STEP 1: 返信権限を追加**
Meta ダッシュボード → **Use cases → Threads → Customize → Permissions** で **`threads_manage_replies`** を **Add**。

**STEP 2: 再認証（4スコープ）→ 即交換**
コードは失効が早いので、**①認可 → ②交換を続けて一気に**行ってください。

① `usephys1` ログイン状態で開く:
```
https://www.threads.com/oauth/authorize?client_id=4371768313073061&redirect_uri=https%3A%2F%2Fhttpbin.org%2Fget&scope=threads_basic%2Cthreads_content_publish%2Cthreads_manage_replies%2Cthreads_manage_insights&response_type=code
```
→「許可」→ httpbin の `code` をコピー（末尾 `#_` 除く）

② すぐに `!` で実行（secret と code を差し替え）:
```
! THREADS_APP_SECRET='現行のThreadsAppSecret' python3 scripts/threads_token_exchange.py --code 'ここにcode'
```

成功（`✓ 長期トークンを…保存`）したら教えてください。私が **`reply_quota_usage` プローブで返信権限を確認**し、OK なら対象メールのラベルを外して**再テスト（分割スレッド投稿→outputs 記録→ラベル/アーカイブ完走）**まで進めます。

あわせて、**孤児投稿（本文1だけの投稿）は Threads アプリから手動削除**をお願いします。

---

## よーん *(10:20 JST)*

成功した

### Claude *(10:20 JST)*

再認証成功ですね。返信権限が入ったかプローブで確認します。

*[ツール: `Bash`, `Bash`, `Bash`]*

実行中です（スレッド投稿は publish 間の待機があるため数十秒〜数分かかります）。完了通知を待って結果を確認します。

完了（exit 0）。ログと outputs 記録・ラベル状態を確認します。

*[ツール: `Bash`]*

投稿は完全成功（本文2件＋リプ1件のスレッド）、ラベル＋アーカイブも OK。最後に outputs 記録を確認します。

*[ツール: `Bash`, `Bash`, `Bash`, `Bash`]*

実行時の本当の exit code を確認します（先ほどの表示はファイル末尾だけでした）。

*[ツール: `Bash`, `Bash`, `Bash`]*

## 根本原因 その2 が確定

**googleapis の DNS が IPv6 のみ返し、この VPS は IPv6 不通のため gspread（record_output.py）が接続ハング**していました。

| 切り分け | 結果 |
|---|---|
| gws ラベル付与 | **0.8秒**（正常）|
| record_output.py | **60秒超ハング**（timeout kill）|
| `sheets.googleapis.com` の解決 | **AAAA（IPv6）のみ**返る |
| IPv6 到達性 | **接続不可** |

つまり再テストの経緯は：投稿成功（38秒）→ ラベル付与成功 → **record_output が IPv6 ハング → 300秒 timeout で kill（exit 124）** → outputs 未記録・「完了」ログなし。graph.threads.net で起きたのと同じ IPv6 問題です（今朝6:00 の z01 記録が通ったのは、たまたま接続順の運が良かった＝**間欠性**で、X 系フローにも同じリスクがあります）。

## まとめ（不具合の全体像）
1. **分割スレッド投稿不可** → `threads_manage_replies` 不足 → **再認証で解決済み**（本文2件＋リプ1件の投稿成功を確認）
2. **outputs 未記録** → record_output.py の **IPv6 ハング**（未修正）
3. **ラベル/アーカイブ** → 実は今回**成功**していた（初回失敗時は症状1の連鎖）

## 修正提案（スクリプト編集のため確認します）
`scripts/record_output.py` に、threads 系スクリプトと同じ **IPv4 固定パッチ**（`socket.getaddrinfo` を IPv4 優先に）を3行ほど追加します。これは X 投稿の記録（毎日の cron）でも同じハングが起こり得るため、恒久対策になります。

修正してよいですか？（OK なら修正 → 実 permalink で欠損分の outputs 記録を補完 → 完了確認まで行います）

---

## よーん *(10:33 JST)*

修正して

### Claude *(10:33 JST)*

`record_output.py` に IPv4 固定パッチを追加します。

*[ツール: `Edit`]*

修正しました。実 permalink で欠損分を補完しつつ、ハングが解消したか時間計測します。

*[ツール: `Bash`]*

✅ **全不具合の解消を確認しました。**

## 修正結果

| 症状 | 原因 | 状態 |
|---|---|---|
| 1. 分割スレッド投稿不可 | `threads_manage_replies` スコープ不足 | ✅ 再認証で解決（本文2件＋リプ1件の投稿成功） |
| 2. outputs 未記録 | record_output.py の **IPv6 接続ハング** | ✅ IPv4 固定パッチで解決（**60秒超ハング → 1.6秒**）＋欠損分を補完記録 |
| 3. ラベル/アーカイブ不可 | 症状1の連鎖（初回のみ） | ✅ 再テストで正常動作を確認済み |

outputs に記録済み: `['2026-07-12 10:33:55', 'https://www.threads.com/@usephys1/post/DarJgo8nedJ', 'threads']`

## よーんへの残タスク（1つ）
**孤児投稿の手動削除**: 今朝 07:00 の失敗時に本文1だけ公開された投稿（スレッドの続きが無いもの）が Threads に残っています。アプリから削除してください（10:21 の完全なスレッドは残してOK）。

## 補足
- `record_output.py` の IPv4 固定は **X 投稿の記録（毎日の cron）にも効く恒久対策**です（今朝6:00 が通ったのは運。間欠的に同じハングが起こり得ました）。
- 明日以降の threads cron（7/12/17/20時）は、新しい【threads投稿】メールが INBOX にあれば正常に動くはずです。

---

この一連の修正（threads_manage_replies 再認証＋record_output IPv4 固定）を `/record` で記録しますか？

---

## よーん *(10:57 JST)*

* 孤児投稿の手動削除は行った

### Claude *(10:58 JST)*

孤児投稿の削除ありがとうございます。これで今回の不具合対応はすべて完了です。

## 完了サマリー
- ✅ 返信権限（`threads_manage_replies`）再認証 → 分割スレッド投稿が動作
- ✅ `record_output.py` IPv4 固定 → outputs 記録ハング解消（60秒超→1.6秒）＋欠損補完
- ✅ ラベル/アーカイブ動作確認
- ✅ 孤児投稿の手動削除（よーん実施）

次回の threads cron（12:00/17:00/20:00）から、新しい【threads投稿】メールがあれば全工程（分割スレッド投稿→outputs 記録→ラベル/アーカイブ）が完走するはずです。

この修正一式（`threads_manage_replies` 再認証＋`record_output.py` IPv4 固定）を `/record` で記録しますか？（`post_threads.py` 等は前回記録済みなので、今回の差分は record_output.py の修正＋再認証の経緯です）

STEP 1・2 を実行します。

*[ツール: `Bash`]*

STEP 3: 未記録の変更候補を提案します。

---

**変更ログ候補（未記録）**

1. **Threads 自動投稿の不具合修正（threads_manage_replies 再認証＋record_output の IPv6 ハング解消）** — 初回 cron 実行で①分割スレッド投稿失敗②outputs 未記録③ラベル未付与が発生。原因は (a) 返信作成に必要な `threads_manage_replies` スコープ不足（→権限追加＋再認証で解決）、(b) googleapis が IPv6 のみ解決され `record_output.py` の gspread が接続ハング（→IPv4 固定パッチで 60秒超→1.6秒）。再テストで分割スレッド投稿→記録→ラベル/アーカイブの完走を確認、欠損 outputs も補完。
   - 関連コミット: 未コミット（`scripts/record_output.py` のみ）
   - 変更ファイル: `scripts/record_output.py`（IPv4 固定）＋`gcp/threads_token.json`（再認証・gitignore）
   - 関連する過去の変更: **【threads投稿】メールを cron で Threads へ投稿する基盤を追加**（07-11）、**Threads 投稿一覧の API 取得・記録基盤を新規構築**（07-08）

補足: record_output.py の IPv4 固定は X 投稿記録（毎日の cron）にも効く恒久対策です。

記録してよいですか？（番号「1」/ スキップ）

---

## よーん *(11:05 JST)*

1

### Claude *(11:06 JST)*

STEP 4: 報告書を作成します。

*[ツール: `Write`]*
