from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_home_and_health():
    assert client.get('/').status_code==200
    assert 'FINN' in client.get('/').text
    assert client.get('/api/health').json()['ok']
    portfolio=client.get('/api/portfolio').json()
    assert portfolio['count']==18


def test_demo_is_explicitly_synthetic():
    digest=client.get('/api/digest?mode=demo&hours=24').json()
    assert digest['mode']=='demo'
    assert all(d['demo'] and d['source_url'] is None for d in digest['items'])
    assert 'ILLUSTRATIVE' in digest['warning']
    market=client.get('/api/prices?mode=demo&price_threshold=3&volume_threshold=2').json()
    assert all(p['demo'] for p in market['items'])
    assert len(market['alerts'])>0


def test_live_failure_cannot_fall_back_to_fake(monkeypatch):
    import app.main as main
    def fail(*args,**kwargs):
        raise ConnectionError('intentionally offline')
    monkeypatch.setattr(main,'fetch_announcements',fail)
    live=client.get('/api/digest?mode=live&hours=24').json()
    assert live['items']==[]
    assert 'No filings have been fabricated' in live['warning']


def test_invalid_mode_and_ticker():
    assert client.get('/api/digest?mode=fantasy').status_code==422
    assert client.get('/api/digest?symbols=../etc').status_code==422
    assert client.post('/api/research/ask',json={'ticker':'RELIANCE','question':'short'}).status_code==422
