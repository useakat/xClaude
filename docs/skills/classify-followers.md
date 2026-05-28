---
title: classify-followers
description: フォロワー全件をペルソナ分類し、前回分類との差分（新規・アンフォロー・消滅）を更新する。初回は全件LLM分類、2回目以降は差分のみを分類して既存JSONに追記・削除する。
category: リサーチ・分析
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

フォロワー全件をペルソナ分類し、前回分類との差分（新規・アンフォロー・消滅）を更新する。初回は全件LLM分類、2回目以降は差分のみを分類して既存JSONに追記・削除する。

## 詳細内容

# classify-followers スキル

Xフォロワーのペルソナ分類を実行・更新する。

## データ定義

| 項目 | パス |
|---|---|
| 分類結果 JSON | `persona/follower_persona_llm.json` |
| ペルソナリファレンス | `persona/README.md` |
| 入力フォロワー JSON | ユーザーが指定（デフォルト: `/tmp/x_followers_all.json`） |
| 出力レポート | `docs/reports/YYYYMMDD_follower_persona_update.md` |

## ペルソナ圧縮リファレンス（subagent 埋め込み用）

```
01: 物理・科学に憧れる30代文系会社員（数式挫折、知的好奇心）
02: 技術系・エンジニア・IT職（物理学習目的、宇宙・量子への興味あり）
03: 育児中の母親・主婦（子供の「なぜ?」に答えたい）
04: 60代以上のシニア男性（退職・定年・科学ファン・SF・哲学）
05: 文系就職した元理系学生（物理挫折・再挑戦・20代）
06: 教師・塾講師・教育職（授業ネタ・理科・物理）
07: 50-60代女性・文学派・物語好き（SF・note発信・読書家）
08: 量子・物理専門のITエンジニア（業務で物理理解が必要）
09: 医療職（医師・看護師・薬剤師・物理コンプレックス）
10: 起業家・経営者・CEO（科学を経営哲学に応用）
11: 物理計算・理論大好き派（量子・最新観測・数式好き）
12: ユーモア・軽妙な突っ込み系宇宙ファン（絵文字多め・ライト反応）
13: その他・分類困難（bio短すぎ・空欄・料理・動物・音楽など関係ない趣味）
14: 技術検証・独自仮説派エンジニア（議論好き・専門用語OK）
15: AI関連（生成AI・LLM・GPT・Claude・プロンプトエンジニア）
16: クリエイター（イラスト・漫画・小説・デザイン・映像・音楽制作）
17: SF・サブカル・アニメ・ゲーム・コスプレ・推し活
18: 学生（高校生・大学生・院生・受験生・物理選択）
19: 天体観測・星空実践派（望遠鏡・プラネタリウム・天体写真・星見オフ会）
```

---

## STEP 0: モード判定

```bash
ls persona/follower_persona_llm.json 2>/dev/null && echo "UPDATE" || echo "INITIAL"
```

- ファイルが **存在しない** → **初回モード**（全件分類）
- ファイルが **存在する** → **更新モード**（差分分類）

---

## STEP 1: フォロワーデータ読み込み

ユーザーからフォロワーJSONのパスを受け取る（未指定時は `/tmp/x_followers_all.json`）。

```python
import json
with open('<input_path>') as f:
    current_followers = json.load(f)
# 形式: [{"id": "...", "username": "...", "name": "...", "description": "...", "public_metrics": {...}}, ...]
print(f"現在のフォロワー数: {len(current_followers)}")
```

---

## STEP 2: 差分計算（更新モードのみ）

```python
import json

# 既存分類読み込み
with open('persona/follower_persona_llm.json') as f:
    existing = json.load(f)
existing_map = {r['username']: r for r in existing['results']}
existing_usernames = set(existing_map.keys())

# 現在フォロワー
current_usernames = {u['username'] for u in current_followers}
current_map = {u['username']: u for u in current_followers}

# 差分
new_followers = [current_map[u] for u in (current_usernames - existing_usernames)]
unfollowed = existing_usernames - current_usernames  # アンフォロー or 消滅

print(f"新規フォロワー: {len(new_followers)}件")
print(f"アンフォロー/消滅: {len(unfollowed)}件")
```

差分が **0件** の場合はここで終了し「変化なし」と報告する。

---

## STEP 3: 新規フォロワーの LLM 分類

