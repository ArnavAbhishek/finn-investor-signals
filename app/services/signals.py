"""Transparent, deterministic announcement classification and prioritisation.

These are triage heuristics, not predictions of stock-price movements.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
CATEGORY_RULES = [
    ("management_change", r"\b(resign(?:ation|ed)?|appointment|appoints?|cessation|ceo|cfo|director|managing director|key managerial personnel)\b"),
    ("litigation", r"\b(litigation|lawsuit|penalty|regulatory order|show cause|insolvency|arbitration|fine|sebi order)\b"),
    ("M&A", r"\b(acquisit(?:ion|ions)|merger|demerger|joint venture|stake sale|amalgamation)\b"),
    ("results", r"\b(financial results|quarterly results|annual results|unaudited financial|audited financial|earnings release|results for the quarter)\b"),
    ("fund_raise", r"\b(qip|qualified institutional|rights issue|preferential allotment|fund rais|commercial paper|buyback|debt issuance|non-convertible debenture)\b"),
    ("pledging", r"\b(pledge|pledging|encumbrance|release of shares)\b"),
    ("credit_rating", r"\b(credit rating|rating upgrade|rating downgrade|rating reaffirm|rating action)\b"),
    ("capex", r"\b(capex|capital expenditure|capacity expansion|new plant|greenfield|new facility)\b"),
    ("insider_trading", r"\b(insider trading|promoter purchase|insider dealing|shareholding by designated person)\b"),
    ("bonus_split", r"\b(stock split|share split|bonus issue|sub-division of shares)\b"),
    ("dividend", r"\b(dividend|record date for dividend)\b"),
    ("earnings_call", r"\b(earnings call|investor call|concall|conference call|call transcript|audio recording)\b"),
    ("agm_egm", r"\b(annual general meeting|extraordinary general meeting|\bagm\b|\begm\b)\b"),
    ("postal_ballot", r"\b(postal ballot|e-voting result)\b"),
    ("investor_meetings", r"\b(investor meet|analyst meet|investor interaction|investor conference|schedule of analyst)\b"),
    ("press_release", r"\b(press release|media release|order win|product launch|strategic partnership)\b"),
]
BASE_PRIORITY = {
    "results": 91, "M&A": 92, "fund_raise": 82, "management_change": 88,
    "litigation": 87, "insider_trading": 67, "earnings_call": 40,
    "investor_meetings": 20, "credit_rating": 81, "dividend": 46,
    "bonus_split": 49, "capex": 74, "press_release": 45,
    "postal_ballot": 17, "agm_egm": 19, "pledging": 84,
    "unclassified": 10,
}
WHY = {
    "results": "Review the filed numbers and compare growth and margins with prior quarters.",
    "M&A": "Check transaction size, consideration, funding and closing conditions.",
    "fund_raise": "Check dilution, financing terms and how management intends to use proceeds.",
    "management_change": "Leadership transitions can change execution and governance risk; read the filing.",
    "litigation": "Verify regulatory or legal exposure and whether any amount is quantified.",
    "insider_trading": "Check the identity, magnitude and context of the reported transaction.",
    "earnings_call": "Compare management commentary and guidance with reported results.",
    "investor_meetings": "Usually routine unless substantive information is disclosed.",
    "credit_rating": "Check the agency rationale, direction of the change and outlook.",
    "dividend": "Check the announced amount and the applicable record or ex-date.",
    "bonus_split": "Review the ratio and record date; share count changes do not create cash.",
    "capex": "Check investment size, capacity and expected commissioning timeline.",
    "press_release": "Look for quantified operational or financial impact in the source document.",
    "postal_ballot": "Usually procedural; check the resolution if it affects ownership or strategy.",
    "agm_egm": "Review material resolutions rather than treating the meeting notice as a catalyst.",
    "pledging": "Monitor promoter collateral changes and potential governance implications.",
    "unclassified": "Routine disclosure unless the underlying document reveals something material.",
}


def classify(title: str, details: str = "") -> str:
    text = f"{title} {details}".lower()
    for name, pattern in CATEGORY_RULES:
        if re.search(pattern, text, re.I):
            return name
    return "unclassified"


def score(category: str, title: str = "") -> int:
    base = BASE_PRIORITY.get(category, 10)
    title = title.lower()
    if re.search(r"\b(resignation|resigned|downgrad|fraud|insolvency|default)\b", title):
        base += 6
    if re.search(r"\b(intimation|compliance|certificate|newspaper publication)\b", title):
        base -= 7
    return min(99, max(0, base))


def tier(value: int) -> str:
    return "high" if value >= 75 else ("medium" if value >= 40 else "routine")


def parse_nse_date(raw: str) -> datetime | None:
    if not raw:
        return None
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y", "%d-%m-%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw.strip(), fmt).replace(tzinfo=IST)
        except ValueError:
            pass
    return None


def digest_event(symbol: str, title: str, detail: str, source_url: str | None, date: datetime | None, *, demo: bool = False, category: str | None = None, why: str | None = None) -> dict:
    category = category or classify(title, detail)
    priority = score(category, title)
    return {
        "id": f"{symbol}-{date.isoformat() if date else 'undated'}-{abs(sum(ord(c) for c in title))}",
        "symbol": symbol,
        "title": title,
        "detail": detail[:520],
        "category": category,
        "priority": priority,
        "tier": tier(priority),
        "why": why or WHY.get(category, WHY["unclassified"]),
        "published_at": date.isoformat() if date else None,
        "source_url": source_url,
        "demo": demo,
    }


def market_alerts(prices: list[dict], price_threshold: float, volume_threshold: float) -> list[dict]:
    alerts = []
    for row in prices:
        change = row.get("change_pct")
        volume = row.get("volume_ratio")
        triggers = []
        if change is not None and abs(change) >= price_threshold:
            triggers.append(f"EOD price move {change:+.2f}% (threshold ±{price_threshold:g}%)")
        if volume is not None and volume >= volume_threshold:
            triggers.append(f"Volume {volume:.2f}× recent 20-session average (threshold {volume_threshold:g}×)")
        if triggers:
            alerts.append({"symbol": row["symbol"], "message": " · ".join(triggers), "demo": row.get("demo", False), "date": row.get("date")})
    return alerts
