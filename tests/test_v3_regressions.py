"""Regression tests for the exact v2 issues the user reported."""
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import app.main as main
from app.services import charts, nse_quote

client = TestClient(main.app)


def test_yahoo_month_labels_are_not_invalid_short_forms():
    assert charts.yahoo_params('1M') == {'range':'1mo','interval':'1d','events':'false'}
    assert charts.yahoo_params('3M')['range'] == '3mo'
    assert charts.yahoo_params('6M')['range'] == '6mo'
    assert charts.yahoo_params('1Y')['range'] == '1y'
    assert charts.yahoo_params('1D')['interval'] == '15m'


def test_yahoo_daily_ranges_retrieve_and_parse_all_periods(monkeypatch):
    calls = []
    class FakeResponse:
        def raise_for_status(self): pass
        def json(self):
            base = datetime(2026,10,1,tzinfo=timezone.utc)
            stamps = [int((base+timedelta(days=i)).timestamp()) for i in range(6)]
            return {'chart':{'result':[{'timestamp':stamps, 'indicators':{'quote':[{
                'close':[100,102,99,104,105,106], 'volume':[12,10,14,16,11,18]
            }]}}]}}
    def fake_get(url, params, headers, timeout):
        calls.append(params.copy())
        return FakeResponse()
    monkeypatch.setattr(charts.requests,'get',fake_get)
    for p in ('1M','3M','6M','1Y'):
        r=charts.live_chart('RELIANCE',p)
        assert len(r['points'])==6
        assert r['mode']=='live'
        assert r['points'][-1]['close']==106.0
    assert [p['range'] for p in calls]==['1mo','3mo','6mo','1y']


def test_one_day_chart_uses_only_latest_session(monkeypatch):
    class FakeResponse:
        def raise_for_status(self): pass
        def json(self):
            days = [datetime(2026,11,12,4,tzinfo=timezone.utc),
                    datetime(2026,11,12,5,tzinfo=timezone.utc),
                    datetime(2026,11,13,4,tzinfo=timezone.utc),
                    datetime(2026,11,13,5,tzinfo=timezone.utc)]
            return {'chart':{'result':[{'timestamp':[int(x.timestamp()) for x in days],
                       'indicators':{'quote':[{'close':[90,92,95,97],'volume':[1,2,3,4]}]}}]}}
    monkeypatch.setattr(charts.requests,'get',lambda *args,**kwargs:FakeResponse())
    result=charts.live_chart('TCS','1D')
    assert len(result['points'])==2
    assert result['points'][-1]['close']==97
    # Daily change against previous session close (92), NOT the prior intraday bar (95).
    assert result['change_pct'] == 5.43
    assert '2026-11-13' in result['points'][0]['date']


def test_forced_refresh_invalidates_cached_source_records():
    with main.CACHE_LOCK:
        main.LAST_FORCED_REFRESH=0
        main.CACHE[('prices',('RELIANCE',))]=(0,[{'fake':1}])
    r=client.post('/api/refresh')
    assert r.status_code==200 and r.json()['accepted']
    assert ('prices',('RELIANCE',)) not in main.CACHE
    again=client.post('/api/refresh')
    assert again.json()['accepted'] is False
    assert again.json()['retry_after_seconds']>0


def test_custom_ticker_supported_on_quote_endpoint():
    requested=main.requested_symbols('DIXON,IRCTC,RELIANCE')
    assert requested==['DIXON','IRCTC','RELIANCE']


def test_quote_normalizer_does_not_invent_ohlcv():
    old={'priceInfo':{'lastPrice':420,'close':413,'intraDayHighLow':{'max':425,'min':411}},'metadata':{'symbol':'TEST'}}
    v=nse_quote._normalize_old(old)
    assert v['orderBook']['lastPrice']==420
    assert v['metaData']['previousClose']==413
    assert v['raw']==old
    assert 'volumeRatio' not in v


def test_app_v3_health_and_period_acceptance():
    assert client.get('/api/health').json()['version']=='4.0.0'
    for period in ('1D','1M','3M','6M','1Y'):
        response=client.get('/api/chart',params={'symbol':'RELIANCE','period':period,'mode':'demo'})
        assert response.status_code==200
        assert response.json()['mode']=='demo'
    assert client.get('/api/chart',params={'symbol':'RELIANCE','period':'7Y','mode':'demo'}).status_code==422
