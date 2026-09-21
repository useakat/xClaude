#!/usr/bin/env python3
"""note.com の GraphQL API（新ダッシュボード用）クライアント。

新ダッシュボード https://note.com/dashboard は REST(/api/v1/stats/pv) ではなく
GraphQL を使っており、インプレッション・記事別売上・流入元がここからしか取れない。

認証は2段構え:
  1. POST https://note.com/api/v3/graphql/auth   (Cookie: _note_session_v5)
       → Set-Cookie: note_gql_auth_token=<JWT>（有効期限 30分）
  2. POST https://graphql.note.com/graphql
       Authorization: Bearer <JWT>
  ※ Cookie だけを graphql.note.com に送っても NotLoggedInViewer になる。

ライブラリとして:
    from note_gql import NoteGraphQL, period_vars
    gql = NoteGraphQL()
    data = gql.query(QUERY, period_vars("28d"))

CLI として（任意クエリの実行・スキーマ調査用）:
    python3 scripts/note_gql.py -q 'query{viewer{__typename}}'
    echo 'query{...}' | python3 scripts/note_gql.py --vars '{"unit":"ALL"}'
    python3 scripts/note_gql.py --introspect DashboardMetricKind
"""
import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

AUTH_URL = "https://note.com/api/v3/graphql/auth"
GQL_URL = "https://graphql.note.com/graphql"
JST = ZoneInfo("Asia/Tokyo")

# JWT の実際の有効期限は 30分。余裕をみて 25分で再取得する
TOKEN_TTL_SEC = 25 * 60

# DashboardPeriodUnit の enum 値（イントロスペクションで確認済み）
PERIOD_UNITS = [
    "DAY", "WEEK", "MONTH", "YEAR", "ALL",
    "LAST_7_DAYS", "LAST_28_DAYS", "LAST_365_DAYS", "CUSTOM",
]
# DashboardMetricKind の enum 値
METRIC_KINDS = ["IMPRESSION", "PAGE_VIEW", "LIKE", "COMMENT", "SALES"]
# DashboardNoteListOrder の enum 値
NOTE_LIST_ORDERS = [
    "PUBLISHED_DATE_DESC", "IMPRESSION_COUNT_DESC", "PAGE_VIEW_COUNT_DESC",
    "LIKE_COUNT_DESC", "COMMENT_COUNT_DESC", "SALES_DESC",
]

PRESETS = {
    "7d": ("LAST_7_DAYS", 7),
    "28d": ("LAST_28_DAYS", 28),
    "365d": ("LAST_365_DAYS", 365),
}


def _iso(d):
    """date/datetime を GraphQL の Datetime 形式（UTC 0時固定）へ。

    フロントは new Date("YYYY-MM-DD").toISOString() 相当を送っているので合わせる。
    """
    return f"{d.strftime('%Y-%m-%d')}T00:00:00.000Z"


def period_vars(period="all", today=None):
    """期間指定を unit/date/endDate の変数 dict に変換する。

    period:
      "all"                      → 全期間
      "7d" / "28d" / "365d"      → 直近 N 日（当日を含む）
      "YYYY-MM-DD"               → その1日だけ
      "YYYY-MM-DD:YYYY-MM-DD"    → 任意期間
    """
    today = today or datetime.now(JST).date()
    p = (period or "all").lower()

    if p == "all":
        # ALL のときフロントは date=endDate=今日を送り、unit 側で全期間扱いになる
        return {"unit": "ALL", "date": _iso(today), "endDate": _iso(today)}

    if p in PRESETS:
        unit, days = PRESETS[p]
        start = today - timedelta(days=days - 1)
        return {"unit": unit, "date": _iso(start), "endDate": _iso(today)}

    if ":" in p:
        s, e = p.split(":", 1)
        start = datetime.strptime(s.strip(), "%Y-%m-%d").date()
        end = datetime.strptime(e.strip(), "%Y-%m-%d").date()
    else:
        start = end = datetime.strptime(p.strip(), "%Y-%m-%d").date()

    if end < start:
        raise ValueError(f"期間の指定が逆です: {period}")
    return {"unit": "CUSTOM", "date": _iso(start), "endDate": _iso(end)}


def period_range(variables, today=None):
    """period_vars() の戻り値から (開始日, 終了日) の date を復元する。"""
    today = today or datetime.now(JST).date()
    end = datetime.strptime(variables["endDate"][:10], "%Y-%m-%d").date() \
        if variables.get("endDate") else today
    if variables["unit"] == "ALL":
        # 全期間の開始日は note 側の固定値（フロントの実装に合わせる）
        return datetime(2014, 4, 1).date(), end
    return datetime.strptime(variables["date"][:10], "%Y-%m-%d").date(), end


