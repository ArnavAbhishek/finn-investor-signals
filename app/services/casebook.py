"""A deliberately small, audited set of *real* primary-source issuer facts.

This is NOT a live price or filing feed. It is a dated, source-linked worked
example that runs during public-provider outages. Facts were verified from
Infosys' own annual report, Q3/Q4/Q1/Q2 fact sheets and Q2 conference call.
Never generalise case-specific facts to unrelated symbols.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Optional

SOURCES = {
    'annual': {'title': 'Infosys Integrated Annual Report FY2025–26', 'url': 'https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-26.pdf', 'kind': 'annual_report'},
    'financials': {'title': 'Infosys published three-year financial overview', 'url': 'https://www.infosys.com/investors/reports-filings/financials/data-sheet.html', 'kind': 'annual_financials'},
    'q3': {'title': 'Q3 FY26 corporate fact sheet', 'url': 'https://www.infosys.com/investors/reports-filings/quarterly-results/2025-2026/q3/documents/fact-sheet.pdf', 'kind': 'quarterly_results'},
    'q4': {'title': 'Q4 FY26 corporate fact sheet', 'url': 'https://www.infosys.com/investors/reports-filings/quarterly-results/2025-2026/q4/documents/fact-sheet.pdf', 'kind': 'quarterly_results'},
    'q1': {'title': 'Q1 FY27 corporate fact sheet', 'url': 'https://www.infosys.com/investors/reports-filings/quarterly-results/2026-2027/q1/documents/fact-sheet.pdf', 'kind': 'quarterly_results'},
    'q2': {'title': 'Q2 FY27 corporate fact sheet', 'url': 'https://www.infosys.com/investors/reports-filings/quarterly-results/2026-2027/q2/documents/fact-sheet.pdf', 'kind': 'quarterly_results'},
    'call': {'title': 'Q2 FY27 earnings-call transcript, 23 Oct 2026', 'url': 'https://www.infosys.com/investors/reports-filings/quarterly-results/2026-2027/q2/documents/transcripts/earningscall.pdf', 'kind': 'concall_transcript'},
    'results': {'title': 'Infosys Q2 FY27 investor results page', 'url': 'https://www.infosys.com/investors/reports-filings/quarterly-results/2026-2027/q2.html', 'kind': 'results_filing'},
}

# Consolidated IFRS in INR crore. No EBITDA: company-supplied Operating
# Profit is NOT silently relabelled as EBITDA. Q3 & Q4 from Q4 fact sheet p5;
# Q1 from Q1 fact sheet p3; Q2 from Q2 fact sheet p4.
QUARTERS = [
    {'period':'Q3 FY26','ended':'2025-12-31','revenue':45479,'operating_profit':8355,'pbt':9229,'pat':6654,'operating_margin_pct':18.4,'source':'q4','page':5},
    {'period':'Q4 FY26','ended':'2026-03-31','revenue':46402,'operating_profit':9743,'pbt':10797,'pat':8501,'operating_margin_pct':21.0,'source':'q4','page':5},
    {'period':'Q1 FY27','ended':'2026-06-30','revenue':48211,'operating_profit':10163,'pbt':11028,'pat':7769,'operating_margin_pct':21.1,'source':'q1','page':3},
    {'period':'Q2 FY27','ended':'2026-09-30','revenue':49244,'operating_profit':10330,'pbt':11063,'pat':7823,'operating_margin_pct':21.0,'source':'q2','page':4},
]

ANGLES = ['business','financial','trajectory','balance','cash','narrative','guidance','bullbear']
ANGLE_TITLES = {
    'business':'Business snapshot', 'financial':'Financial snapshot',
    'trajectory':'Performance trajectory','balance':'Balance-sheet health',
    'cash':'Cash quality', 'narrative':'Narrative vs numbers',
    'guidance':'Management guidance','bullbear':'Bull vs bear'
}

def cite(source: str, page: Optional[int] = None) -> dict:
    return {**SOURCES[source], 'page': page, 'url': SOURCES[source]['url'] + (f'#page={page}' if page and SOURCES[source]['url'].lower().endswith('.pdf') else '')}

def delta(now: Optional[float], before: Optional[float]) -> Optional[float]:
    """Avoid false growth rates around zero or missing baselines."""
    if now is None or before in (None, 0):
        return None
    return round((now - before) * 100 / abs(before), 2)

def compare_periods(current: dict, previous: dict, year_ago: dict) -> dict:
    """Deterministic, audit-friendly quarter comparisons with explicit caveats."""
    result=[]
    for key, label in [('revenue','Revenue'),('ebitda','EBITDA'),('pbt','PBT'),('pat','PAT')]:
        val=current.get(key); prev=previous.get(key); old=year_ago.get(key)
        result.append({'metric':key,'label':label, 'current':val, 'previous':prev, 'year_ago':old,
                       'qoq_pct':delta(val,prev), 'yoy_pct':delta(val,old),
                       'available': val is not None and prev is not None and old is not None})
    return {'current':current.get('period'),'previous':previous.get('period'),
            'year_ago':year_ago.get('period'),'unit':current.get('unit','₹ crore'),
            'rows':result, 'notes':[
                'Compare the same reporting basis (consolidated vs standalone, IFRS vs Ind AS).',
                'EBITDA is not substituted with operating profit; provide a verifiable EBITDA source.',
                'QoQ/YoY use (current − comparison) ÷ absolute(comparison) × 100; zero bases are unavailable.'
            ]}

def infosys_case() -> dict:
    q2=QUARTERS[-1];q1=QUARTERS[-2]
    last_year={'period':'Q2 FY26','unit':'₹ crore','revenue':44490,'ebitda':None,'pbt':10229,'pat':7364}
    latest={**q2,'ebitda':None,'unit':'₹ crore'}
    prev={**q1,'ebitda':None,'unit':'₹ crore'}
    numbers=compare_periods(latest,prev,last_year)
    evidence = {
        'business': [
            {'text':'Financial Services accounts for 28.0% of Q2 FY27 revenue, Manufacturing 16.0%, and Energy/Utilities/Resources/Services 14.2%.', 'source':'q2','page':1},
            {'text':'Infosys provides technology consulting, digital transformation and AI-led services to global enterprises.', 'source':'annual'}
        ],
        'financial': [
            {'text':'Q2 FY27 revenue ₹49,244 crore; reported operating profit ₹10,330 crore; PBT ₹11,063 crore; net profit ₹7,823 crore. Reported operating margin 21.0%.', 'source':'q2','page':4},
            {'text':'The source does not separately state an EBITDA figure on the extracted fact sheet. Operating profit is shown separately, not relabelled.', 'source':'q2','page':4}
        ],
        'trajectory': [
            {'text':'Reported quarterly revenue increased over the last four disclosed quarters from ₹45,479 crore (Q3 FY26) to ₹49,244 crore (Q2 FY27).', 'source':'q4','page':5},
            {'text':'The reported margin dip to 18.4% in Q3 FY26 includes a labour-code provision; Q2 FY27 reported margin is 21.0%. Avoid assuming a like-for-like underlying change without adjustment.', 'source':'q4','page':5}
        ],
        'balance': [
            {'text':'The FY26 company financial overview reports cash and cash equivalents ₹22,201 crore, current investments ₹12,950 crore, and total equity ₹93,297 crore.', 'source':'financials'},
            {'text':'The company’s published overview has no value for its debt-to-equity ratio; this brief does not invent one.', 'source':'financials'}
        ],
        'cash': [
            {'text':'Infosys reports FY26 free cash flow ₹33,097 crore and FCF conversion at 112.3% of net profit.', 'source':'annual'},
            {'text':'On the Q2 FY27 earnings call the CFO discussed quarterly free cash flow of US$928 million, equal to 113% of reported net profit.', 'source':'call','page':3}
        ],
        'narrative': [
            {'text':'Management said client spending remained cautious and quarterly growth was below expectations; this is consistent with the stated downward revision in FY27 constant-currency growth guidance.', 'source':'call','page':3},
            {'text':'Q2 FY27 reported INR revenue nevertheless grew 2.1% QoQ; INR growth is not interchangeable with constant-currency growth.', 'source':'q2','page':4}
        ],
        'guidance': [
            {'text':'On 23 Oct 2026 management revised FY27 constant-currency revenue growth guidance to 1%–2% YoY and retained operating margin guidance of 20%–22%.', 'source':'call','page':3},
            {'text':'As of this Q2 FY27 disclosure, the FY27 outcome is not yet available; the annual target cannot honestly be marked met or missed.', 'source':'call','page':3}
        ],
        'bullbear': [
            {'text':'Bull evidence: 10.5% of Q2 FY27 revenue was described as AI-related and large-deal TCV was US$5.2 billion on the company’s call.', 'source':'call','page':2},
            {'text':'Bear evidence: management acknowledged spending caution and revised FY27 growth guidance downward to 1%–2%.', 'source':'call','page':3}
        ]
    }
    content = []
    for angle in ANGLES:
        content.append({'id':angle,'title':ANGLE_TITLES[angle],
                        'findings':[{'text':e['text'],'citation':cite(e['source'],e.get('page'))} for e in evidence[angle]]})
    return {
        'ticker':'INFY','company':'Infosys Limited',
        'kind':'verified_historical_case', 'as_of':'2026-10-23',
        'unit':'₹ crore, consolidated IFRS except where specified',
        'not_live':True, 'quarters':QUARTERS, 'headlines':numbers,
        'angles':content, 'sources':[{'key':k,**cite(k)} for k in SOURCES],
        'guidance':{'revenue_growth_cc_pct':[1,2],'operating_margin_pct':[20,22],
                    'horizon':'FY27 (year ending March 2027)', 'status':'outcome not yet reported','citation':cite('call',3)},
        'annual':{'fy26_revenue':178650, 'fy25_revenue':162990,'fy26_fcf':33097,
                  'fy26_roe_pct':31.6,'source':cite('annual')},
        'caveats':['Not live; stored official-document facts, last updated after Infosys Q2 FY27 results.',
                   'Company-reported operating profit is NOT an EBITDA figure.',
                   'FY27 annual guidance and quarterly growth use different time horizons and cannot be directly scored.',
                   'Values come from company primary sources, not a broker model.']
    }
