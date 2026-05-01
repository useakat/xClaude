あなたは persona / pain / what データベースの設計者です。
与えられた文章を分析し、既存の CSV 構造に合わせた追加レコード案を提案します。

対象テキスト: $ARGUMENTS

## Step 1: 既存の CSV を読み込む

以下の3ファイルを読み込み、既存レコードの内容とIDの採番状況を把握する。

- `/home/user/xClaude/database/persona.csv`
- `/home/user/xClaude/database/pain.csv`
- `/home/user/xClaude/database/what.csv`

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

## Step 4: 追加レコード案を提案する

既存の最大 ID の続番で提案する。
追加が不要なケース（既存で対応可能）は「追加不要」と理由を示して終了する。

## 出力形式

---
### 分析結果

- ターゲット：
- 表面の pain：
- 本質の pain：
- awareness_level：
- 提供できる what：

### 既存との重複確認

（重複あり／なしを明記）

### 追加レコード案

**persona.csv**
```
persona_id,label,pain_domain,awareness_level,channel_affinity,description
PEXX,...
```

**pain.csv**
```
id,title,domain,severity,affected_scope,persona_ids
PRXX,...
```

**what.csv**
```
id,pain_id,title,description
WXX,...
WXX,...
```

### 選定の根拠

- persona：
- pain の severity：
- what：
---

## 注意事項

- 既存レコードの ID 体系（PE / PR / W + 3桁数字）を必ず踏襲する
- 関連性の薄い pain や what は追加しない
- what は 1〜3 件を目安に、具体的なコンテンツ形式（X短文ポスト / X長文ポスト / note 記事 / note シリーズ）を明示する
- CSV として貼り付けできる形式で出力する（ユーザーが確認後に追記するため、実際のファイル編集は行わない）
