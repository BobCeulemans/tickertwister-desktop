"""JSON boundary for the unchanged, migrated original FinAnalysis engine."""
import json,sys,os,math,re,contextlib
from pathlib import Path
from datetime import datetime,timezone
from tickertwister import FinAnalysis,ANALYSIS_METHODS
from market_data import number
LABELS=json.loads(Path(__file__).with_name('labels.json').read_text())
NUMERIC_KEYS='revenue income gross cost operating interest assets equity liabilities currentAssets currentLiabilities cash investments receivables inventory payables longDebt currentDebt shortDebt retained cfo capex debtIssued debtRepaid buybacks dividends eps dps shares debt fcf fcfe netBorrowings roe roa grossMargin netMargin currentRatio quickRatio debtEquity liabilitiesEquity interestCoverage fcfMargin cashConversion assetTurnover capexIncome dividendCoverage dio dso dpo ccc'.split()
MAP={'revenue':(0,'TotalRevenue'),'income':(0,'NetIncome'),'gross':(0,'GrossProfit'),'cost':(0,'CostOfRevenue'),'operating':(0,'OperatingIncome'),'interest':(0,'InterestExpense','InterestExpenseNonOperating'),'assets':(1,'TotalAssets'),'equity':(1,'StockholdersEquity'),'liabilities':(1,'TotalLiabilitiesNetMinorityInterest'),'currentAssets':(1,'CurrentAssets'),'currentLiabilities':(1,'CurrentLiabilities'),'cash':(1,'CashAndCashEquivalents'),'investments':(1,'OtherShortTermInvestments'),'receivables':(1,'Receivables','AccountsReceivable'),'inventory':(1,'Inventory'),'payables':(1,'AccountsPayable'),'retained':(1,'RetainedEarnings'),'cfo':(2,'OperatingCashFlow'),'capex':(2,'CapitalExpenditure'),'debt':(1,'TotalDebt'),'dividends':(2,'CashDividendsPaid','CommonStockDividendPaid'),'buybacks':(2,'RepurchaseOfCapitalStock'),'eps':(0,'DilutedEPS'),'shares':(1,'OrdinarySharesNumber','ShareIssued'),'netBorrowings':(2,'NetIssuancePaymentsOfDebt')}
MAP.update({'sga':(0,'SellingGeneralAndAdministration'),'rd':(0,'ResearchAndDevelopment'),'opex':(0,'OperatingExpense'),'pretax':(0,'PretaxIncome'),'tax':(0,'TaxProvision'),'assetSalesGain':(0,'GainOnSaleOfPPE','GainOnSaleOfBusiness'),'otherIncome':(0,'OtherNonOperatingIncomeExpenses'),'da':(2,'DepreciationAndAmortization','DepreciationAmortizationDepletion'),'taxPaid':(2,'IncomeTaxPaidSupplementalData'),'ppe':(1,'NetPPE'),'goodwill':(1,'Goodwill'),'intangibles':(1,'OtherIntangibleAssets'),'longInvestments':(1,'InvestmentsAndAdvances','LongTermEquityInvestment'),'otherLongAssets':(1,'OtherNonCurrentAssets'),'prepaid':(1,'PrepaidAssets'),'otherCurrentAssets':(1,'OtherCurrentAssets'),'accrued':(1,'CurrentAccruedExpenses'),'otherCurrentLiabilities':(1,'OtherCurrentLiabilities'),'longDebt':(1,'LongTermDebt'),'currentDebt':(1,'CurrentDebt'),'longDebtCurrent':(1,'LongTermDebtCurrent'),'deferredTax':(1,'NonCurrentDeferredTaxesLiabilities'),'minorityInterest':(1,'MinorityInterest'),'otherLiabilities':(1,'OtherNonCurrentLiabilities'),'preferredStock':(1,'PreferredStock'),'commonStock':(1,'CommonStock'),'paidInCapital':(1,'AdditionalPaidInCapital'),'treasuryStock':(1,'TreasuryStock'),'cfi':(2,'InvestingCashFlow'),'cff':(2,'FinancingCashFlow'),'stockIssued':(2,'IssuanceOfCapitalStock')})
def divide(a,b):return a/b if a is not None and b is not None and b>0 else None
def minus(a,b):return a-b if a is not None and b is not None else None
def plus(*args):return sum(args) if all(v is not None for v in args) else None

def build_rows(matrices,dates):
    def cell(key,date):
        idx,*names=MAP[key]
        return next((matrices[idx][n][date] for n in names if matrices[idx].get(n,{}).get(date) is not None),None)
    years=[]
    for date in dates:
        y=dict.fromkeys(NUMERIC_KEYS);y.update(end=date)
        for k in MAP:y[k]=cell(k,date)
        for k in ('capex','dividends','buybacks','interest'):
            if y[k] is not None:y[k]=abs(y[k])
        y['fcf']=minus(y['cfo'],y['capex']);y['fcfe']=plus(y['fcf'],y['netBorrowings'])
        for key,a,b in [('roe','income','equity'),('roa','income','assets'),('grossMargin','gross','revenue'),('netMargin','income','revenue'),('currentRatio','currentAssets','currentLiabilities'),('debtEquity','debt','equity'),('liabilitiesEquity','liabilities','equity'),('interestCoverage','operating','interest'),('fcfMargin','fcf','revenue'),('cashConversion','cfo','income'),('assetTurnover','revenue','assets'),('capexIncome','capex','income'),('dividendCoverage','fcf','dividends')]:y[key]=divide(y[a],y[b])
        y['quickRatio']=divide(plus(y['cash'],y['investments'],y['receivables']),y['currentLiabilities'])
        for key,a,b in [('dio','inventory','cost'),('dso','receivables','revenue'),('dpo','payables','cost')]:
            value=divide(y[a],y[b]);y[key]=value*365 if value is not None else None
        y['ccc']=minus(plus(y['dio'],y['dso']),y['dpo']);years.append(y)
    return years

