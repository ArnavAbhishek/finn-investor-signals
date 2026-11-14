"""FINN: mobile-first, primary-source investment signal prototype."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from threading import Lock
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .services.announcements import fetch_announcements
from .services.market import fetch_prices
from .services.charts import demo_chart, live_chart, PERIODS
from .services.nse_quote import fetch_nse_quote
from .services.research import ResearchStore, discover_sources, fetch_public_pdf, validate_ticker
from .services.signals import IST, digest_event, market_alerts
from .services.casebook import infosys_case, compare_periods, SOURCES
from .services.angles import research_angles

PACKAGE = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("FINN_DATA_DIR",str(PACKAGE.parent / ".local_data"))).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
store = ResearchStore(DATA_DIR)
# Offline proof of the research loop: explicitly fictional training PDFs.
# Never placed under an actual company's NSE ticker.
for _filename, _kind in (
    ("DEMOCO_Annual_Report_EXTRACT_FICTIONAL.pdf", "annual_report"),
    ("DEMOCO_Earnings_Call_Transcript_FICTIONAL.pdf", "concall_transcript"),
    ("DEMOCO_Q2_Results_FICTIONAL.pdf", "results_filing"),
):
    _path = PACKAGE.parent / "examples" / _filename
    if _path.is_file():
        store.add_pdf("DEMOCO", _filename, _kind, _path.read_bytes())
app = FastAPI(title="FINN Investment Signals", version="4.0.0", description="Investor triage, not investment advice")
app.mount("/assets", StaticFiles(directory=PACKAGE / "static"), name="assets")

PORTFOLIO = json.loads((PACKAGE / "data" / "portfolio.json").read_text())
DEMO_EVENTS = json.loads((PACKAGE / "data" / "demo_announcements.json").read_text())
DEMO_PRICES = json.loads((PACKAGE / "data" / "demo_prices.json").read_text())
PORTFOLIO_SYMBOLS = [c["symbol"] for c in PORTFOLIO]
CACHE: dict[tuple, tuple[float,list[dict]]] = {}
CACHE_LOCK = Lock()
LAST_FORCED_REFRESH = 0.0



def cached(key: tuple, lifespan: int, loader):
    now = time.monotonic()
    with CACHE_LOCK:
        value = CACHE.get(key)
        if value and now - value[0] < lifespan:
            return value[1]
    result = loader()
    with CACHE_LOCK:
        CACHE[key] = (time.monotonic(), result)
    return result


def requested_symbols(raw: str | None) -> list[str]:
    if not raw:
        return PORTFOLIO_SYMBOLS
    try:
        symbols = list(dict.fromkeys(validate_ticker(s) for s in raw.split(",") if s.strip()))
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    if not 1 <= len(symbols) <= 30:
        raise HTTPException(422,"Watchlist must have 1–30 symbols")
    return symbols


def validate_mode(mode: str):
    if mode not in ("demo", "live"):
        raise HTTPException(422,"mode must be demo or live")


@app.get("/")
def root():
    return FileResponse(PACKAGE / "static" / "index.html")


@app.get("/api/health")
def health():
    return {"ok":True,"version":"4.0.0","local_time":datetime.now(IST).isoformat()}


@app.post("/api/refresh")
def recheck_market_sources():
    """Visible Recheck button really invalidates quotes/filings caches.

    This unauthenticated prototype limits forced invalidations globally to once
    per 90 seconds to protect public endpoints from repeated expensive calls.
    """
    global LAST_FORCED_REFRESH
    now = time.monotonic()
    with CACHE_LOCK:
        remaining = 90 - (now - LAST_FORCED_REFRESH)
        if LAST_FORCED_REFRESH and remaining > 0:
            return {"accepted": False, "retry_after_seconds": int(remaining) + 1,
                    "message": "A source recheck already ran recently; cached results remain available."}
        LAST_FORCED_REFRESH = now
        CACHE.clear()
    return {"accepted": True, "message": "Cached source responses cleared; next requests will query providers again."}


@app.get("/api/portfolio")
def portfolio():
    return {"companies":PORTFOLIO,"count":len(PORTFOLIO),"ad_hoc_examples":["HCLTECH","PIDILITIND","DIXON","DIVISLAB"],"verified_primary_source_case":"INFY","research_demo":"DEMOCO is fictional and only demonstrates evidence retrieval"}


@app.get("/api/digest")
def digest(mode: str = "live", hours: int = Query(24, ge=1, le=720), symbols: str | None = None):
    validate_mode(mode)
    requested = requested_symbols(symbols)
    if mode == "demo":
        now = datetime.now(IST)
        items = [digest_event(e["symbol"],e["title"],e["detail"],None,now-timedelta(hours=e["age_hours"]),
                              demo=True, category=e["category"], why=e["why"])
                 for e in DEMO_EVENTS if e["symbol"] in requested and e["age_hours"] <= hours]
        return {"items":sorted(items,key=lambda e:(e["priority"],e["published_at"]),reverse=True),
                "mode":"demo","warning":"ILLUSTRATIVE SCENARIOS ONLY — not actual exchange filings or company events.",
                "fetched_at":None,"source":"synthetic demonstration fixtures"}
    try:
        items = cached(("filings",tuple(sorted(requested)),hours),180,
              lambda:fetch_announcements(requested,hours))
        return {"items":items,"mode":"live","warning":None,"fetched_at":datetime.now(IST).isoformat(),
                "source":"NSE public website (best-effort, may be delayed)"}
    except Exception as exc:
        return {"items":[],"mode":"live","warning":f"NSE feed unavailable: {type(exc).__name__}. No filings have been fabricated or substituted.",
                "fetched_at":None,"source":"NSE public website"}


@app.get("/api/prices")
def prices(mode: str = "live", symbols: str | None = None,
           price_threshold: float = Query(3.0,ge=0.1,le=40),
           volume_threshold: float = Query(2.0,ge=1,le=20)):
    validate_mode(mode)
    requested = requested_symbols(symbols)
    if mode == "demo":
        rows = [{**e,"demo":True,"date":None} for e in DEMO_PRICES if e["symbol"] in requested]
        warning = "ILLUSTRATIVE VALUES ONLY — these are not verified market prices or volumes."
        source = "synthetic demonstration fixtures"
    else:
        try:
            rows = cached(("prices",tuple(sorted(requested))),240,lambda:fetch_prices(requested))
            warning = (f"Public market data returned for {len(rows)} of {len(requested)} symbols; unavailable symbols are omitted."
                       if len(rows) != len(requested) else None)
            source = "Yahoo Finance historical EOD, with NSE public quote fallback when available (not streaming)"
        except Exception as exc:
            rows = []
            warning = f"Live EOD market data unavailable: {type(exc).__name__}. No prices were fabricated."
            source = "Yahoo Finance historical EOD / NSE public quotes"
    return {"items":rows,"alerts":market_alerts(rows,price_threshold,volume_threshold),
            "mode":mode,"source":source,"warning":warning,"fetched_at":datetime.now(IST).isoformat() if mode == "live" and rows else None}


@app.get("/api/research/documents")
def docs(ticker: str):
    try:
        return {"ticker":validate_ticker(ticker),"documents":store.list_docs(ticker)}
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc


@app.get("/api/research/documents/{document_id}/file")
def pdf_file(document_id: str):
    info = store.get_doc(document_id)
    if not info:
        raise HTTPException(404,"Document not found")
    return FileResponse(store.base / "pdfs" / f"{document_id}.pdf", media_type="application/pdf", filename=info["name"], content_disposition_type="inline")


@app.post("/api/research/upload")
async def upload(request: Request, ticker: str, name: str = "Source.pdf", kind: str = "annual_report"):
    if request.headers.get("content-length") and int(request.headers["content-length"]) > 20 * 1024 * 1024:
        raise HTTPException(413,"PDF exceeds the 20 MB limit")
    try:
        body = await request.body()
        return {"document":store.add_pdf(ticker,name,kind,body)}
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc


class ImportRequest(BaseModel):
    ticker: str
    name: str = "Company source.pdf"
    kind: str = "annual_report"
    url: str


@app.post("/api/research/import")
def import_pdf(payload: ImportRequest):
    try:
        data = fetch_public_pdf(payload.url)
        return {"document":store.add_pdf(payload.ticker,payload.name,payload.kind,data,url=payload.url)}
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc


@app.get("/api/research/discover")
def discover(ticker: str):
    try:
        return discover_sources(ticker)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc


class ResearchRequest(BaseModel):
    ticker: str
    question: str = Field(min_length=8,max_length=600)


@app.post("/api/research/ask")
def ask(payload: ResearchRequest):
    try:
        return store.analyze(validate_ticker(payload.ticker),payload.question)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc




@app.get("/api/case/{ticker}")
def verified_case(ticker: str):
    """Historical company-issued source pack: guaranteed to work without market APIs."""
    if validate_ticker(ticker) != 'INFY':
        raise HTTPException(404,"A pre-verified source case is available for INFY only; upload primary PDFs for other tickers")
    return infosys_case()


@app.get("/api/research/angles")
def analysis_angles(ticker: str, angle: str = "all"):
    try:
        return research_angles(store, ticker, angle)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


class FinancialPeriod(BaseModel):
    period: str = Field(min_length=2, max_length=60)
    revenue: float | None = None
    ebitda: float | None = None
    pbt: float | None = None
    pat: float | None = None
    unit: str = '₹ crore'


class ComparisonRequest(BaseModel):
    current: FinancialPeriod
    previous: FinancialPeriod
    year_ago: FinancialPeriod
    source_url: str = Field(min_length=10, max_length=1000)


@app.post("/api/results/compare")
def compare_quarterly_results(payload: ComparisonRequest):
    """Actual financial reconciliation is deterministic, not LLM arithmetic.

    User-supplied figures are labelled as such and must be checked against URL.
    Negative values are allowed (losses). Zero prior bases cannot yield growth.
    """
    if not payload.source_url.startswith('https://'):
        raise HTTPException(422,'Source must be an HTTPS company/exchange filing')
    periods=[payload.current,payload.previous,payload.year_ago]
    bases={p.unit for p in periods}
    if len(bases)!=1:
        raise HTTPException(422,'All periods must use the same reporting unit')
    result=compare_periods(*[p.model_dump() for p in periods])
    result.update({'provenance':'user_supplied_not_automatically_verified',
                   'source_url':payload.source_url,
                   'warning':'Check figures, dates, reporting entity and accounting basis against the original filing.'})
    return result


@app.get('/api/research/management')
def management_context(ticker: str):
    """Only biography evidence in ingested primary documents is presented.

    No unsupported professional histories/LinkedIn scraping.
    """
    try:
        ticker=validate_ticker(ticker)
        matches=store.evidence(ticker,'appointment director CEO CFO joined career background experience',limit=5)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    return {'ticker':ticker,'evidence':matches, 'mode':'primary_document_bio_search',
            'note':'No biography is asserted without sourced evidence. Open an official company bio or professional profile separately to verify the incoming executive.'}

@app.get("/api/chart")
def stock_chart(symbol: str, period: str = "3M", mode: str = "live"):
    validate_mode(mode)
    if period not in PERIODS:
        raise HTTPException(422, "Period must be 1D, 1M, 3M, 6M or 1Y")
    try:
        symbol = validate_ticker(symbol)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    if mode == "demo":
        price = next((p for p in DEMO_PRICES if p["symbol"] == symbol), None)
        if price is None:
            raise HTTPException(404,"No fictional chart for this symbol. Choose Live for supported NSE tickers.")
        return demo_chart(symbol, price["close"], price["change_pct"],period)
    try:
        return cached(("chart",symbol,period),300,lambda:live_chart(symbol,period))
    except Exception as exc:
        return JSONResponse(status_code=503,content={"detail":str(exc),"symbol":symbol,"mode":"live",
               "source":"Yahoo Finance historical chart; no fallback values or fabricated history"})


@app.get("/api/nse/quote")
def nse_quote(symbol: str):
    try:
        symbol = validate_ticker(symbol)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    try:
        return cached(("nse_quote",symbol),240,lambda:fetch_nse_quote(symbol))
    except Exception as exc:
        return JSONResponse(status_code=503,content={"detail":"NSE public quote endpoint unavailable on this host; try the exchange link.",
             "source_url":f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}","symbol":symbol,"mode":"unavailable"})
