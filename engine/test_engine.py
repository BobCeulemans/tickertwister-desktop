import pandas as pd
from tickertwister import FinAnalysis, ALIASES, ANALYSIS_METHODS
from engine import convert
DATES = pd.to_datetime(['2025-09-30','2024-09-30','2023-09-30','2022-09-30'])
class Provider:
    def get_info(self):
        return dict(longName='<script>alert(1)</script>',currency='USD',financialCurrency='USD',sharesOutstanding=10,currentPrice=20,returnOnEquity=None,returnOnAssets=None,debtToEquity=40,revenueGrowth=.1,priceToBook=.8,trailingPE=15,forwardPE=12,trailingPegRatio=2,pegRatio=1,enterpriseToEbitda=3)
    def frame(self):
        data={names[0]:[100.,100.,100.,100.] for names in ALIASES.values()}
        data.update(NetIncome=[20,18,16,14],TotalRevenue=[100]*4,GrossProfit=[45]*4,CostOfRevenue=[55]*4,
            StockholdersEquity=[100]*4,TotalAssets=[200]*4,CurrentAssets=[60]*4,CurrentLiabilities=[30]*4,
            CashAndCashEquivalents=[40,30,20,10],OtherShortTermInvestments=[0]*4,Receivables=[10]*4,
            TotalDebt=[40,30,20,10],TotalLiabilitiesNetMinorityInterest=[70,60,50,40],
            OperatingCashFlow=[30,28,26,24],CapitalExpenditure=[-10]*4,NetIssuancePaymentsOfDebt=[-5]*4,
            InterestExpense=[2]*4,TaxProvision=[5]*4,PretaxIncome=[25]*4,OperatingIncome=[25]*4,
            DilutedEPS=[2,1.8,1.6,1.4],CashDividendsPaid=[-1]*4,RepurchaseOfCapitalStock=[-1]*4)
        return pd.DataFrame(data,index=DATES).T
    def get_income_stmt(self, **kw): return self.frame()
    def get_balance_sheet(self, **kw): return self.frame()
    def get_cashflow(self, **kw): return self.frame()
    def get_dividends(self):
        return pd.Series([1.,1.2,1.4,1.6,1.8],index=pd.DatetimeIndex(pd.to_datetime(['2022-06-01','2023-06-01','2024-06-01','2025-06-01','2026-06-01']),name='Date'),name='Dividends')

def analysis(**kwargs): return FinAnalysis('TEST',provider=Provider(),**kwargs)


def test_exact_original_score_and_contributions():
    a=analysis();raw=a.report();mapped=convert(a)
    assert len(ANALYSIS_METHODS)==39
    assert mapped['score']['total']==39
    assert mapped['score']['value']==raw['score']
    assert mapped['score']['points']==raw['points']
    assert mapped['score']['weight']==raw['weight']
    for section,criterion in zip(raw['sections'],mapped['score']['criteria']):
        assert section['name']==criterion['key']
        assert section['weight']==criterion['weight']
        assert section['available']==criterion['available']
        if section['available']:assert section['points']==criterion['points']

def test_missing_fields_excluded_and_histories_preserved():
    a=analysis();a.pal_t=a.pal_t.drop(columns='Net Income')
    raw=a.report();mapped=convert(a)
    assert mapped['score']['available']==raw['available']<39
    assert len(mapped['originalHistories'])==len(raw['histories'])

def test_cashflow_signs_and_euro_currency():
    a=analysis();a.data['financialCurrency']='EUR';a.data['currency']='EUR'
    mapped=convert(a);y=mapped['years'][-1]
    assert mapped['currency']=='EUR'
    assert mapped['quote']['currency']=='EUR'
    assert y['capex']==10 and y['fcf']==20 and y['fcfe']==15
    assert mapped['valuationShares']==10