def fiscal_dividends(stock, years, same_currency=True):
    if not same_currency:return
    try:
        import pandas as pd
        history=stock.history(period='max', auto_adjust=False, actions=True)
        if history.empty or 'Dividends' not in history:return
        history=history.copy()
        history.index=pd.to_datetime(history.index).tz_localize(None).normalize()
        for i,y in enumerate(years):
            end=pd.Timestamp(y['end'])
            start=pd.Timestamp(years[i-1]['end']) if i else end-pd.DateOffset(years=1)
            # Allow weekends/holidays at the boundary, but not partial history.
            if history.index.min()>start+pd.Timedelta(days=7) or history.index.max()<end-pd.Timedelta(days=7):continue
            values=history.loc[(history.index>start)&(history.index<=end),'Dividends']
            if values.empty or values.isna().any() or (values<0).any():continue
            y['dps']=float(values.sum())
            y['dpsSource']='Yahoo dividend events by ex-dividend date; fiscal window; split-adjusted share basis'
    except Exception:
        pass # Unavailable dividend history must remain missing, not zero.

def convert(analysis):
    r=analysis.report();dates=sorted(str(d.date()) for d in analysis.dates)
    if not dates:raise ValueError('NO_ANNUAL_DATA')
    matrices=[{k:dict(zip(t['dates'],v)) for k,v in t['rows']} for t in r['tables']]
    years=build_rows(matrices,dates)
    criteria=[]
    for s in r['sections']:
        criteria.append(dict(key=s['name'],label=LABELS['labels'][s['name']],heading=LABELS['headings'][s['name']],weight=s['weight'],points=s['points'] if s['available'] else None,factor=(s['points']/s['weight'] if s['weight'] else 0) if s['available'] else None,available=s['available'],formula=s['label'],threshold=s['text'],value=None))
    histories=[]
    for h in r['histories']:
        name=h['name'];kind='money' if name in LABELS['millions'] else 'ratio' if name in LABELS['ratios'] else 'days' if name in LABELS['days'] else 'perShare' if name in LABELS['perShare'] else 'months' if name=='totalCashToMonthlyOperatingExpensesHistory' else 'percent'
        histories.append(dict(name=name,label=LABELS['labels'].get(name,name),heading=LABELS['headings'].get(name,name),kind=kind,pairs=[[d,v*1e6 if v is not None and kind=='money' else v] for d,v in h['pairs']]))
    info=analysis.data;currency=r['currency'];quote_currency=info.get('currency');price=number(info.get('currentPrice',info.get('regularMarketPrice')))
    quote=None if price is None else dict(price=price,currency=quote_currency,at=datetime.fromtimestamp(info['regularMarketTime'],timezone.utc).isoformat() if isinstance(info.get('regularMarketTime'),(int,float)) else r['fetched_at'],source='Yahoo Finance',marketCap=number(info.get('marketCap')))
    # Sum actual dividend-per-share events in the fiscal window, never infer
    # DPS by dividing cash outflows by today's share count.
    fiscal_dividends(analysis.stock, years, currency == quote_currency)
    trailing=number(info.get('trailingAnnualDividendRate'))
    return dict(schema='yahoo39-v1',source='Yahoo Finance / yfinance',symbol=r['symbol'],name=r['name'],currency=currency,quoteCurrency=quote_currency,years=years,quote=quote,
        fetchedAt=r['fetched_at'],latestEnd=dates[-1],stale=(datetime.now(timezone.utc)-datetime.fromisoformat(dates[-1]).replace(tzinfo=timezone.utc)).days>550,
        score=dict(value=r['score'],points=r['points'],weight=r['weight'],available=r['available'],total=r['total'],coverage=r['available']/r['total'],criteria=criteria),
        originalHistories=histories,originalTables=r['tables'],originalValuation=r['valuation'],summary=r['summary'],warnings=r['warnings'],provenance=[],cik='',
        revenueGrowth=number(info.get('revenueGrowth')),valuationShares=number(info.get('sharesOutstanding')),dividendPerShare=trailing,dividendCurrency=quote_currency,shareBasis='Yahoo sharesOutstanding')

def main():
    symbol=sys.argv[1].strip().upper() if len(sys.argv)==2 else ''
    if not re.fullmatch(r'[A-Z0-9^][A-Z0-9.^=\-]{0,19}',symbol):raise ValueError('INVALID_TICKER')
    import yfinance as yf
    cache=os.environ.get('TICKERTWISTER_CACHE')
    if cache:Path(cache).mkdir(parents=True,exist_ok=True);yf.set_tz_cache_location(cache)
    with contextlib.redirect_stdout(sys.stderr):
        analysis=FinAnalysis(symbol);result=convert(analysis)
        from period_data import supplement
        supplement(analysis,result,build_rows)
        from currency_data import supplement_currency
        supplement_currency(result)
    print(json.dumps(result,allow_nan=False,ensure_ascii=False,default=str))
if __name__=='__main__':
    try:main()
    except Exception as e:
        print(json.dumps({'error':str(e) if str(e) in ('INVALID_TICKER','NO_ANNUAL_DATA') else 'YAHOO_UNAVAILABLE'}));sys.exit(1)
