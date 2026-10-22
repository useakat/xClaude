#!/usr/bin/env python3
"""note 記事の価格設定ルール（docs/plans/note_funnel_measures.md「note 記事の価格設定ルール」2026-10-22）の判定。
note_article_daily.py（毎朝の照合とメール）と note_funnel_export.py（ダッシュボード・週次の「次の動作」列）が共用する。

  1. 有料記事は ¥100 から始める
  2. 現在価格の区間（改稿日があればそこから）で PV が RULE_PV に達し、購入が RULE_BUYS 以上なら「価格を上げる」
  3. 同じく PV が RULE_PV に達して購入が RULE_BUYS 未満なら「冒頭と有料ラインを見直す」（次の RULE_PV を待つ）
  4. 上げた価格の 売上/1,000 PV が前の価格の区間を下回れば「戻すかブラッシュアップするか判断」（2・3 より優先）
"""
RULE_PV = 200
RULE_BUYS = 2


def decide_action(n_pv: int, n_buy: int, price: int, prev: dict | None = None) -> str:
    """窓の PV・購入数・価格と、直前の区間 prev（{"price", "pv", "buys"}。無ければ None）から動作を返す。
    PV が RULE_PV 未満なら空文字"""
    if n_pv < RULE_PV:
        return ""
    cur_rev = n_buy * price / n_pv * 1000
    if prev and prev.get("price") and prev["price"] < price and prev.get("pv"):
        p_rev = prev["buys"] * prev["price"] / prev["pv"] * 1000
        if cur_rev < p_rev:
            return (f"戻すかブラッシュアップするか判断（規則 4：売上/1,000 PV {cur_rev:,.0f} 円 ＜ "
                    f"¥{prev['price']} の {p_rev:,.0f} 円 [PV {prev['pv']}・購入 {prev['buys']}]）")
    return "価格を上げる（規則 2）" if n_buy >= RULE_BUYS else "冒頭と有料ラインを見直す（規則 3）"
