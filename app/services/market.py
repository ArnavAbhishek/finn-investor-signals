"""Best-effort EOD price & volume retrieval for NSE-listed symbols.

Primary: Yahoo Finance (.NS) historical close and traded volume. Fallback:
NSE's public quote website (last recorded quote, no fabricated volume ratio).
No streaming, no exchange-subscribed price feed, no guarantee on Render.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import math

from .charts import live_chart
from .nse_quote import fetch_nse_quote


def compute_eod_signal(symbol: str, rows: list[dict]) -> dict | None:
    """Use two last daily observations, and a 20-session volume baseline excluding latest."""
    valid = [r for r in rows if r.get('close') is not None and r.get('volume') is not None and float(r['close']) > 0]
    if len(valid) < 6:
        return None
    last, previous = valid[-1], valid[-2]
    recent = [float(x['volume']) for x in valid[-21:-1] if float(x['volume']) > 0]
    avg_vol = sum(recent)/len(recent) if recent else None
    change = (float(last['close'])/float(previous['close'])-1)*100
    ratio = float(last['volume'])/avg_vol if avg_vol else None
    return {'symbol':symbol,'close':round(float(last['close']),2),
            'change_pct':round(change,2),'volume_ratio':round(ratio,2) if ratio is not None else None,
            'date':str(last.get('date') or ''),'demo':False,'provider':'Yahoo Finance (historical EOD)'}


def _one_yahoo(symbol: str) -> dict | None:
    history=live_chart(symbol,'3M')
    return compute_eod_signal(symbol,history['points'])


def _first_number(*values):
    for value in values:
        if value is None or isinstance(value,bool): continue
        try:
            number=float(str(value).replace(',',''))
            if math.isfinite(number) and number>0: return number
        except (ValueError,TypeError): pass
    return None


def _one_nse(symbol: str) -> dict | None:
    data=fetch_nse_quote(symbol)['data']
    book=data.get('orderBook') or {}
    meta=data.get('metaData') or {}
    info=data.get('priceInfo') or {}
    close=_first_number(book.get('lastPrice'), info.get('lastPrice'))
    if close is None: return None
    prev=_first_number(meta.get('previousClose'),meta.get('prevClose'),info.get('close'),book.get('close'))
    delta=round((close/prev-1)*100,2) if prev else None
    # A single quote does not give a 20-session volume average; never invent it.
    return {'symbol':symbol,'close':round(close,2),'change_pct':delta,
            'volume_ratio':None,'date':str(data.get('lastUpdateTime') or ''),
            'demo':False,'provider':'NSE public quote website (unofficial endpoint)'}


def fetch_prices(symbols: list[str]) -> list[dict]:
    """Request history first; missing symbols may be recovered from NSE website.

    Individual failures are represented as missing data, not made-up zero changes.
    """
    quotes={}
    with ThreadPoolExecutor(max_workers=5) as pool:
        jobs={pool.submit(_one_yahoo,s):s for s in symbols}
        for job in as_completed(jobs):
            try:
                row=job.result()
                if row: quotes[row['symbol']]=row
            except Exception: pass
    missing=[s for s in symbols if s not in quotes]
    if missing:
        with ThreadPoolExecutor(max_workers=4) as pool:
            jobs={pool.submit(_one_nse,s):s for s in missing}
            for job in as_completed(jobs):
                try:
                    row=job.result()
                    if row: quotes[row['symbol']]=row
                except Exception: pass
    if not quotes:
        raise RuntimeError('Both Yahoo EOD history and NSE website quotes were unavailable; no values substituted.')
    return sorted(quotes.values(),key=lambda x:x['symbol'])
