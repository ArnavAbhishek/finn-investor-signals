"""Verified historical NSE-listed stock prices and explicitly synthetic preview charts.

The Yahoo v8 chart API uses 1mo/3mo/6mo, not 1m/3m/6m; 1D requests
intraday intervals. Our UI falls back to an attributed external chart widget
rather than drawing made-up 'live' prices when providers reject hosting IPs.
"""
from __future__ import annotations
from datetime import date, timedelta, datetime, timezone
import hashlib
import math
import random
import requests

PERIODS = {
    '1D': ('5d', '15m'),  # last trading session, including non-trading days
    '1M': ('1mo', '1d'),
    '3M': ('3mo', '1d'),
    '6M': ('6mo', '1d'),
    '1Y': ('1y', '1d'),
}
RANGE_DAYS = {'1D': 1, '1M': 31, '3M': 93, '6M': 186, '1Y': 366}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json,text/plain,*/*',
}


def demo_chart(symbol: str, closing: float, change_pct: float, period: str) -> dict:
    """Preview-only seeded curve. Never returned as live data."""
    if period not in PERIODS:
        raise ValueError('Invalid range')
    seed = int(hashlib.sha256(symbol.encode()).hexdigest()[:12],16)
    rng = random.Random(seed)
    today = date.today()
    dates = [today - timedelta(days=n) for n in range(365, -1, -1)]
    dates = [d for d in dates if d.weekday() < 5]
    v = 100.0
    rows = []
    for day in dates:
        v *= 1.00045 + rng.gauss(0, 0.011)
        rows.append({'date': day.isoformat(), 'close': v, 'volume': rng.randint(300000, 2500000)})
    rows[-1]['close'] = rows[-2]['close'] * (1 + change_pct / 100)
    multiplier = closing / rows[-1]['close']
    for r in rows:
        r['close'] = round(r['close'] * multiplier, 2)
    if period == '1D':
        # Never imply the fictional points are minute-by-minute exchange data.
        rows = [rows[-2], rows[-1]]
    elif period != '1Y':
        cut = (today - timedelta(days=RANGE_DAYS[period])).isoformat()
        rows = [r for r in rows if r['date'] >= cut]
    return {'symbol': symbol, 'period': period, 'points': rows, 'mode': 'demo',
            'source': 'Synthetic illustrative scenario', 'warning': 'Fictional chart; not NSE trading history.',
            'updated_at': None, 'close': closing, 'change_pct': change_pct}


def yahoo_params(period: str) -> dict:
    """Always map product labels to supported Yahoo API range/interval pairs."""
    if period not in PERIODS:
        raise ValueError('Invalid chart period')
    range_value, interval = PERIODS[period]
    return {'range': range_value, 'interval': interval, 'events': 'false'}


def parse_yahoo_chart(response: dict, symbol: str, period: str, provider: str) -> dict:
    frames = (response.get('chart') or {}).get('result') or []
    if not frames:
        raise ValueError('No chart records')
    row = frames[0]
    stamps = row.get('timestamp') or []
    quote = (row.get('indicators') or {}).get('quote') or []
    if not quote:
        raise ValueError('No OHLCV fields')
    closes = quote[0].get('close') or []
    vols = quote[0].get('volume') or []
    observations = []
    for idx, stamp in enumerate(stamps):
        if idx >= len(closes) or closes[idx] is None:
            continue
        try:
            close = float(closes[idx])
            if not math.isfinite(close) or close <= 0:
                continue
            # Yahoo timestamps are UTC seconds; daily bar dates are most useful in IST.
            when = datetime.fromtimestamp(stamp, timezone.utc)
            observations.append({'date': when.isoformat() if period=='1D' else when.date().isoformat(),
                                 'close': round(close, 2),
                                 'volume': int(vols[idx] or 0) if idx < len(vols) else 0})
        except (ValueError, TypeError, OverflowError):
            continue
    previous_session_close = None
    if period == '1D' and observations:
        # 1D means the last *session*, but daily change must use the previous
        # session close rather than the previous 15-minute bar.
        from zoneinfo import ZoneInfo
        ist = ZoneInfo('Asia/Kolkata')
        last_date = datetime.fromisoformat(observations[-1]['date']).astimezone(ist).date()
        previous_sessions = [p for p in observations
            if datetime.fromisoformat(p['date']).astimezone(ist).date() < last_date]
        if previous_sessions:
            previous_session_close = previous_sessions[-1]['close']
        else:
            meta = row.get('meta') or {}
            previous_session_close = meta.get('chartPreviousClose') or meta.get('previousClose')
        observations = [p for p in observations
            if datetime.fromisoformat(p['date']).astimezone(ist).date() == last_date]
    if len(observations) < 2:
        raise ValueError('Fewer than two valid chart points')
    last, prior = observations[-1], observations[-2]
    return {'symbol': symbol, 'period': period, 'points': observations, 'mode': 'live',
            'source': provider, 'warning': 'Historical exchange-session data; not a streaming quote.',
            'updated_at': last['date'], 'close': last['close'],
            'change_pct': (round((last['close'] / previous_session_close - 1) * 100, 2)
                           if period=='1D' and previous_session_close else
                           (None if period=='1D' else round((last['close'] / prior['close'] - 1) * 100, 2)))}


def _direct_yahoo(symbol: str, period: str) -> dict:
    params = yahoo_params(period)
    for host in ('query1.finance.yahoo.com', 'query2.finance.yahoo.com'):
        try:
            response = requests.get(f'https://{host}/v8/finance/chart/{symbol}.NS',
                                    params=params, headers=HEADERS, timeout=7)
            response.raise_for_status()
            return parse_yahoo_chart(response.json(), symbol, period, 'Yahoo Finance · NSE historical prices')
        except (requests.RequestException, ValueError, TypeError, KeyError, IndexError):
            continue
    raise RuntimeError('Yahoo chart endpoint did not return usable observations')


def live_chart(symbol: str, period: str) -> dict:
    yahoo_params(period)
    try:
        return _direct_yahoo(symbol, period)
    except RuntimeError:
        pass
    try:
        import yfinance as yf
        ticker = yf.Ticker(f'{symbol}.NS')
        # yfinance .history accepts 1d, 1mo, 3mo, etc.
        p, interval = PERIODS[period]
        frame = ticker.history(period=p, interval=interval, auto_adjust=False, actions=False, timeout=8)
        if frame is None or frame.empty:
            raise ValueError('Empty data frame')
        items = []
        for when, row in frame.iterrows():
            close = float(row['Close'])
            if math.isfinite(close) and close > 0:
                items.append({'date': when.isoformat() if period=='1D' else when.date().isoformat(),
                              'close': round(close, 2), 'volume': int(row['Volume'] or 0)})
        previous_session_close = None
        if period == '1D' and items:
            latest_session = datetime.fromisoformat(items[-1]['date']).date()
            earlier = [r for r in items if datetime.fromisoformat(r['date']).date() < latest_session]
            previous_session_close = earlier[-1]['close'] if earlier else None
            items = [r for r in items if datetime.fromisoformat(r['date']).date() == latest_session]
        if len(items) < 2:
            raise ValueError('Insufficient observations')
        last, prev = items[-1], items[-2]
        return {'symbol': symbol, 'period': period, 'points': items, 'mode': 'live',
                'source': 'Yahoo Finance via yfinance · NSE historical prices',
                'warning': 'Historical exchange-session data; not a streaming quote.',
                'updated_at': last['date'], 'close': last['close'],
                'change_pct': (round((last['close'] / previous_session_close - 1) * 100, 2)
                               if period=='1D' and previous_session_close else
                               (None if period=='1D' else round((last['close'] / prev['close'] - 1) * 100, 2)))}
    except Exception as exc:
        raise RuntimeError('No historical chart available from market data providers on this host') from exc
