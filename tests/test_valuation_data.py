import json, sys, tempfile, unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))
from valuation_data import valuation_inputs, treasury_yield, yahoo_ten_year_quote

class ValuationDataTests(unittest.TestCase):
    def test_latest_balance_and_no_lease_double_count(self):
        r={'years':[{'end':'2025-12-31','debt':300,'cash':50,'interest':10,'tax':20,'pretax':100}], 'quarters':[{'end':'2026-09-30','debt':400,'cash':80,'leaseDebt':30}]}
        v=valuation_inputs(r)
        self.assertEqual(v['netDebt'],320)
        self.assertEqual(v['balanceDate'],'2026-09-30')
        self.assertEqual(v['grossDebt'],400)
    def test_missing_debt_or_cash_is_not_assumed_zero(self):
        v=valuation_inputs({'years':[{'end':'2025-12-31','cash':10,'interest':5,'pretax':-100,'tax':2}]})
        self.assertIsNone(v['netDebt'])
        v=valuation_inputs({'years':[{'end':'2025-12-31','debt':0}]})
        self.assertIsNone(v['netDebt'])
    def test_incomplete_later_quarter_uses_one_complete_dated_balance(self):
        v=valuation_inputs({'years':[{'end':'2025-12-31','debt':200,'cash':30}],
                            'quarters':[{'end':'2026-06-30','debt':250}]})
        self.assertEqual((v['balanceDate'],v['netDebt']), ('2025-12-31',170))
    def test_net_cash_and_combined_debt_components(self):
        v=valuation_inputs({'years':[{'end':'2025-12-31','currentDebtAndLeases':10,'longDebtAndLeases':20,'cash':50}]})
        self.assertEqual(v['netDebt'],-20)

