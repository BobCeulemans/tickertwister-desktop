"""FinAnalysis is the migrated original Tickertwister analysis class.
Copyright ©2022 Bob Ceulemans, MD. Apache-2.0.
"""
from functools import wraps
from html.parser import HTMLParser
import math
import re
import pandas as pd
from analysis_rules import OriginalAnalysisRules, Score, Dictionary
from market_data import MarketData, DataUnavailable, number

ALIASES = {
 'Net Income': ('NetIncome',), 'Total Revenue': ('TotalRevenue',),
 'Gross Profit': ('GrossProfit',), 'Cost Of Revenue': ('CostOfRevenue',),
 'Income Before Tax': ('PretaxIncome',), 'Income Tax Expense': ('TaxProvision',),
 'Interest Expense': ('InterestExpense', 'InterestExpenseNonOperating'), 'Operating Income': ('OperatingIncome',),
 'Research Development': ('ResearchAndDevelopment',),
 'Selling General Administrative': ('SellingGeneralAndAdministration',),
 'Total Operating Expenses': ('TotalExpenses',),
 'Net Income Applicable To Common Shares': ('NetIncomeCommonStockholders',),
 'Total Stockholder Equity': ('StockholdersEquity',), 'Total Assets': ('TotalAssets',),
 'Net Tangible Assets': ('NetTangibleAssets',), 'Inventory': ('Inventory',),
 'Net Receivables': ('Receivables', 'AccountsReceivable'), 'Accounts Payable': ('AccountsPayable',),
 'Retained Earnings': ('RetainedEarnings',), 'Cash': ('CashAndCashEquivalents',),
 'Short Term Investments': ('OtherShortTermInvestments',),
 'Total Current Assets': ('CurrentAssets',), 'Total Current Liabilities': ('CurrentLiabilities',),
 # Historical D/E now consistently uses total debt, matching Yahoo's current D/E.
 'Long Term Debt': ('TotalDebt',), 'Total Liab': ('TotalLiabilitiesNetMinorityInterest',),
 'Total Cash From Operating Activities': ('OperatingCashFlow',),
 'Capital Expenditures': ('CapitalExpenditure',),
 'Depreciation': ('DepreciationAndAmortization', 'DepreciationAmortizationDepletion'),
 'Net Borrowings': ('NetIssuancePaymentsOfDebt',),
 'Repurchase Of Stock': ('RepurchaseOfCapitalStock',),
 'Dividends Paid': ('CashDividendsPaid', 'CommonStockDividendPaid'),
}

class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_data(self, text): self.parts.append(text)
    def handle_starttag(self, tag, attrs):
        if tag in ('br', 'li', 'p', 'tr'): self.parts.append('\n')

def plain(value):
    parser = PlainText()
    parser.feed(str(value))
    return ''.join(parser.parts).strip()


def adapt(frame, dates):
    result = frame.copy()
    for old, names in ALIASES.items():
        for name in names:
            if name in frame.index:
                row = frame.loc[name]
                result.loc[old] = row if old not in result.index else result.loc[old].combine_first(row)
    # Legacy rules expect cash outflows and interest expense with negative signs.
    for key in ('Capital Expenditures', 'Interest Expense', 'Repurchase Of Stock', 'Dividends Paid'):
        if key in result.index: result.loc[key] = -result.loc[key].abs()
    return result.reindex(columns=dates)


def checked(method):
    @wraps(method)
    def run(self):
        name = method.__name__
        if name in self._cache: return self._cache[name]
        nw, np = len(self.weights_list), len(self.points_list)
        before = dict(self.fundamentals)
        self._missing = False
        original_currency = self.data.get('currency')
        if name.endswith('History') or name.startswith('freeCashFlow'):
            self.data['currency'] = self.data.get('financialCurrency') or 'onbekend'
        try:
            if name == 'freeCashFlowToFirm':
                for n in range(len(self.dates)):
                    pretax = self._cell(self.pal_t, 'Income Before Tax', n)
                    tax = self._cell(self.pal_t, 'Income Tax Expense', n)
                    if pretax <= 0 or not 0 <= tax / pretax <= 1:
                        raise ValueError('Invalid effective tax rate')
            value = method(self)
        except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError, OverflowError):
            value = None
            self._missing = True
        finally:
            self.data['currency'] = original_currency
        text = plain(value) if value is not None else ''
        unavailable = self._missing or not text or 'No data' in text or 'not calculated' in text or 'NaN' in text
        if unavailable:
            del self.weights_list[nw:]
            del self.points_list[np:]
            self.fundamentals = before
            value = 'Niet beschikbaar: onvoldoende gegevens of ongeldige deler.'
        self.status[name] = not unavailable
        self.contributions[name] = dict(points=sum(self.points_list[np:]), weight=sum(self.weights_list[nw:]))
        self._cache[name] = value
        return value
    return run


