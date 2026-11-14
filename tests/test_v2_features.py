"""Version 2 paths: deterministic chart and fail-closed provider handling."""
from fastapi.testclient import TestClient
from app.main import app
from app.services.market import _one_nse
from app.services.charts import demo_chart

client=TestClient(app)

def test_chart_is_explicit_demo_and_stable():
    a=client.get('/api/chart?symbol=RELIANCE&period=3M&mode=demo')
    assert a.status_code==200
    data=a.json()
    assert data['mode']=='demo'
    assert 'synthetic' in data['source'].lower()
    assert len(data['points'])>=40
    assert data['points'][-1]['close']==1380.5
    assert data==client.get('/api/chart?symbol=RELIANCE&period=3M&mode=demo').json()

def test_chart_rejects_unknown_range_and_demo_symbol():
    assert client.get('/api/chart?symbol=RELIANCE&period=5Y&mode=demo').status_code==422
    assert client.get('/api/chart?symbol=NOTREAL&period=3M&mode=demo').status_code==404

def test_nse_fallback_does_not_fake_volume_average(monkeypatch):
    import app.services.market as market
    monkeypatch.setattr(market,'fetch_nse_quote',lambda symbol:{'data':{
        'orderBook':{'lastPrice':102.5},'metaData':{'previousClose':100},
        'lastUpdateTime':'14-Nov-2026 15:30:00'}})
    row=_one_nse('TEST')
    assert row['close']==102.5
    assert row['change_pct']==2.5
    assert row['volume_ratio'] is None
    assert row['provider'].startswith('NSE')

def test_live_chart_failure_never_becomes_demo(monkeypatch):
    import app.main as main
    def fail(*args,**kwargs): raise RuntimeError('simulated provider outage')
    monkeypatch.setattr(main,'live_chart',fail)
    resp=client.get('/api/chart?symbol=RELIANCE&period=1M&mode=live')
    assert resp.status_code==503
    assert resp.json()['mode']=='live'
    assert 'no fallback values' in resp.json()['source']