class NoteAuthError(RuntimeError):
    pass


class NoteGraphQL:
    """note GraphQL の薄いクライアント（トークンの自動取得・自動更新つき）。"""

    def __init__(self, session_id=None, timeout=30):
        self.session_id = session_id or os.getenv("NOTE_SESSION")
        if not self.session_id:
            raise NoteAuthError("NOTE_SESSION が .env に設定されていません")
        self.timeout = timeout
        self._s = requests.Session()
        self._s.headers.update({"User-Agent": "Mozilla/5.0"})
        self._s.cookies.set("_note_session_v5", self.session_id, domain=".note.com")
        self._token = None
        self._token_at = 0.0

    def _refresh_token(self):
        r = self._s.post(
            AUTH_URL,
            headers={"x-requested-with": "XMLHttpRequest",
                     "Referer": "https://note.com/dashboard"},
            timeout=self.timeout,
        )
        r.raise_for_status()
        token = self._s.cookies.get_dict().get("note_gql_auth_token")
        if not token:
            raise NoteAuthError(
                "note_gql_auth_token を取得できません。NOTE_SESSION が失効している可能性があります"
            )
        self._token, self._token_at = token, time.time()
        return token

    def token(self):
        if self._token is None or time.time() - self._token_at > TOKEN_TTL_SEC:
            self._refresh_token()
        return self._token

    def query(self, query, variables=None, _retried=False):
        """GraphQL クエリを実行して data を返す。errors があれば例外。"""
        r = self._s.post(
            GQL_URL,
            headers={
                "Content-Type": "application/json",
                "Origin": "https://note.com",
                "Referer": "https://note.com/",
                "Authorization": f"Bearer {self.token()}",
            },
            json={"query": query, "variables": variables or {}},
            timeout=self.timeout,
        )
        r.raise_for_status()
        body = r.json()
        errors = body.get("errors")
        if errors:
            # トークン失効時は取り直して1度だけリトライ（フロントの errorLink と同じ挙動）
            if not _retried and any(
                e.get("message") == "Unauthenticated" for e in errors
            ):
                self._refresh_token()
                return self.query(query, variables, _retried=True)
            raise RuntimeError("GraphQL error: " + json.dumps(errors, ensure_ascii=False))
        return body["data"]

    def paginate(self, query, variables, connection_field, page_size=50):
        """Relay 形式の Connection を最後まで辿って node のリストを返す。"""
        nodes, after = [], None
        while True:
            v = {**variables, "first": page_size, "after": after}
            conn = self.query(query, v)[connection_field]
            nodes += [e["node"] for e in conn["edges"] if e.get("node")]
            info = conn["pageInfo"]
            if not info.get("hasNextPage"):
                return nodes
            after = info["endCursor"]

    def viewer(self):
        """ログイン確認用。未ログインなら None。"""
        d = self.query("query{viewer{__typename ... on Viewer{urlname nickname}}}")
        v = d.get("viewer") or {}
        return v if v.get("__typename") == "Viewer" else None

    def last_updated_at(self):
        """記事別統計の最終集計時刻（ISO 文字列）。"""
        d = self.query("query{dashboardStatLastUpdatedTimes{noteStatLastUpdatedAt}}")
        return (d.get("dashboardStatLastUpdatedTimes") or {}).get("noteStatLastUpdatedAt")


def main():
    ap = argparse.ArgumentParser(description="note GraphQL API を直接叩く")
    ap.add_argument("-q", "--query", help="クエリ文字列（省略時は標準入力から読む）")
    ap.add_argument("--vars", default="{}", help="変数の JSON 文字列")
    ap.add_argument("--introspect", metavar="TYPE",
                    help="型名を指定して enum 値／フィールドを表示する")
    ap.add_argument("--viewer", action="store_true", help="ログイン状態を確認する")
    args = ap.parse_args()

    gql = NoteGraphQL()

    if args.viewer:
        v = gql.viewer()
        print(json.dumps(v or {"__typename": "NotLoggedInViewer"}, ensure_ascii=False, indent=2))
        sys.exit(0 if v else 1)

    if args.introspect:
        q = """query($n:String!){__type(name:$n){
                 name kind
                 enumValues{name}
                 fields{name type{kind name ofType{kind name ofType{name}}}}
                 inputFields{name type{kind name ofType{name}}}}}"""
        print(json.dumps(gql.query(q, {"n": args.introspect}),
                         ensure_ascii=False, indent=2))
        return

    query = args.query or sys.stdin.read()
    if not query.strip():
        ap.error("クエリが空です")
    print(json.dumps(gql.query(query, json.loads(args.vars)),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