class FinAnalysis(OriginalAnalysisRules):
    def __init__(self, ticker, benchMark=None, FCFE=None, multiple=15, DR=.12, CAGR=None, userId=None, *, provider=None):
        self.source = ticker if isinstance(ticker, MarketData) else MarketData(ticker, provider)
        self.ticker, self.stock = self.source.ticker, self.source.stock
        self.data = dict(self.source.info)
        for key in ('returnOnEquity', 'returnOnAssets'): self.data.setdefault(key, None)
        self.data.setdefault('currency', self.data.get('financialCurrency', 'onbekend'))
        self.benchMark, self.FCFE, self.multiple_PFCF = benchMark, FCFE, multiple
        self.discount_rate, self.growth_FCF, self.userId = DR, CAGR, userId
        self.weights_list, self.points_list, self.fundamentals = [], [], {}
        self._cache, self.status, self.contributions = {}, {}, {}
        self._missing = False
        dates = sorted(set(self.source.income.columns) | set(self.source.balance.columns) | set(self.source.cashflow.columns), reverse=True)
        # Ignore Yahoo's placeholder columns containing no values in any statement.
        dates = [d for d in dates if any(d in f.columns and f[d].notna().any() for f in (self.source.income,self.source.balance,self.source.cashflow))][:4]
        self.dates = dates
        labels = [str(d.date()) for d in dates] + ['ontbreekt'] * 4
        self.y0, self.y1, self.y2, self.y3 = labels[:4]
        self.ttm = 'Yahoo actueel/TTM'
        self.pal, self.bs, self.cfs = (adapt(f, dates) for f in (self.source.income, self.source.balance, self.source.cashflow))
        self.pal_t, self.bs_t, self.cfs_t = self.pal.T, self.bs.T, self.cfs.T
        self.revenue_and_earnings = pd.DataFrame({'Earnings': self.pal.loc['Net Income'].iloc[::-1]}) if 'Net Income' in self.pal.index else pd.DataFrame()
        for key in ('0q', 'n1q', '0y', 'n1y', 'p5y', 'n5y'): setattr(self, 'growthRate_'+key, None)

    def _cell(self, frame, key, index):
        try:
            value = number(frame[key].iloc[index])
            if value is None: raise ValueError('Missing value')
            return value
        except (KeyError, IndexError, ValueError):
            self._missing = True
            raise ValueError(f'Ontbrekende jaarwaarde: {key}')

    def earningsPerShareHistory(self):
        # Use the fiscal-date-aligned frame, just like the other 38 criteria.
        values = [self._cell(self.pal_t, 'DilutedEPS', n) for n in range(len(self.dates))]
        if len(values) < 2: raise ValueError('Need history')
        self.fundamentals['earningsPerShareHistory'] = [self.y3,self.y2,self.y1,self.y0][-len(values):], values[::-1]
        self.weights_list.append(Score.w_EPS)
        increasing = all(a > b for a,b in zip(values,values[1:]))
        self.points_list.append(Score.w_EPS * (1 if increasing else .5 if values[0] > values[-1] else 0))
        return 'EPS: ' + ('consistent stijgend' if increasing else 'niet consistent stijgend') + ' (gerapporteerde diluted EPS per boekjaar).'

    def dividendsHistory(self):
        """Dividendbetaling en trend per aandeel over afgesloten kalenderjaren; Div/CFO per boekjaar."""
        paid = [-self._cell(self.cfs_t, 'Dividends Paid', n) for n in range(len(self.dates))]
        cfo = [self._cell(self.cfs_t, 'Total Cash From Operating Activities', n) for n in range(len(self.dates))]
        if not paid or any(v <= 0 for v in cfo): raise ValueError('Missing dividend/CFO data')
        labels = [str(d.date()) for d in self.dates][::-1]
        self.fundamentals['dividendsHistory'] = labels, [v/1e6 for v in paid[::-1]]
        self.fundamentals['dividendsToCFOHistory'] = labels, [100*a/b for a,b in zip(paid[::-1],cfo[::-1])]
        self.weights_list.append(Score.w_dividends)
        if all(v == 0 for v in paid):
            self.points_list.append(0)
            return 'Geen dividendbetalingen in de beschikbare boekjaren.'
        self.points_list.append(Score.w_dividends * (1 if all(v > 0 for v in paid) else .5))
        # Missing price-history data must not imply a dividend cut.
        try:
            from datetime import date
            dividends = self.stock.get_dividends()
            yearly = dividends.resample('YE').sum()
            yearly = yearly[yearly.index.year < date.today().year].tail(4)
            vals = [number(v) for v in yearly]
            if len(vals) < 4 or any(v is None for v in vals): raise ValueError('Incomplete dividend history')
        except Exception:
            return 'Dividend betaald; trend per aandeel ontbreekt (geen trendpunten).'
        self.fundamentals['dividendsPerShareHistory'] = [str(d.year) for d in yearly.index], vals
        if all(v > 0 for v in vals):
            up = all(a < b for a,b in zip(vals, vals[1:]))
            down = all(a > b for a,b in zip(vals, vals[1:]))
            weight = Score.w_dividends_decreasing if down else Score.w_dividends_increasing
            factor = 1 if up else .5 if vals[-1] > vals[0] else 0
            self.weights_list.append(weight)
            self.points_list.append(weight*factor)
        return 'Dividendbetaling beoordeeld; de dividendtrend gebruikt uitsluitend afgesloten kalenderjaren.'

    def _cash_growth(self, kind):
        """Pure historical growth calculation, without changing score contributions."""
        if len(self.dates) < 2: raise ValueError('Insufficient dates')
        values=[]
        for n in (0,len(self.dates)-1):
            value=self._cell(self.cfs_t,'Total Cash From Operating Activities',n)+self._cell(self.cfs_t,'Capital Expenditures',n)
            if kind == 'FCFE': value += self._cell(self.cfs_t,'Net Borrowings',n)
            if kind == 'FCFF':
                pretax=self._cell(self.pal_t,'Income Before Tax',n)
                if pretax <= 0: raise ValueError('Invalid pretax income')
                tax=self._cell(self.pal_t,'Income Tax Expense',n)/pretax
                if not 0 <= tax <= 1: raise ValueError('Invalid tax rate')
                value += abs(self._cell(self.pal_t,'Interest Expense',n))*(1-tax)
            values.append(value)
        if min(values) <= 0: raise ValueError('CAGR requires positive endpoints')
        years=(self.dates[0]-self.dates[-1]).days/365.25
        if years <= 0: raise ValueError('Invalid fiscal dates')
        growth=(values[0]/values[1])**(1/years)-1
        if not math.isfinite(growth): raise ValueError('Non-finite growth')
        return growth, years

    def _cash_cagr(self, kind):
        fraction, years = self._cash_growth(kind)
        growth = fraction * 100
        key={'FCF':'freeCashFlowCAGR','FCFE':'freeCashFlowToEquityCAGR','FCFF':'freeCashFlowToFirmCAGR'}[kind]
        self.fundamentals[key]=growth
        weight=getattr(Score,'w_'+kind+'_growth_2000bp')
        self.weights_list.append(weight)
        self.points_list.append(weight*(1 if growth >= 20 else .5 if growth > 0 else 0))
        return f'{kind} CAGR over {years:.2f} jaar: {growth:.2f}% (criterium: ≥20%).'

    def freeCashFlowCAGR(self): return self._cash_cagr('FCF')
    def freeCashFlowToFirmCAGR(self): return self._cash_cagr('FCFF')
    def freeCashFlowToEquityCAGR(self): return self._cash_cagr('FCFE')

    def valuation(self):
        try:
            fcfe = self.FCFE * 1e6 if self.FCFE is not None else self._cell(self.cfs_t,'Total Cash From Operating Activities',0) + self._cell(self.cfs_t,'Capital Expenditures',0) + self._cell(self.cfs_t,'Net Borrowings',0)
            shares, price = number(self.data.get('sharesOutstanding')), number(self.data.get('currentPrice'))
            currency = self.data.get('financialCurrency')
            if currency is None or currency != self.data.get('currency'):
                return {'error': 'Waardering overgeslagen: jaarrekening- en koersvaluta verschillen of zijn onbekend.'}
            if self.growth_FCF is not None:
                growth, growth_source = self.growth_FCF, 'manual'
            else:
                try:
                    growth, _ = self._cash_growth('FCFE')
                    growth_source = 'historical-fcfe-cagr'
                except (ValueError, TypeError, IndexError, KeyError, OverflowError):
                    growth, growth_source = 0, 'unavailable-zero-assumption'
            rate, multiple = self.discount_rate, self.multiple_PFCF
            if not all(math.isfinite(v) for v in (fcfe, growth, rate, multiple)) or fcfe <= 0 or shares is None or shares <= 0 or not (-1 < growth and 0 <= rate <= 1 and 0 < multiple <= 100):
                raise ValueError('Invalid valuation inputs')
            flows = [fcfe*(1+growth)**n/(1+rate)**n for n in range(1,11)]
            per_share = (sum(flows)+flows[-1]*multiple)/shares
            if not math.isfinite(per_share) or per_share <= 0:
                raise ValueError('Non-finite valuation')
            return dict(fcfe=fcfe, growth=growth, growthSource=growth_source, rate=rate, multiple=multiple, per_share=per_share,
                price=price, currency=currency, margin=100*(1-price/per_share) if price is not None else None)
        except (ValueError, TypeError, IndexError, KeyError, OverflowError):
            return {'error': 'Geen waardering: positieve FCFE, aandelenaantal en volledige kasstroomgegevens vereist.'}

    def performance(self):
        if not self.benchMark:
            return None
        try:
            import yfinance as yf
            series = {}
            for symbol, stock in [(self.ticker, self.stock), (self.benchMark, yf.Ticker(self.benchMark))]:
                close = stock.history(period='1y', auto_adjust=True)['Close']
                close.index = pd.to_datetime(close.index.date)
                series[symbol] = close
            prices = pd.concat(series, axis=1).dropna()
            if len(prices) < 2 or (prices.iloc[0] <= 0).any():
                raise ValueError('Insufficient common trading dates')
            return dict(start=str(prices.index[0].date()), end=str(prices.index[-1].date()),
                items=[dict(symbol=symbol, return_pct=float((prices[symbol].iloc[-1]/prices[symbol].iloc[0]-1)*100)) for symbol in prices])
        except Exception:
            return {'error': 'Koersvergelijking niet beschikbaar; de fundamentele analyse blijft beschikbaar.'}

    def score(self):
        self.report()
        return self.fundamentals['score'][2]

    def rank(self):
        value = self.score()
        return value / 100 if value is not None else None

    def intrinsicValue(self):
        return self.valuation()

    def conclusion(self):
        report = self.report()
        return dict(score=report["score"], available=report["available"], total=report["total"], valuation=report["valuation"])

    def report(self):
        if hasattr(self, "_report"): return self._report
        sections = []
        for name in ANALYSIS_METHODS:
            value = getattr(self, name)()
            sections.append(dict(name=name, label=plain(getattr(type(self), name).__doc__ or name),
                text=plain(value), available=self.status[name], **self.contributions[name]))
        weight, points = sum(self.weights_list), sum(self.points_list)
        score = 100*points/weight if weight else None
        self.fundamentals['score'] = [points, weight, score]
        histories=[]
        for name, value in self.fundamentals.items():
            if isinstance(value, (list,tuple)) and len(value)==2 and isinstance(value[0],list) and isinstance(value[1],list) and value[0]:
                histories.append(dict(name=name, pairs=list(zip(value[0],value[1]))))
        tables=[]
        for title, frame in [('Resultatenrekening',self.source.income),('Balans',self.source.balance),('Kasstromen',self.source.cashflow)]:
            tables.append(dict(title=title, dates=[str(d.date()) for d in frame.columns], rows=[(str(k),[number(v) for v in row]) for k,row in frame.iterrows()]))
        self._report = dict(symbol=self.ticker,name=self.data.get('longName',self.ticker),summary=self.data.get('longBusinessSummary',''),
            currency=self.data.get('financialCurrency','onbekend'),score=score,points=points,weight=weight,
            available=sum(s['available'] for s in sections),total=len(sections),sections=sections,histories=histories,
            valuation=self.valuation(),performance=self.performance(),tables=tables,
            snapshot=[dict(key=key, label=value[1], value=self.data[key]) for key,value in vars(Dictionary).items() if isinstance(value,tuple) and key in self.data and key not in ('longBusinessSummary','longName') and isinstance(self.data[key],(str,int,float))],warnings=self.source.warnings,fetched_at=self.source.fetched_at)
        return self._report

# All original scoring/history methods, in original source order; each evaluated once.
ANALYSIS_METHODS = [name for name in OriginalAnalysisRules.__dict__ if name.endswith('History') or name in (
    'priceToBookValue','priceToEarningsTTM','priceToEarningsGrowthTTM','evToEbitda',
    'freeCashFlow','freeCashFlowCAGR','freeCashFlowToFirm','freeCashFlowToFirmCAGR','freeCashFlowToEquity','freeCashFlowToEquityCAGR')]
for _name in ANALYSIS_METHODS:
    setattr(FinAnalysis, _name, checked(getattr(FinAnalysis, _name)))

# Backwards-compatible class name and positional constructor arguments.
Tickertwister = FinAnalysis
