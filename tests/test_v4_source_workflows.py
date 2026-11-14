from fastapi.testclient import TestClient
from app.main import app
from app.services.casebook import compare_periods, infosys_case
from app.services.angles import research_angles
from app.services.signals import BASE_PRIORITY

client=TestClient(app)

def test_company_case_has_real_source_provenance():
    r=client.get('/api/case/INFY')
    assert r.status_code==200
    data=r.json()
    assert data['kind']=='verified_historical_case' and data['not_live']
    assert len(data['quarters'])==4
    assert data['quarters'][-1]['revenue']==49244
    assert all(s['url'].startswith('https://www.infosys.com/') for s in data['sources'])


def test_four_quarter_results_are_reconciled_not_hallucinated():
    data=infosys_case()['headlines']
    rev=next(x for x in data['rows'] if x['metric']=='revenue')
    ebidta=next(x for x in data['rows'] if x['metric']=='ebitda')
    assert rev['qoq_pct']==2.14 and rev['yoy_pct']==10.69
    assert not ebidta['available'] and ebidta['current'] is None


def test_all_eight_lenses_are_cited():
    data=client.get('/api/research/angles?ticker=INFY').json()
    assert len(data['angles'])==8
    assert all(angle['findings'] for angle in data['angles'])
    assert all(f['citation']['url'].startswith('https://www.infosys.com') for a in data['angles'] for f in a['findings'])


def test_adhoc_ticker_without_sources_does_not_guess():
    data=client.get('/api/research/angles?ticker=DIXON').json()
    assert data['status']=='no_documents'
    assert all(not x['findings'] for x in data['angles'])


def test_all_17_categories_implemented():
    assert len(BASE_PRIORITY)==17


def test_user_numbers_require_source_and_consistent_units():
    sample={'current':{'period':'Q2','unit':'₹ crore','revenue':120},
      'previous':{'period':'Q1','unit':'₹ crore','revenue':100},
      'year_ago':{'period':'Q2 prior year','unit':'₹ crore','revenue':80},
      'source_url':'https://company.in/result.pdf'}
    r=client.post('/api/results/compare',json=sample)
    assert r.status_code==200 and r.json()['rows'][0]['qoq_pct']==20
    sample['previous']['unit']='USD'
    assert client.post('/api/results/compare',json=sample).status_code==422


def test_negative_baseline_and_zero_baseline_are_safe():
    r=compare_periods({'period':'Q2','pat':-50},{'period':'Q1','pat':-100},{'period':'Q2 last year','pat':0})
    pat=next(x for x in r['rows'] if x['metric']=='pat')
    assert pat['qoq_pct']==50.0
    assert pat['yoy_pct'] is None


def test_lenses_invalid_angle_rejected():
    assert client.get('/api/research/angles?ticker=INFY&angle=madeup').status_code==422
