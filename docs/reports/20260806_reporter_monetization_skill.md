---
title: マネタイズ月報スキル reporter-monetization を新設
date: 2026-08-06
tags: [skill, workflow]
sidebar:
  hidden: true
---

← [変更ログへ](../changelog/)

## 背景・動機

既存の月報（`reporter-monthly`）は運用中心で、マネタイズを「投稿の型別成績 × note 導線 × 来月計画」で捉える視点が無かった。よーんは毎月のマネタイズ運用状況を、次の3本柱で把握したい：
1. X・threads 投稿の**型別成績**（過去3ヶ月の推移つき）
2. **note マネタイズ状況**（売上＋ X/threads→note リンク導線の CTR/CVR/売上。note_url 付き全投稿対象）
3. **来月のマネタイズ計画案**（X/threads 運用の修正案・note 導線の修正案を含む）

方針：新スキルとして新設／手動実行のみ（まずは）／導線は W001 限定の既存 Xnote導線記録を使わず note_url 付き全投稿に拡張。

## 実施内容

- **`scripts/monetization_metrics.py` を新規作成**（集計エンジン）。決定論的な数値集計を Python に集約し、スキルは結果を物語化するだけにする。SA 認証（`GOOGLE_SERVICE_ACCOUNT_KEY` or `gcp/charming-well-...json`）＋ IPv4 固定、読み取り専用。`--month YYYY-MM`（既定=前月）で対象月＋前2ヶ月の3ヶ月分を JSON 出力。`--dry-run` で人間可読サマリー。
  - 型判定は outputs シートで行う（X: outputs.B の tweet_id で X投稿一覧を突合し what_id 付与／threads: Threads投稿一覧.H の元X投稿URL → outputs の what_id を解決）。
  - 出力: `x_by_type`（本数/IMP/エンゲージ/リンククリック/フォロー増）、`threads_by_type`（本数/views/エンゲージ）、`note_sales`（月次・記事別）、`funnel_by_type`（IMP→クリック(CTR)→購入(CVR)→売上）、`caveats`。
- **`.claude/skills/reporter-monetization/SKILL.md` を新規作成**。STEP2 で集計スクリプトを実行し、STEP4 で型別成績（3ヶ月推移）・note マネタイズ・来月計画の3セクションを生成、`docs/reports/monetization/YYYY-MM.md` に保存（STEP5）。数値は必ずスクリプト出力を使い、示唆・計画案のみ AI 生成。
- **`.claude/skills/metadata.yaml`** に `reporter-monetization: category: レポート生成` を追記（Wiki 自動更新用）。
- **`docs/reports/monetization/index.md`** を新設（レポート一覧）。

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/monetization_metrics.py` | 新規（型別成績・note売上・導線の3ヶ月集計、JSON/dry-run 出力） |
| `.claude/skills/reporter-monetization/SKILL.md` | 新規（月次マネタイズ報告の手順・フォーマット） |
| `.claude/skills/metadata.yaml` | `reporter-monetization` を追記 |
| `docs/reports/monetization/index.md` | 新規（レポート一覧） |

## 設計判断

- **集計は Python、物語は AI**：型別×3ヶ月×導線の突合は決定論的処理なので `monetization_metrics.py` に寄せ、数値の捏造を防ぐ。スキルは JSON を読んで所見・計画案だけ生成する。
- **導線は note_url 付き全投稿に拡張**：既存 Xnote導線記録（W001 限定・sync_x_note_analytics.py 生成）は非改修のまま、monetization_metrics.py が outputs.note_url を持つ全投稿で独自に再計算する。
- **総売上は note購入記録を正とする**：導線の売上は記事単位で型内重複排除するが型をまたぐ二重計上があり得るため、月次総売上は note_sales（実勢合計）を正とする。

## 確認結果

- `--month 2026-07 --dry-run` で **note売上 3,430円/8件** が既存月報 2026-07.md と一致（検算成功）。
- 型別成績（X: 長文/ワンポイント/短文/質問回答、threads）と3ヶ月の note売上推移が出力されることを確認。
- スキルが `/reporter-monetization` として読み込まれることを確認。

## 今後の課題（既知の制約）

- outputs 未記録の投稿は型別・導線の集計対象外（型は `(未記録)`/`(元投稿不明)` に計上）。
- W001 の note リンクはセルフリプ側にあり本体ポスト行のリンククリックに出ないため、導線 CTR は構造的に過小。
- threads はリンククリック指標が無く note 導線 CTR/CVR を算出できない（views 止まり）。
- 手動実行のみ。運用が固まれば routine 化を別途検討。
