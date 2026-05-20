---
title: フォロワー全件ペルソナ LLM 分類・ペルソナ19新設・classify-followers スキル追加
date: 2026-05-21
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog.md)

## 背景・動機

キーワードマッチ方式の `assign_persona()` では4183件のフォロワーのうち64%（2690件）がペルソナ13（その他）に落ちており、実際のフォロワー層の把握が困難だった。LLMがbioの文脈を読んで分類することで、より正確な分布把握と未知クラスタの発見を目指した。外部APIを使わずClaude Code subagentのみで完結させる方針を取った。

## 実施内容

**Pass 1: 全件 LLM 分類**
- 4183件を150件バッチ28分割し、subagent 28並列（3ターン）で分類
- 各エージェントに18ペルソナの圧縮リファレンスを渡し、`username / persona / confidence / memo` のJSON配列を出力させた
- result_22/23/24/26でエージェントが`id`のみ返却 → ID→usernameマップで解決
- specific_dict（既知ユーザーの手動定義）を適用して上書き
- 全結果を `persona/follower_persona_llm.json` に保存

**Pass 2: 新ペルソナ候補クラスタ分析**
- confidence=low/medium のペルソナ13（1388件）を3エージェント並列でクラスタ分析
- 「天体観測・星空実践派」を26件（1.9%）検出 → ペルソナ19として新設
- Part 1/2エージェントに幻覚発生（「よーんファン47%」「bot群330件」）→ 実データ検証で否定
- Part 0分析と実データ検証（キーワード検索）の結果のみを採用

**ペルソナ19新設**
- `persona/19_stargazer-practitioner.md` を作成
- `persona/README.md` に19番を追記

**classify-followers スキル追加**
- 次回以降の差分更新に対応したスキル `.claude/skills/classify-followers/SKILL.md` を作成
- 初回: 全件分類、2回目以降: 新規/アンフォロー差分のみ処理

**成果物ファイルの整理**
- `follower_persona_llm.json` → `persona/` へ移動
- `follower_persona_llm_summary.md` → `docs/reports/20260521_follower_persona_llm_analysis.md` へ移動
- `new_persona_proposals.md` → `docs/reports/20260521_new_persona_proposals.md` へ移動

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `persona/follower_persona_llm.json` | 新規作成（4183件の LLM 分類結果） |
| `persona/19_stargazer-practitioner.md` | 新規作成（天体観測・星空実践派ペルソナ定義） |
| `persona/README.md` | ペルソナ19の行・構成説明を追記 |
| `.claude/skills/classify-followers/SKILL.md` | 新規作成（差分更新スキル） |
| `.claude/skills/metadata.yaml` | classify-followers エントリを追加 |
| `docs/reports/20260521_follower_persona_llm_analysis.md` | 分類結果サマリー |
| `docs/reports/20260521_new_persona_proposals.md` | Pass 2 新ペルソナ候補レポート |

## 設計判断

- **subagentのみで完結**: 外部APIコスト・認証なしで大量分類が可能。ただし1バッチあたり100件以下が幻覚対策として望ましいと判明（今回150件で幻覚発生）
- **2-Pass方式**: Pass1で全件に仮ペルソナを振り、Pass2でペルソナ13かつ低確信度のみを再分析。全件を2回分類するより効率的
- **specific_dict上書き**: リプ頻度10回以上の既知ユーザーはLLM分類に関わらず手動定義を優先
- **ペルソナ19独立化の判断**: 「条件（3%超の反応率or絶対数100超）」未達だが、既存18ペルソナにない「観測・体験行動軸」という明確な差異があるため新設を承認

## 確認結果

- 全4183件がカバーされていることを確認（件数照合スクリプトで検証）
- ペルソナ13割合: キーワード分類64.3% → LLM分類73.3%（LLMが汎用IT/AI bioを保守的に判定するため増加。コンテンツターゲティング精度は向上）
- specific_dictの8名が正しいペルソナに分類されていることを確認
- classify-followers スキルが `/classify-followers` で呼び出せることを確認

## 今後の課題

- 次回フォロワー取得後に `/classify-followers` で差分更新を実行し、スキルの動作を実地検証する
- 天体観測・星空実践派（P19）へのコンテンツ反応率を計測し、3%超なら独立ペルソナとして本格運用
- Pass 2 の幻覚対策として、バッチサイズを50-100件に縮小し代表bioをusernameで検証するフローを `SKILL.md` に反映済み
