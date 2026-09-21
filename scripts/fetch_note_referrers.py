#!/usr/bin/env python3
"""note の新ダッシュボードから流入元（リファラ）を取得する。

新ダッシュボードの「流入元」グラフと同じデータで、
  - 期間合計（Google / X / note.com / no referrer …）
  - 日別の内訳（積み上げ棒グラフの元データ）
の両方が取れる。記事単位の内訳はスキーマに存在せず、アカウント全体のみ。

Usage:
  python3 fetch_note_referrers.py                       # 直近28日
  python3 fetch_note_referrers.py --period 7d
  python3 fetch_note_referrers.py --period 2026-09-01:2026-09-30
  python3 fetch_note_referrers.py --period all --no-daily   # 全期間の合計だけ
  python3 fetch_note_referrers.py --csv                 # date,referrer,count の CSV
  python3 fetch_note_referrers.py --csv --total         # referrer,count の CSV

Output (JSON):
  {
    "unit", "startDate", "endDate", "lastUpdatedAt",
    "total": [{"name", "count"} ...],
    "daily": [{"date", "label", "referrers": {"Google": 21, ...}, "total": 34} ...]
  }
"""
import sys
import csv
import json
import argparse
from pathlib import Path
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).parent))
from note_gql import NoteGraphQL, period_vars, period_range  # noqa: E402

REFERRER_QUERY = """
query($unit: DashboardPeriodUnit!, $date: Datetime!, $endDate: Datetime,
      $includeTimeSeries: Boolean!) {
  dashboardStatLastUpdatedTimes { noteStatLastUpdatedAt }
  dashboardNoteReferrersChart(unit: $unit, date: $date, endDate: $endDate) {
    id
    legend { name count color }
    timeSeriesBarChart @include(if: $includeTimeSeries) {
      labels
      data { label data color }
    }
  }
}
"""


def fetch(period="28d", include_daily=True):
    gql = NoteGraphQL()
    variables = {**period_vars(period), "includeTimeSeries": include_daily}
    data = gql.query(REFERRER_QUERY, variables)

    chart = data.get("dashboardNoteReferrersChart") or {}
    start, end = period_range(variables)

    legend = [
        {"name": e["name"], "count": e["count"], "color": e.get("color")}
        for e in (chart.get("legend") or [])
    ]

    daily = []
    series = chart.get("timeSeriesBarChart") or {}
    labels = series.get("labels") or []
    if labels:
        # 目盛りが日数と一致するときだけ実日付を割り当てる
        # （長期間だと granularity が週・月になりラベルが日付と対応しない）
        span = (end - start).days + 1
        dates = [start + timedelta(days=i) for i in range(len(labels))] \
            if len(labels) == span else [None] * len(labels)

        for i, label in enumerate(labels):
            refs = {}
            for s in series.get("data") or []:
                v = (s.get("data") or [])[i] if i < len(s.get("data") or []) else 0
                if v:
                    refs[s["label"]] = v
            daily.append({
                "date": dates[i].isoformat() if dates[i] else None,
                "label": label,
                "referrers": refs,
                "total": sum(refs.values()),
            })

    return {
        "unit": variables["unit"],
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "lastUpdatedAt": (data.get("dashboardStatLastUpdatedTimes") or {})
                         .get("noteStatLastUpdatedAt"),
        "total": legend,
        "daily": daily,
    }


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--period", default="28d",
                    help="all / 7d / 28d / 365d / YYYY-MM-DD / "
                         "YYYY-MM-DD:YYYY-MM-DD（既定 28d）")
    ap.add_argument("--no-daily", action="store_true", help="日別内訳を取得しない")
    ap.add_argument("--csv", action="store_true", help="CSV で出力する")
    ap.add_argument("--total", action="store_true",
                    help="--csv と併用: 日別ではなく期間合計を出力する")
    args = ap.parse_args()

    result = fetch(args.period, include_daily=not args.no_daily and not args.total)

    if not args.csv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    w = csv.writer(sys.stdout)
    if args.total or args.no_daily:
        w.writerow(["referrer", "count"])
        for e in result["total"]:
            w.writerow([e["name"], e["count"]])
    else:
        w.writerow(["date", "label", "referrer", "count"])
        for d in result["daily"]:
            for name, count in d["referrers"].items():
                w.writerow([d["date"] or "", d["label"], name, count])


if __name__ == "__main__":
    main()
