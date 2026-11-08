"""Regression contract for Yahoo statement names, dates and accounting signs."""
import json
from pathlib import Path
import pandas as pd
import pytest
from yfinance.const import fundamentals_keys
from engine import MAP, build_rows, convert
from tickertwister import ALIASES, FinAnalysis, adapt
from period_data import matrix, supplement
from market_data import MarketData
from test_engine import Provider, DATES

CONTRACT=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/statement-contract.json').read_text())
OUTFLOWS={'capex','dividends','buybacks','interest'}
LEGACY_OUTFLOWS={'Capital Expenditures','Interest Expense','Repurchase Of Stock','Dividends Paid'}
STATEMENTS=('financials','balance-sheet','cash-flow')


def synthetic_frames():
    # Different values for every statement/row/date, including same-name decoys
    # in the wrong statement. No equal dummy values can hide a crossed binding.
    names=sorted({n for _,*ns in CONTRACT['appFields'].values() for n in ns} |
                 {n for ns in CONTRACT['legacyAliases'].values() for n in ns})
    return [pd.DataFrame([[(-1 if name in ('CapitalExpenditure','CashDividendsPaid','RepurchaseOfCapitalStock') else 1)*((s+1)*1000000+(r+1)*1000+d*17)
                           for d in range(4)] for r,name in enumerate(names)],index=names,columns=DATES)
            for s in range(3)]


def test_frozen_v102_field_names_and_statement_bindings():
    assert {k:list(v) for k,v in MAP.items()}==CONTRACT['appFields']
    assert {k:list(v) for k,v in ALIASES.items()}==CONTRACT['legacyAliases']
    for key,(s,*names) in CONTRACT['appFields'].items():
        # Legacy optional field absent from both versions: keep missing; do not
        # replace with CurrentDebt (which is not the same accounting concept).
        if key=='longDebtCurrent':
            assert names==['LongTermDebtCurrent']
            continue
        assert any(n in fundamentals_keys[STATEMENTS[s]] for n in names),key


@pytest.mark.parametrize('quarterly',[False,True])
@pytest.mark.parametrize('alternative_names',[False,True])
def test_every_table_item_is_bound_by_name_and_date_not_position(quarterly,alternative_names):
    frames=synthetic_frames()
    if alternative_names:
        for _,(s,*names) in CONTRACT['appFields'].items():
            if len(names)>1:frames[s]=frames[s].drop(index=names[0],errors='ignore')
    if quarterly:
        for frame in frames:frame.columns=pd.to_datetime(['2026-09-30','2026-06-30','2026-03-31','2025-12-31'])
    expected=[]
    for date in frames[0].columns:
        row={'end':str(date.date())}
        for key,(s,*names) in CONTRACT['appFields'].items():
            value=next((float(frames[s].loc[n,date]) for n in names if n in frames[s].index),None)
            row[key]=abs(value) if key in OUTFLOWS and value is not None else value
        expected.append(row)
    shuffled=[f.sample(frac=1,random_state=i).sample(frac=1,axis=1,random_state=i+10) for i,f in enumerate(frames)]
    actual=build_rows([matrix(f) for f in shuffled],[row['end'] for row in expected])
    for want,got in zip(expected,actual):
        for key,value in want.items():assert got[key]==value,(key,want['end'])
        assert got['fcfe']==want['cfo']-want['capex']+want['netBorrowings']
        assert got['roe']==want['income']/want['equity']
        assert got['roa']==want['income']/want['assets']
        assert got['debtEquity']==want['debt']/want['equity']


def test_all_legacy_aliases_keep_priority_and_signs():
    frame=synthetic_frames()[0]
    for fallback in (False,True):
        current=frame.copy()
        if fallback:
            current=current.drop(index=[names[0] for names in CONTRACT['legacyAliases'].values() if len(names)>1])
        result=adapt(current.sample(frac=1,random_state=11).iloc[:,::-1],DATES)
        for alias,names in CONTRACT['legacyAliases'].items():
            key=next(n for n in names if n in current.index)
            for date in DATES:
                expected=current.loc[key,date]
                if alias in LEGACY_OUTFLOWS:expected=-abs(expected)
                assert result.loc[alias,date]==expected,(alias,date)


def test_no_substitution_when_net_income_or_net_borrowings_missing():
    frames=synthetic_frames()
    frames[0]=frames[0].drop(index='NetIncome')
    frames[2]=frames[2].drop(index='NetIssuancePaymentsOfDebt')
    rows=build_rows([matrix(f) for f in frames],[str(d.date()) for d in DATES])
    for row in rows:
        assert row['income'] is None and row['netBorrowings'] is None
        assert row['roe'] is None and row['fcfe'] is None
        assert row['revenue'] is not None and row['fcf'] is not None


class Reordered(Provider):
    def frame(self):return super().frame().sample(frac=1,random_state=2).iloc[:,[2,0,3,1]]


def test_all_39_criteria_and_eps_remain_attached_to_their_fiscal_dates():
    baseline=convert(FinAnalysis('TEST',provider=Provider()))
    reordered=convert(FinAnalysis('TEST',provider=Reordered()))
    assert reordered['years']==baseline['years']
    assert reordered['originalHistories']==baseline['originalHistories']
    assert reordered['score']==baseline['score']
    assert reordered['originalValuation']==baseline['originalValuation']


def test_diluted_eps_missing_one_fiscal_period_is_not_shifted():
    class Missing(Provider):
        def get_income_stmt(self,**kw):return self.frame().drop(columns=DATES[1])
    a=FinAnalysis('TEST',provider=Missing())
    criterion=next(c for c in convert(a)['score']['criteria'] if c['key']=='earningsPerShareHistory')
    assert not criterion['available']


def test_annual_ambiguous_rows_and_dates_are_missing_not_arbitrarily_selected():
    class Ambiguous(Provider):
        def get_income_stmt(self,**kw):
            f=self.frame();return pd.concat([f,f.loc[['NetIncome']]*100])
        def get_balance_sheet(self,**kw):
            f=self.frame();return pd.concat([f,f[[DATES[0]]]*100],axis=1)
    data=MarketData('TEST',provider=Ambiguous())
    assert 'NetIncome' not in data.income.index
    assert DATES[0] not in data.balance.columns
    assert len(data.warnings)>=2
    result=convert(FinAnalysis(data))
    assert all(y['income'] is None for y in result['years'])
    assert result['years'][-1]['assets'] is None


def test_quarterly_ambiguous_dates_are_missing_not_annual_substitutes():
    frame=synthetic_frames()[0]
    frame=pd.concat([frame,frame[[DATES[0]]]*100],axis=1)
    result=matrix(frame)
    assert all(str(DATES[0].date()) not in values for values in result.values())
    assert result['NetIncome'][str(DATES[1].date())]==frame.loc['NetIncome',DATES[1]]