class TreasuryTests(unittest.TestCase):
    friday = datetime(2026, 11, 20, 22, tzinfo=timezone.utc)
    saturday = friday + timedelta(days=1)
    fred = 'observation_date,DGS10\n2026-11-18,5.07\n2026-11-19,5.04\n2026-11-20,.\n'
    treasury = ('Date,"7 Yr","10 Yr","20 Yr"\n'
                '11/20/2026,4.80,4.92,5.34\n11/19/2026,4.94,5.04,5.43\n')

    @classmethod
    def feeds(cls, treasury=None, fred=None):
        def fetch(url):
            value = treasury if 'home.treasury.gov' in url else fred
            if value is None:
                raise OSError('offline')
            return value
        return fetch

    def test_weekend_uses_latest_valid_ten_year_observation_across_sources(self):
        treasury = self.treasury + '11/22/2026,1,9,1\n11/21/2026,1,N/A,1\n'
        with tempfile.TemporaryDirectory() as folder:
            latest = treasury_yield(self.feeds(treasury, self.fred), folder, self.saturday)
            self.assertEqual((latest['date'], latest['yield'], latest['sourceID']), ('2026-11-20', 4.92, 'treasury'))
            self.assertTrue(latest['url'].endswith('field_tdr_date_value_month=202611'))
            def cache_hit(url):
                raise AssertionError('A recent checked cache should be reused')
            self.assertEqual(treasury_yield(cache_hit, folder, self.saturday + timedelta(minutes=10)), latest)

    def test_newer_fred_observation_wins_and_treasury_has_priority_on_same_date(self):
        fred = self.fred + '2026-11-20,4.91\n'
        with tempfile.TemporaryDirectory() as folder:
            latest = treasury_yield(self.feeds(self.treasury, fred), folder, self.friday)
            self.assertEqual(latest['yield'], 4.92)
            fresher = fred + '2026-11-23,4.98\n'
            latest = treasury_yield(self.feeds(self.treasury, fresher), folder, self.friday + timedelta(days=3))
            self.assertEqual((latest['yield'], latest['sourceID']), (4.98, 'fred'))
            self.assertEqual(latest['url'], 'https://fred.stlouisfed.org/series/DGS10')

    def test_cache_refreshes_intraday_and_offline_retains_the_newer_observation(self):
        with tempfile.TemporaryDirectory() as folder:
            initial = treasury_yield(self.feeds(fred=self.fred), folder, self.friday)
            self.assertEqual(initial['date'], '2026-11-19')
            later = self.friday + timedelta(minutes=16)
            release = treasury_yield(self.feeds(self.treasury, self.fred), folder, later)
            self.assertEqual((release['date'], release['yield']), ('2026-11-20', 4.92))
            corrected = self.treasury.replace('4.92', '4.93')
            revision = treasury_yield(self.feeds(corrected), folder, later + timedelta(minutes=16))
            self.assertEqual(revision['yield'], 4.93)
            stale_source = treasury_yield(self.feeds(fred=self.fred), folder, self.saturday)
            self.assertEqual(stale_source['date'], revision['date'])
            self.assertEqual(stale_source['retrievedAt'], revision['retrievedAt'])
            offline = treasury_yield(self.feeds(), folder, self.saturday + timedelta(days=9))
            self.assertEqual(offline, stale_source)

    def test_zero_or_negative_yield_is_a_real_observation_for_the_low_rate_policy(self):
        for source_rate in ('0', '-0.1'):
            with tempfile.TemporaryDirectory() as folder:
                fred = self.fred + f'2026-11-20,{source_rate}\n'
                result = treasury_yield(self.feeds(fred=fred), folder, self.saturday)
                self.assertEqual((result['date'], result['yield']), ('2026-11-20', float(source_rate)))

    def test_old_fred_cache_is_rechecked_and_source_links_are_rebuilt(self):
        with tempfile.TemporaryDirectory() as folder:
            cache = Path(folder) / 'treasury-dgs10.json'
            cache.write_text(json.dumps({'yield':5.04, 'date':'2026-11-19',
                'source':'FRED / Federal Reserve DGS10','url':'https://example.invalid',
                'retrievedAt': self.saturday.isoformat()}))
            result = treasury_yield(self.feeds(self.treasury), folder, self.saturday)
            self.assertEqual((result['yield'], result['sourceID']), (4.92,'treasury'))
            self.assertTrue(result['url'].startswith('https://home.treasury.gov/'))
            cache.write_text('{"date":"invalid"}')
            self.assertIsNone(treasury_yield(self.feeds(), folder, self.saturday))

    def test_year_boundary_can_read_previous_year_official_series(self):
        def fetch(url):
            if '/2025/all?' in url:
                return 'Date,10 Yr\n12/31/2025,4.25\n'
            if '/2026/all?' in url:
                return 'Date,10 Yr\n'
            raise OSError('offline')
        with tempfile.TemporaryDirectory() as folder:
            now = datetime(2026, 1, 1, 16, tzinfo=timezone.utc)
            result = treasury_yield(fetch, folder, now)
            self.assertEqual((result['date'], result['yield']), ('2025-12-31',4.25))

class YahooBenchmarkTests(unittest.TestCase):
    def test_tnx_keeps_percentage_points_and_uses_a_short_batch_cache(self):
        import pandas as pd
        from unittest.mock import patch
        day = datetime(2026, 11, 20, 22, tzinfo=timezone.utc)
        frame = pd.DataFrame({'Close': [4.88, 4.92]}, index=pd.to_datetime(['2026-11-19', '2026-11-20']))
        with tempfile.TemporaryDirectory() as temp, patch('yfinance.Ticker') as ticker:
            ticker.return_value.history.return_value = frame
            self.assertEqual(yahoo_ten_year_quote(temp, day), {'date': '2026-11-20', 'yield': 4.92})
            self.assertEqual(yahoo_ten_year_quote(temp, day), {'date': '2026-11-20', 'yield': 4.92})
            ticker.assert_called_once_with('^TNX')


if __name__=='__main__':unittest.main()
