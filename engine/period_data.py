"""Additional comparison periods; original FinAnalysis score remains unchanged."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date,timedelta
from market_data import number, unambiguous_statement
import pandas as pd

def matrix(frame):
    if not isinstance(frame,pd.DataFrame) or frame.empty:return {}
    frame=unambiguous_statement(frame)
    return {str(key):{str(d.date()):number(frame.loc[key,d]) for d in frame.columns} for key in frame.index}

def quarter_key(end):
    d=date.fromisoformat(end);ends=[date(y,m,1)+timedelta(days=32) for y in range(d.year-1,d.year+2) for m in (3,6,9,12)]
    ends=[e.replace(day=1)-timedelta(days=1) for e in ends]
    nearest=min(ends,key=lambda e:abs((e-d).days))
    return f'{nearest.year}-Q{(nearest.month+2)//3}' if abs((nearest-d).days)<=7 else None

def supplement(analysis,result,build_rows):
    result['country']=str(analysis.data.get('country') or '')
    result['website']=str(analysis.data.get('website') or '')
    result['sector']=str(analysis.data.get('sector') or '');result['industry']=str(analysis.data.get('industry') or '')
    result['periodWarnings']=[];result['quarters']=[]
    def fetch(method):
        try:return getattr(analysis.stock,method)(freq='quarterly',pretty=False)
        except Exception:return pd.DataFrame()
    with ThreadPoolExecutor(max_workers=3) as pool:frames=list(pool.map(fetch,['get_income_stmt','get_balance_sheet','get_cashflow']))
    matrices=[matrix(unambiguous_statement(f,result['periodWarnings'],'Quarterly statement')) for f in frames]
    # WACC follows actual fiscal quarters, also for companies whose year-end is off-calendar.
    income_dates = sorted({d for row in matrices[0].values() for d,v in row.items() if v is not None})
    balance_dates = {d for row in matrices[1].values() for d,v in row.items() if v is not None}
    actual_dates = sorted(set(income_dates) | balance_dates)
    result['waccAccounts'] = wacc_accounts(result['years'], build_rows(matrices,actual_dates), balance_dates, income_dates)
    # Require a real income-statement period, never fabricate a quarter from annual data.
    dates=sorted({d for row in matrices[0].values() for d,v in row.items() if v is not None})[-8:]
    rows=build_rows(matrices,dates)
    for row in rows:
        key=quarter_key(row['end'])
        if not key or row['revenue'] is None:continue
        row['periodKey']=key;row['periodType']='quarter'
        result['quarters'].append(row)
    if not result['quarters']:result['periodWarnings'].append('No quarterly income-statement data available; refresh later.')

def wacc_accounts(annual, quarterly, balance_dates, income_dates):
    """Gross debt at the most recent balance date and flows for its trailing year."""
    annual_by_date = {row['end']: row for row in annual if any(row.get(k) is not None for k in ('assets','equity','debt','cash'))}
    end = max(set(annual_by_date) | set(balance_dates), default=None)
    if end is None:
        return None
    quarter_rows = {row['end']: row for row in quarterly}
    year = annual_by_date.get(end, {})
    balance = quarter_rows.get(end, {})
    def debt(row):
        if row.get('debt') is not None:
            return row['debt']
        a,b = row.get('longDebtAndLeases'),row.get('currentDebtAndLeases')
        return a+b if a is not None and b is not None else None
    gross = debt(balance)
    result = dict(balanceDate=end, debt=debt(year) if gross is None else gross, flowDate=None, flowBasis=None)
    dates = sorted({d for d in income_dates if d <= end})[-4:]
    aligned = len(dates)==4 and dates[-1]==end and all(75 <= (date.fromisoformat(b)-date.fromisoformat(a)).days <= 105 for a,b in zip(dates,dates[1:]))
    if aligned or year:
        # A full fiscal year is precisely a TTM period on its own closing date.
        result.update(flowDate=end,flowBasis='FY=TTM' if year else 'TTM')
    for key in ('interest','tax','pretax'):
        values = [quarter_rows[d].get(key) for d in dates] if aligned else []
        result[key] = year.get(key)
        if result[key] is None and values and all(v is not None for v in values):
            result[key] = sum(values)
    return result
