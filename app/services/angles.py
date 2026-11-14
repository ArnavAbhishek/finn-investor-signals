"""Eight explainable Pull analysis lenses over primary source documents."""
from __future__ import annotations
from .casebook import ANGLES, ANGLE_TITLES, infosys_case
from .research import ResearchStore, validate_ticker

PROMPTS = {
  'business':'business overview segments revenue mix products customers services',
  'financial':'financial results revenue profit after tax operating margin earnings per share return on equity',
  'trajectory':'annual revenue growth profitability margins five year trend recent quarter',
  'balance':'balance sheet borrowings debt to equity working capital inventory receivables payables',
  'cash':'cash from operations free cash flow capital expenditure cash conversion net profit',
  'narrative':'management commentary growth expectations results delivered management forecast',
  'guidance':'revenue guidance margin outlook capex expectation projection next financial year',
  'bullbear':'risks headwinds drivers opportunities demand competition execution challenges'
}

def research_angles(store: ResearchStore, ticker: str, lens: str = 'all') -> dict:
    ticker=validate_ticker(ticker)
    if lens not in ANGLES and lens!='all':
        raise ValueError('Unknown research angle')
    requested=ANGLES if lens=='all' else [lens]
    if ticker=='INFY':
        verified=infosys_case()
        return {'ticker':ticker,'status':'official_source_case','as_of':verified['as_of'],
                'source_mode':'Dated, manually verified excerpts from Infosys primary-source company documents',
                'angles':[x for x in verified['angles'] if x['id'] in requested]}
    docs=store.list_docs(ticker)
    if not docs:
        return {'ticker':ticker,'status':'no_documents','source_mode':'No company-specific documents indexed',
                'angles':[{'id':x,'title':ANGLE_TITLES[x],'findings':[],'insufficient':True} for x in requested]}
    output=[]
    for angle in requested:
        found=store.evidence(ticker,PROMPTS[angle],limit=3)
        output.append({'id':angle,'title':ANGLE_TITLES[angle],
                       'findings':[{'text':row['excerpt'][:380]+'…' if len(row['excerpt'])>380 else row['excerpt'],
                                   'citation':{'title':row['document_name'],'kind':row['kind'],
                                   'page':row['page'],'url':row['source_url'] or f"/api/research/documents/{row['document_id']}/file#page={row['page']}"},
                                   'verbatim_source_excerpt':True} for row in found],
                       'insufficient':not bool(found)})
    return {'ticker':ticker,'status':'primary_pdf_evidence','source_mode':'Extractive only: these are retrieved snippets, NOT verified analyst conclusions',
            'angles':output}
