from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.signals import classify, score, tier, parse_nse_date, market_alerts
from app.services.market import compute_eod_signal
from app.services.announcements import normalize_row


def test_category_and_priority():
    assert classify('CFO resignation under Regulation 30') == 'management_change'
    assert classify('Unaudited financial results for the quarter') == 'results'
    assert classify('Order approved for acquisition of subsidiary') == 'M&A'
    assert classify('Annual general meeting notice') == 'agm_egm'
    assert classify('Routine compliance certificate') == 'unclassified'
    assert tier(score('results')) == 'high'
    assert tier(score('unclassified')) == 'routine'


def test_date_and_source_validation():
    assert parse_nse_date('11-Nov-2026 14:30:00').tzinfo is not None
    assert parse_nse_date('not-a-date') is None
    row = {'symbol':'RELIANCE','desc':'Financial Results for the Quarter','an_dt':'11-Nov-2026 14:30:00','attchmntFile':'https://evil.test/file.pdf'}
    event=normalize_row(row)
    assert event['source_url'] is None
    assert event['demo'] is False
    assert event['tier'] == 'high'


def test_eod_excludes_current_volume_from_average():
    rows=[{'date':str(i),'close':100+i,'volume':1000} for i in range(6)]
    rows[-1]['volume']=2500
    r=compute_eod_signal('TEST',rows)
    assert r['volume_ratio']==2.5
    assert r['change_pct']==round((105/104-1)*100,2)


def test_rule_thresholds_are_configurable():
    prices=[{'symbol':'TEST','change_pct':-3.2,'volume_ratio':2.4,'demo':True}]
    assert len(market_alerts(prices,3,2))==1
    assert market_alerts(prices,4,3)==[]
