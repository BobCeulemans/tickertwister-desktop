"""Ten-year government yields in the currency of each nominal valuation."""
import csv
import fcntl
import io
import json
import math
import os
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from valuation_data import cache_is_recent, download_csv, treasury_yield, yahoo_ten_year_quote

BUND = 'https://api.statistiken.bundesbank.de/rest/data/BBSSY/D.REN.EUR.A630.000000WT1010.A'
GILT = 'https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp'
CONFEDERATION = 'https://www.snb.ch/en/srv/current_interest_exchange_rates'
JGB = 'https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv'
CANADA = 'https://www.bankofcanada.ca/valet/observations/BD.CDN.10YR.DQ.YLD/json'
IDS = {'EUR': 'bund', 'GBP': 'gilt', 'CHF': 'snb', 'JPY': 'jgb', 'CAD': 'boc'}
MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()


def major_currency(code):
    return {'GBp': 'GBP', 'GBX': 'GBP', 'ZAc': 'ZAR', 'ILA': 'ILS'}.get(code, code)


def observation(currency, day, value, today):
    try:
        day = date.fromisoformat(day)
        if isinstance(value, bool):
            return None
        value = float(value)
        if day <= today and math.isfinite(value) and -100 < value < 100:
            return dict(currency=currency, sourceID=IDS[currency], date=day.isoformat(), **{'yield': value})
    except (TypeError, ValueError):
        pass
    return None


def foreign_feed(currency, today, fetch):
    since = today - timedelta(days=14)
    if currency == 'EUR':
        content = fetch(f'{BUND}?startPeriod={since}&format=sdmx_csv').lstrip('\ufeff')
        rows = ((r['TIME_PERIOD'], r['OBS_VALUE']) for r in csv.DictReader(io.StringIO(content), delimiter=';')
                if r.get('BBK_SEIS_ISIN') == '000000WT1010' and r.get('BBK_STD_CURRENCY') == 'EUR')
    elif currency == 'GBP':
        def uk(d):
            return f'{d.day:02}/{MONTHS[d.month-1]}/{d.year}'
        url = f'{GILT}?csv.x=yes&Datefrom={uk(since)}&Dateto={uk(today)}&SeriesCodes=IUDMNPY&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N'
        content = fetch(url).lstrip('\ufeff')
        def gilt_rows():
            for row in csv.DictReader(io.StringIO(content)):
                try:
                    day, month, year = row['DATE'].split()
                    yield date(int(year), MONTHS.index(month)+1, int(day)).isoformat(), row['IUDMNPY']
                except (ValueError, KeyError):
                    continue
        rows = gilt_rows()
    elif currency == 'JPY':
        # The Ministry publishes the current month's daily par yields, with a preamble and footnotes.
        lines = fetch(JGB).splitlines()
        start = next((i for i, line in enumerate(lines) if line.startswith('Date,')), len(lines))
        rows = []
        for row in csv.DictReader(lines[start:]):
            try:
                day = datetime.strptime(row['Date'], '%Y/%m/%d').date().isoformat()
                rows.append((day, row['10Y']))
            except (ValueError, KeyError, TypeError):
                continue
    elif currency == 'CAD':
        data = json.loads(fetch(f'{CANADA}?start_date={since}&end_date={today}'))
        rows = [(r.get('d'), r['BD.CDN.10YR.DQ.YLD'].get('v')) for r in data.get('observations',[])
                if isinstance(r,dict) and isinstance(r.get('BD.CDN.10YR.DQ.YLD'),dict)]
    elif currency == 'CHF':
        # Match the current ten-year spot quotation only, never SARON or the policy rate.
        content = fetch(CONFEDERATION)
        match = re.search(r'Yield on Swiss Confederation bonds</span>\s*<span>\s*([−+\-\d.]+)%\s*</span>\s*<span[^>]*>\s*(\d{2}\.\d{2}\.\d{4})\s*\(Spot interest rate for 10-year maturities\)', content)
        rows = [(datetime.strptime(match[2], '%d.%m.%Y').date().isoformat(), match[1].replace('−','-'))] if match else []
    else:
        return None
    valid = (observation(currency, day, value, today) for day, value in rows)
    return max((obs for obs in valid if obs), key=lambda obs: obs['date'], default=None)


def download_sovereign(url):
    # English JGB CSV data have Japanese Shift-JIS punctuation in the footnotes.
    return download_csv(url, encoding='cp932' if url == JGB else 'utf-8-sig')


def foreign_rate(currency, now, folder=None, fetch=download_sovereign):
    path = Path(folder) / f'sovereign-{currency}.json' if folder else None
    def read_cache():
        if path:
            try:
                raw = json.loads(path.read_text())
                if raw['sourceID'] == IDS[currency] and raw['currency'] == currency:
                    obs = observation(currency, raw['date'], raw['yield'], now.date())
                    if obs:
                        return {**obs, 'checkedAt': raw.get('checkedAt', '')}
            except (OSError, ValueError, TypeError, KeyError):
                pass
        return None
    cached = read_cache()
    if cached and cache_is_recent(cached, now):
        return cached
    try:
        latest = foreign_feed(currency, now.date(), fetch)
    except (OSError, ValueError, csv.Error, KeyError):
        latest = None
    if not latest:
        return cached
    latest['checkedAt'] = now.isoformat()
    if cached and latest['date'] < cached['date']:
        return cached
    if path:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.with_suffix('.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                existing = read_cache()
                if existing and (existing['date'], existing['checkedAt']) > (latest['date'], latest['checkedAt']):
                    return existing
                with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as output:
                    json.dump(latest, output)
                os.replace(output.name, path)
        except OSError:
            pass
    return latest


def currency_benchmark(currency, now, folder):
    if currency in IDS:
        return foreign_rate(currency, now, folder)
    if currency != 'USD':
        return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        official = pool.submit(treasury_yield, cache_dir=folder, now=now)
        yahoo = pool.submit(yahoo_ten_year_quote, cache_dir=folder, now=now)
        candidates = []
        for future, source in [(yahoo, 'tnx'), (official, None)]:
            try:
                item = future.result()
                if item:
                    candidates.append({**item, 'sourceID': source or item['sourceID'], 'currency': 'USD'})
            except Exception:
                continue  # One unavailable feed must not mask the other.
    return max(candidates, key=lambda obs: obs['date'], default=None)


def supplement_benchmarks(report):
    currencies = {major_currency(code) for code in (report.get('currency'), report.get('quoteCurrency')) if code}
    now = datetime.now(timezone.utc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {code: pool.submit(currency_benchmark, code, now, os.environ.get('TICKERTWISTER_CACHE')) for code in currencies}
        report['riskFreeRates'] = {}
        for code, job in jobs.items():
            try:
                item = job.result()
            except Exception:
                continue  # A provider outage must leave the rest of the financial report usable.
            if item:
                report['riskFreeRates'][code] = item
