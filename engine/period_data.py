"""Additional comparison periods; original FinAnalysis score remains unchanged."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date,timedelta
from market_data import number
import pandas as pd

def matrix(frame):
    if not isinstance(frame,pd.DataFrame) or frame.empty:return {}
    frame=frame.loc[~frame.index.duplicated(keep=False)]
    return {str(key):{str(d.date()):number(frame.loc[key,d]) for d in frame.columns} for key in frame.index}

def quarter_key(end):
    d=date.fromisoformat(end);ends=[date(y,m,1)+timedelta(days=32) for y in range(d.year-1,d.year+2) for m in (3,6,9,12)]
    ends=[e.replace(day=1)-timedelta(days=1) for e in ends]
    nearest=min(ends,key=lambda e:abs((e-d).days))
    return f'{nearest.year}-Q{(nearest.month+2)//3}' if abs((nearest-d).days)<=7 else None

def supplement(analysis,result,build_rows):
    result['website']=str(analysis.data.get('website') or '')
    result['sector']=str(analysis.data.get('sector') or '');result['industry']=str(analysis.data.get('industry') or '')
    result['periodWarnings']=[];result['quarters']=[]
    def fetch(method):
        try:return getattr(analysis.stock,method)(freq='quarterly',pretty=False)
        except Exception:return pd.DataFrame()
    with ThreadPoolExecutor(max_workers=3) as pool:frames=list(pool.map(fetch,['get_income_stmt','get_balance_sheet','get_cashflow']))
    matrices=[matrix(f) for f in frames]
    # Require a real income-statement period, never fabricate a quarter from annual data.
    dates=sorted({d for row in matrices[0].values() for d,v in row.items() if v is not None})[-8:]
    rows=build_rows(matrices,dates)
    for row in rows:
        key=quarter_key(row['end'])
        if not key or row['revenue'] is None:continue
        row['periodKey']=key;row['periodType']='quarter'
        result['quarters'].append(row)
    if not result['quarters']:result['periodWarnings'].append('No quarterly income-statement data available; refresh later.')
