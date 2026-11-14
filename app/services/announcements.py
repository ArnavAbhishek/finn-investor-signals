"""Best-effort NSE website feed adapter (not a licensed streaming feed).

NSE's public website interface is subject to access controls/changes. It is
not an official supported developer API. Fail closed: never substitute demo
filings while declaring the data live.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from urllib.parse import urlparse
import requests

from .signals import IST, digest_event, parse_nse_date

BASE = "https://www.nseindia.com"
ENDPOINT = f"{BASE}/api/corporate-announcements"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": f"{BASE}/companies-listing/corporate-filings-announcements",
}


def _official_file(value: str | None) -> str | None:
    if not value or not isinstance(value, str):
        return None
    if value.startswith("/"):
        value = BASE + value
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (hostname == "nseindia.com" or hostname.endswith(".nseindia.com")):
        return None
    return value


def normalize_row(row: dict) -> dict | None:
    symbol = str(row.get("symbol") or row.get("sm_symbol") or "").upper().strip()
    title = str(row.get("desc") or row.get("attchmntText") or row.get("subject") or "").strip()
    detail = str(row.get("attchmntText") or row.get("desc") or "").strip()
    date = parse_nse_date(str(row.get("an_dt") or row.get("sort_date") or row.get("date") or ""))
    if not symbol or not title or date is None:
        return None
    link = _official_file(row.get("attchmntFile") or row.get("fileName") or row.get("attachment"))
    return digest_event(symbol, title, detail, link, date)


def fetch_announcements(symbols: list[str], hours: int = 24, now: datetime | None = None) -> list[dict]:
    if hours < 1 or hours > 24 * 30:
        raise ValueError("Window must be between 1 hour and 30 days")
    now = now or datetime.now(IST)
    start = now - timedelta(hours=hours)
    symbol_set = set(symbols)
    session = requests.Session()
    session.headers.update(HEADERS)
    # Most NSE website endpoints tolerate a browser UA; warm up on a filings
    # page only if the initial API request is rejected. Do not assume the NSE
    # homepage is reachable from a data-centre IP.
    warmed = False
    all_events = []
    cursor = start
    while cursor <= now:
        end = min(cursor + timedelta(days=6), now)
        response = session.get(ENDPOINT, params={
            "index": "equities",
            "from_date": cursor.strftime("%d-%m-%Y"),
            "to_date": end.strftime("%d-%m-%Y"),
        }, timeout=15)
        if response.status_code in (401, 403) and not warmed:
            warmed = True
            try:
                session.get(f"{BASE}/companies-listing/corporate-filings-announcements",timeout=7)
            except requests.RequestException:
                pass
            response = session.get(ENDPOINT, params={
                "index": "equities",
                "from_date": cursor.strftime("%d-%m-%Y"),
                "to_date": end.strftime("%d-%m-%Y"),
            }, timeout=15)
        response.raise_for_status()
        rows = response.json()
        # On dates with no filing NSE also returns {"data":[],"msg":...}.
        if isinstance(rows,dict) and isinstance(rows.get("data"),list):
            rows = rows["data"]
        if not isinstance(rows,list):
            raise ValueError("Unexpected NSE announcements response shape")
        for row in rows:
            if not isinstance(row, dict):
                continue
            event = normalize_row(row)
            if event and event["symbol"] in symbol_set and event["published_at"] >= start.isoformat() and event["published_at"] <= now.isoformat():
                all_events.append(event)
        cursor = end + timedelta(days=1)
    unique = { (r["symbol"], r["title"], r["published_at"]): r for r in all_events }
    return sorted(unique.values(), key=lambda r: (r["priority"], r["published_at"]), reverse=True)
