"""NSE public website quote adapter (experimental; not a licensed developer feed).

NSE periodically changes their site endpoints and may deny cloud IPs. Try two
publicly visible website formats; never bypass the exchange's access controls.
"""
from __future__ import annotations
import requests
from urllib.parse import quote

BASE = 'https://www.nseindia.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json,text/plain,*/*',
    'Accept-Language': 'en-IN,en;q=0.9',
    'Referer': f'{BASE}/get-quotes/equity',
}


def _normalize_old(data: dict) -> dict | None:
    """Original NSE public page format: priceInfo, metadata, securityInfo."""
    price = data.get('priceInfo')
    if not isinstance(price, dict) or not price.get('lastPrice'):
        return None
    # Preserve the payload, but put expected fields in a stable output shape.
    return {'priceInfo': price, 'metaData': {'previousClose': price.get('previousClose') or price.get('close'),
                                              'dayHigh': (price.get('intraDayHighLow') or {}).get('max'),
                                              'dayLow': (price.get('intraDayHighLow') or {}).get('min')},
            'orderBook': {'lastPrice': price.get('lastPrice')},
            'raw': data}


def fetch_nse_quote(symbol: str) -> dict:
    s = requests.Session()
    s.headers.update(HEADERS)
    errors = []
    candidates = [
        (f'{BASE}/api/quote-equity', {'symbol': symbol}),
        (f'{BASE}/api/NextApi/apiClient/GetQuoteApi', {'functionName':'getSymbolData', 'marketType':'N','series':'EQ','symbol':symbol}),
    ]
    for idx, (endpoint, params) in enumerate(candidates):
        try:
            response = s.get(endpoint, params=params, timeout=7)
            if response.status_code in (401,403) and idx == 0:
                # The normal public site landing page supplies a session cookie.
                try: s.get(f'{BASE}/get-quotes/equity?symbol={quote(symbol)}',timeout=5)
                except requests.RequestException: pass
                response = s.get(endpoint,params=params,timeout=7)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data,dict):
                errors.append('non-object quote response');continue
            if idx==0:
                normal = _normalize_old(data)
                if normal is None: errors.append('quote missing priceInfo');continue
            else:
                rows = data.get('equityResponse')
                if not isinstance(rows,list) or not rows or not isinstance(rows[0],dict):
                    errors.append('quote missing equityResponse');continue
                normal = rows[0]
            return {'symbol':symbol, 'source':'NSE website public quote interface (unofficial)',
                    'data':normal,'source_url':f'{BASE}/get-quotes/equity?symbol={quote(symbol)}',
                    'notice':'Raw source fields included for verification; may be delayed.'}
        except (requests.RequestException,ValueError,KeyError) as exc:
            errors.append(type(exc).__name__)
    raise RuntimeError('NSE quote source unavailable; both public website formats failed')