def test_quarter_alignment_with_52_week_years():
    from period_data import quarter_key
    assert quarter_key('2026-09-26') == '2026-Q3'
    assert quarter_key('2027-01-02') == '2026-Q4'
    assert quarter_key('2026-02-28') is None


def test_duplicate_line_items_never_fabricate_financial_values():
    from period_data import matrix
    frame=pd.DataFrame([[1.],[2.]],index=['NetIncome','NetIncome'],columns=pd.to_datetime(['2026-09-30']))
    assert matrix(frame)=={}

def test_fiscal_dps_uses_actual_events_and_not_current_shares():
    from engine import fiscal_dividends
    class History:
        def history(self,**kwargs):
            idx=pd.date_range('2022-09-25','2025-10-01',tz='America/New_York')
            h=pd.DataFrame({'Dividends':0.0},index=idx)
            for date,value in [('2023-09-30',.2),('2023-10-01',.3),('2024-02-01',.4),('2024-09-30',.5),('2024-10-01',.6)]:h.loc[date,'Dividends']=value
            return h
    rows=[{'end':'2023-09-30','dps':None},{'end':'2024-09-30','dps':None},{'end':'2025-09-30','dps':None}]
    fiscal_dividends(History(),rows)
    assert [round(y['dps'],2) for y in rows]==[.2,1.2,.6]
    missing=[{'end':'2021-09-30','dps':None}];fiscal_dividends(History(),missing);assert missing[0]['dps'] is None
    currency=[{'end':'2024-09-30','dps':None}];fiscal_dividends(History(),currency,False);assert currency[0]['dps'] is None

def test_unavailable_dividend_history_is_not_zero():
    from engine import fiscal_dividends
    rows=[{'end':'2025-09-30','dps':None}]
    fiscal_dividends(object(),rows)
    assert rows[0]['dps'] is None


def test_currency_snapshot_and_missing_fx():
    from currency_data import supplement_currency
    from datetime import datetime, timezone
    import pandas as pd
    class Provider:
        def history(self, **kwargs):
            return pd.DataFrame({'Close': [150.]}, index=pd.to_datetime(['2026-11-06'], utc=True))
    report = {'symbol': 'SONY', 'currency': 'JPY', 'quote': {'currency': 'USD'}}
    supplement_currency(report, lambda symbol: Provider(), datetime(2026, 11, 6, tzinfo=timezone.utc))
    assert report['fx']['rate'] == 150
    assert report['fx']['from'] == 'USD' and report['fx']['to'] == 'JPY'
    assert report['quoteBasis']['ordinaryPerQuote'] == 1
    unknown = {'symbol': 'UNKNOWN', 'currency': 'JPY', 'quote': {'currency': 'USD'}}
    supplement_currency(unknown, lambda symbol: Provider(), datetime(2026, 11, 6, tzinfo=timezone.utc))
    assert 'quoteBasis' not in unknown
    stale = {'symbol': 'SONY', 'currency': 'JPY', 'quote': {'currency': 'USD'}}
    supplement_currency(stale, lambda symbol: Provider(), datetime(2026, 12, 6, tzinfo=timezone.utc))
    assert 'fx' not in stale


def test_reported_growth_remains_uncapped_in_valuation_and_report():
    for growth in (.271, -.074, 1.2, 0, None):
        a = analysis(); a.data['revenueGrowth'] = growth
        result = a.valuation()
        assert result['growth'] == (growth if growth is not None else 0)
        assert result['per_share'] > 0
        assert convert(a)['revenueGrowth'] == growth
    a = analysis(); a.data['revenueGrowth'] = .271
    a.data['financialCurrency'] = 'EUR'
    mapped = convert(a)
    assert 'error' in mapped['originalValuation']
    assert mapped['revenueGrowth'] == .271  # Available even when the legacy valuation cannot run.


def test_extreme_growth_does_not_produce_infinite_model_values():
    a = analysis(); a.data['revenueGrowth'] = 1e50
    assert 'error' in a.valuation()
