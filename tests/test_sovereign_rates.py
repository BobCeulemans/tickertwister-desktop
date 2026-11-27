import tempfile
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))
from sovereign_rates import foreign_rate, major_currency
from period_data import wacc_accounts


class TenYearInputs(unittest.TestCase):
    now = datetime(2026,11,27,9,tzinfo=timezone.utc)

    def test_eur_selects_german_ten_year_and_ignores_missing_and_future_quotes(self):
        data = ('BBK_SEIS_ISIN;BBK_STD_CURRENCY;TIME_PERIOD;OBS_VALUE\n'
                '000000WT1010;EUR;2026-11-26;3.25\n000000WT0202;EUR;2026-11-27;9\n'
                '000000WT1010;EUR;2026-11-27;.\n000000WT1010;EUR;2026-11-28;8')
        with tempfile.TemporaryDirectory() as cache:
            result=foreign_rate('EUR',self.now,cache,lambda url:data)
            self.assertEqual((result['date'],result['yield'],result['sourceID']),('2026-11-26',3.25,'bund'))
            self.assertEqual(foreign_rate('EUR',self.now,cache,lambda url:self.fail('cache miss')),result)
            self.assertIsNone(foreign_rate('GBP',self.now,cache,lambda url:''))

    def test_swiss_spot_and_british_gilt_have_their_own_currency_and_units(self):
        snb = ('<span>SARON</span><span>0.05%</span>\n'
               '<span class="heading">Yield on Swiss Confederation bonds</span><span>0.575%</span>'
               '<span class="dt">26.11.2026 (Spot interest rate for 10-year maturities)</span>')
        ch=foreign_rate('CHF',self.now,fetch=lambda url:snb)
        gbp=foreign_rate('GBP',self.now,fetch=lambda url:'DATE,IUDMNPY\n25 Nov 2026,5.1234')
        self.assertEqual((ch['yield'],ch['currency'],ch['date']),(0.575,'CHF','2026-11-26'))
        self.assertEqual((gbp['yield'],gbp['sourceID'],major_currency('GBp')),(5.1234,'gilt','GBP'))

    def test_japanese_and_canadian_ten_year_observations_select_the_requested_maturity(self):
        japan = ('Interest Rate (November 2026),,,(Unit : %)\nDate,1Y,10Y,20Y\n'
                 '2026/11/26,1.606,2.704,3.615\n2026/11/27,,N/A,3.7\nSource notes,,,')
        jpy=foreign_rate('JPY',self.now,fetch=lambda url:japan)
        self.assertEqual((jpy['sourceID'],jpy['date'],jpy['yield']),('jgb','2026-11-26',2.704))
        canada='{"observations":[{"d":"2026-11-26","BD.CDN.10YR.DQ.YLD":{"v":"3.8"}},{"d":"2026-11-27","x":{"v":"5"}}]}'
        cad=foreign_rate('CAD',self.now,fetch=lambda url:canada)
        self.assertEqual((cad['sourceID'],cad['date'],cad['yield']),('boc','2026-11-26',3.8))

    def test_wacc_trailing_year_uses_actual_fiscal_quarters_and_latest_balance(self):
        dates=['2025-10-31','2026-01-31','2026-04-30','2026-07-31','2026-10-31']
        rows=[dict(end=d,interest=i,tax=20,pretax=100,debt=50+i) for i,d in enumerate(dates,1)]
        annual=[dict(end=dates[1],debt=25,interest=99,tax=12,pretax=30)]
        result=wacc_accounts(annual,rows,dates,dates)
        self.assertEqual((result['interest'],result['tax'],result['debt'],result['flowBasis']),(14,80,55,'TTM'))
        gap=wacc_accounts(annual,rows,dates,[d for d in dates if d!=dates[2]])
        self.assertEqual((gap['interest'],gap['flowDate'],gap['balanceDate']),(None,None,dates[-1]))
        matching_end=wacc_accounts(annual,rows[:2],dates[:2],dates[:2])
        self.assertEqual((matching_end['interest'],matching_end['flowBasis']),(99,'FY=TTM'))
