"""Run a quick reviewer-style smoke test against an actual FINN deployment.

Usage: python scripts/verify_deployment.py --base https://YOUR-SERVICE.onrender.com
This deliberately treats external NSE/Yahoo access as a warning, not a guaranteed pass.
"""
from __future__ import annotations
import argparse
import json
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import URLError


def get(base: str, path: str):
    with urlopen(base.rstrip('/')+path, timeout=20) as response:
        return json.loads(response.read().decode())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8000')
    args=parser.parse_args()
    base=args.base
    checks=[
        ('health', '/api/health', lambda x:x.get('ok') and x.get('version')=='4.0.0'),
        ('18 starter tickers', '/api/portfolio', lambda x:x.get('count')==18),
        ('real Infosys evidence case', '/api/case/INFY', lambda x:x.get('ticker')=='INFY' and len(x.get('quarters',[]))==4 and len(x.get('angles',[]))==8),
        ('eight source-backed lenses', '/api/research/angles?ticker=INFY&angle=all', lambda x:len(x.get('angles',[]))==8),
        ('transparent missing documents', '/api/research/angles?ticker=DIXON&angle=cash', lambda x:x.get('status') in ('no_documents','primary_pdf_evidence')),
    ]
    failures=0
    for name,path,condition in checks:
        try:
            result=get(base,path)
            okay=bool(condition(result))
            print(('PASS' if okay else 'FAIL'),name)
            failures+=not okay
        except Exception as exc:
            failures+=1;print('FAIL',name,str(exc))
    try:
        live=get(base,'/api/prices?mode=live&symbols=INFY')
        rows=live.get('items',[])
        print('EXTERNAL EOD CHECK:',len(rows),'verified records; warning:',live.get('warning'))
    except (URLError,Exception) as exc:
        print('EXTERNAL EOD WARNING: public provider unavailable:',exc)
    print('Required checks failed:',failures)
    return 0 if failures==0 else 1

if __name__=='__main__':
    raise SystemExit(main())