新規フォロワーが **150件以下** の場合は 1 エージェント、それ以上は 150件バッチに分割して並列 Agent 呼び出し。

各 Agent へのプロンプト構造：

```
あなたはXフォロワーのbioを19種類のペルソナに分類する専門家です。

## ペルソナリファレンス
[STEP 0 の圧縮リファレンス]

## 分類ルール
- name（表示名）と description（bio）を合わせて判断する
- bioが空欄・10文字未満の場合は 13 に分類
- 1人につき最も当てはまるペルソナ1つを選ぶ
- confidence: high（確信あり）/ medium（どちらかと言えば）/ low（bio不足で推測）
- memo: 判断根拠を20字以内で

## 出力形式（JSON配列のみ出力）
```json
[
  {"username": "xxx", "persona": "02", "confidence": "high", "memo": "エンジニアbio、物理学習目的"},
  ...
]
```

## 対象データ
[150件以下の username + name + description]
```

結果を `/tmp/classify_new_XX.json` に保存させる。

---

## STEP 4: 結果統合・JSON 更新

```python
import json
from datetime import date

# 既存 JSON 読み込み
with open('persona/follower_persona_llm.json') as f:
    existing = json.load(f)

# 新規分類結果を統合
new_results = []
for i in range(num_batches):
    with open(f'/tmp/classify_new_{i:02d}.json') as f:
        new_results.extend(json.load(f))

# アンフォロー/消滅アカウントを除去
existing_results = [r for r in existing['results'] if r['username'] not in unfollowed]

# 新規追加
existing_results.extend(new_results)

# 保存
output = {
    'classified_at': str(date.today()),
    'total': len(existing_results),
    'previous_total': existing['total'],
    'added': len(new_results),
    'removed': len(unfollowed),
    'results': existing_results,
}
with open('persona/follower_persona_llm.json', 'w') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"更新完了: {existing['total']} → {len(existing_results)}件")
```

---

## STEP 5: 差分レポート生成

`docs/reports/YYYYMMDD_follower_persona_update.md` に保存：

```markdown
# フォロワーペルソナ更新レポート

**更新日**: YYYY-MM-DD
**前回総数**: N件
**今回総数**: M件（+追加 / -削除）

## 新規フォロワー分類（N件）

| ペルソナ | 件数 | % |
|---|---|---|
| 01 | ... | ... |
...

## アンフォロー/消滅（N件）

| ペルソナ | 件数 |
|---|---|
| 13 | ... |
...

## ペルソナ分布の変化

| P | 前回 | 今回 | 差分 |
|---|---|---|---|
...
```

---

## STEP 6: Git コミット

```bash
bash $(git rev-parse --show-toplevel)/scripts/commit_and_sync.sh \
  "feat(persona): フォロワーペルソナ分類更新（YYYY-MM-DD）"
```

---

## 初回モード（全件分類）

既存 JSON がない場合は、フォロワー全件を 150件バッチに分割して並列 Agent 分類する。  
手順は `/root/.claude/plans/tidy-tinkering-pudding.md` の Pass 1 と同様。

バッチ分割スクリプト：

```python
import json

with open('<input_path>') as f:
    followers = json.load(f)

batch_size = 150
batches = [followers[i:i+batch_size] for i in range(0, len(followers), batch_size)]
for idx, batch in enumerate(batches):
    with open(f'/tmp/classify_batch_{idx:02d}.json', 'w') as f:
        json.dump(batch, f, ensure_ascii=False)

print(f"バッチ数: {len(batches)}")
```

分類後は STEP 4・5・6 と同じ手順で保存・レポート・コミット。

---

## 注意事項

- 分類後に **specific_dict**（手動定義の既知ユーザー→ペルソナ対応表）を適用して上書きする
  - 定義は `persona_breakdown2.py` の `specific` 辞書を参照
  - 必要なら `persona/specific_users.json` として永続化を検討
- フォロワー JSON の取得方法は xmcp（X API MCP サーバー）または手動エクスポートを使う
- LLM エージェントが幻覚を起こすことがある（特にバイオが少ない大量バッチ）。次の対策を取る：
  - バッチサイズは 100 件以下が望ましい
  - エージェントが返した JSON に `username` がない場合は `id` で元データから復元する
  - 分類後に元データとの件数照合を必ず行う
