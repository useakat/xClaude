---
title: analyze-target
description: analyze-target スキル
category: リサーチ・分析
---

← [スキル一覧へ](/xClaude/skills/)

## スキル説明

analyze-target スキル

## 詳細内容

あなたは persona / pain / what データベースの設計者です。
与えられた文章を分析し、既存の CSV 構造に合わせた追加レコード案を提案します。

対象テキスト: $ARGUMENTS

## Step 1: 既存の CSV を読み込む

以下の3シートを取得し、既存レコードの内容とIDの採番状況を把握する。

```
sheets_get_values(spreadsheetId="1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc", range="persona!A:Z")
sheets_get_values(spreadsheetId="1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc", range="pain!A:Z")
sheets_get_values(spreadsheetId="1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc", range="what!A:Z")
```

### 各ファイルの構造

**persona.csv**
| カラム | 説明 |
|---|---|
| persona_id | PE001 形式 |
| label | ペルソナの名称 |
| pain_domain | emotion / x_post / science_curiosity など |
| awareness_level | unaware / problem_aware / solution_seeking |
| channel_affinity | post / note / post/note |
| description | 一行説明 |

**pain.csv**
| カラム | 説明 |
|---|---|
| id | PR001 形式 |
| title | pain の一言表現 |
| domain | emotion / x_post / science_curiosity など |
| severity | 1〜5（5が最も深刻） |
| affected_scope | 影響を受ける人の属性・範囲 |
| persona_ids | 対応する persona_id |

**what.csv**
| カラム | 説明 |
|---|---|
| id | W001 形式 |
| pain_id | 対応する pain の id |
| title | 提供コンテンツの名称 |
| description | 提供価値の説明 |

## Step 2: テキストを分析する

$ARGUMENTS のテキストから以下を読み取る。

- **誰の悩みか**：どんな属性・状況の人が対象か
- **何に困っているか**：表面的な困りごととその本質
- **何を求めているか**：awareness_level はどの段階か
- **何を提供できるか**：どんなコンテンツ・価値が解決策になるか

## Step 3: 既存レコードとの重複チェック

- 同じ persona・pain・what が既存にないか確認する
- 近いものがある場合は「既存の〇〇に近い」と明記し、新規追加が必要かを判断する

## Step 4: 複数候補を分かりやすく提示する

既存の最大 ID の続番で提案する。
追加が不要なケース（既存で対応可能）は「追加不要」と理由を示して終了する。

複数候補がある場合は、候補ごとに「スコア」を付けて提示し、ユーザーが選択できるようにする。

## Step 5: ユーザーの選択を取得する

複数候補が出た場合、ユーザーから以下をそれぞれ選択してもらう：

```
persona 候補をNo で指定: [ユーザーが数字を入力]
pain 候補をNo で指定: [ユーザーが数字を入力]
what 候補をNo で指定: [ユーザーが数字を入力]
```

入力をパースして、ユーザーの選択内容を確認する。

## Step 6: Google Sheets に自動追記する

選択内容に基づいて、以下の処理を実行する：

1. **各シートの現在の最大 ID を確認**
   - persona シート：最大 persona_id を取得
   - pain シート：最大 id を取得
   - what シート：最大 id を取得

2. **新規 ID を採番**（max_id + 1）

3. **各シートに 1 レコードずつ追記**
   ```
   sheets_append_values(
     spreadsheetId="1LerdRNS7dwPXhjunDY4Z4u7g7LWkQqABsat3_LBeIGc",
     range="persona!A:F",
     values=[[新規persona_id, label, pain_domain, awareness_level, channel_affinity, description]]
   )
   ```

4. **完了報告**
   - 追記された新規 ID とレコード内容を表示

## 出力形式（STEP 4）

---
### 分析結果

- ターゲット：
- 表面の pain：
- 本質の pain：
- awareness_level：
- 提供できる what：

### 既存との重複確認

（重複あり／なしを明記）

### 追加レコード候補

**persona 候補（複数、スコア付き）：**
1. [説明1]（スコア: 8.5/10）
2. [説明2]（スコア: 7.2/10）

**pain 候補（複数、スコア付き）：**
1. [説明1]（スコア: 9.0/10）

**what 候補（複数、スコア付き）：**
1. [説明1]（スコア: 8.8/10）
2. [説明2]（スコア: 7.5/10）

### 選定の根拠

- persona：
- pain の severity：
- what：

---

## STEP 5-6 でのユーザーインタラクション

```
【追加候補を確認してください】

persona 候補：
1. ジェネレーションZ / STEM関心層 / 好奇心駆動型（スコア: 8.5/10）
2. 30代エンジニア / 文系転職志向（スコア: 7.2/10）

pain 候補：
1. 物理の複雑性 / 時間不足（スコア: 9.0/10）

what 候補：
1. 科学知識 + 人間ドラマ / エンタメ性（スコア: 8.8/10）
2. 実践的な問題解決法（スコア: 7.5/10）

→ 追記対象を指定してください：
   persona No: 1
   pain No: 1
   what No: 1
```

## 注意事項

- 既存レコードの ID 体系（PE / PR / W + 3桁数字）を必ず踏襲する
- 関連性の薄い pain や what は追加しない
- what は 1〜3 件を目安に、具体的なコンテンツ形式（X短文ポスト / X長文ポスト / note 記事 / note シリーズ）を明示する
- **ユーザーの選択確認後、Google Sheets に自動追記する（STEP 5-6）**

