"""Traceable valuation inputs. Missing disclosures never become fabricated zeroes."""
import csv
import fcntl
import io
import json
import os
import ssl
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone, timedelta
from http.client import HTTPException
from pathlib import Path
from urllib.request import Request, urlopen

TREASURY_BASE = 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates'
FRED_SERIES = 'https://fred.stlouisfed.org/series/DGS10'
CACHE_TTL = timedelta(minutes=15)


def observation(source, observed, value, today):
    """Build an attributed observation only for a valid published date and rate."""
    try:
        if not isinstance(observed, str) or isinstance(value, bool):
            return None
        when = date.fromisoformat(observed)
        rate = float(value)
        if when > today or not -100 < rate < 100:
            return None
    except (TypeError, ValueError, OverflowError):
        return None
    if source == 'treasury':
        url = (f'{TREASURY_BASE}/TextView?type=daily_treasury_yield_curve'
               f'&field_tdr_date_value_month={when:%Y%m}')
        label = 'U.S. Treasury / 10-Year CMT'
    elif source == 'fred':
        url, label = FRED_SERIES, 'FRED / Federal Reserve DGS10'
    else:
        return None
    return {'yield': rate, 'date': when.isoformat(), 'sourceID': source, 'source': label, 'url': url}


def download_csv(url, encoding='utf-8-sig'):
    import certifi
    request = Request(url, headers={'User-Agent': 'Tickertwister/1.1', 'Accept': 'text/csv'})
    with urlopen(request, timeout=5, context=ssl.create_default_context(cafile=certifi.where())) as response:
        return response.read(100000).decode(encoding)


def latest_csv(source, url, today, fetch):
    result = None
    try:
        for row in csv.DictReader(io.StringIO(fetch(url))):
            if source == 'treasury':
                try:
                    observed = datetime.strptime(row['Date'], '%m/%d/%Y').date().isoformat()
                except (KeyError, ValueError, TypeError):
                    continue
                value = row.get('10 Yr')
            else:
                observed = row.get('observation_date') or row.get('DATE') or row.get('date')
                value = row.get('DGS10')
            item = observation(source, observed, value, today)
            if item and (not result or item['date'] > result['date']):
                result = item
    except (OSError, ValueError, csv.Error, HTTPException):
        return None
    return result


def read_cached(path, today):
    if path:
        try:
            raw = json.loads(path.read_text())
            source = raw.get('sourceID')
            # Review 2 only used FRED. Its daily cache must be rechecked against Treasury.
            legacy = not source and raw.get('source') == 'FRED / Federal Reserve DGS10'
            item = observation('fred' if legacy else source, raw['date'], raw['yield'], today)
            if item:
                item['retrievedAt'] = raw['retrievedAt'] if isinstance(raw.get('retrievedAt'), str) else ''
                if not legacy:
                    item['checkedAt'] = raw.get('checkedAt', '')
                return item
        except (OSError, AttributeError, KeyError, TypeError, ValueError):
            pass
    return None


def cache_is_recent(cached, now):
    try:
        age = now - datetime.fromisoformat(cached['checkedAt'])
        return timedelta(0) <= age < CACHE_TTL
    except (KeyError, TypeError, ValueError):
        return False


def observation_order(item):
    # On the same observation date, favour Treasury, then the newest retrieval (revisions).
    return item['date'], item['sourceID'] == 'treasury', item.get('retrievedAt', '')


def treasury_yield(fetch=download_csv, cache_dir=None, now=None):
    now = now or datetime.now(timezone.utc)
    today = now.date()
    cache_dir = cache_dir or os.environ.get('TICKERTWISTER_CACHE')
    path = Path(cache_dir) / 'treasury-dgs10.json' if cache_dir else None
    cached = read_cached(path, today)
    if cached and cache_is_recent(cached, now):
        return cached

    years = {today.year, (today - timedelta(days=7)).year}
    feeds = [('treasury', f'{TREASURY_BASE}/daily-treasury-rates.csv/{year}/all'
              f'?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv')
             for year in sorted(years)]
    feeds.append(('fred', 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10&cosd='
                  + str(today - timedelta(days=30))))
    with ThreadPoolExecutor(max_workers=len(feeds)) as pool:
        jobs = [pool.submit(latest_csv, source, url, today, fetch) for source, url in feeds]
        observations = [item for job in jobs if (item := job.result())]
    if not observations:
        return cached
    for item in observations:
        item['retrievedAt'] = now.isoformat()
    if cached:
        observations.append(cached)
    result = max(observations, key=observation_order).copy()
    result['checkedAt'] = now.isoformat()
    if path:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Two company analyses can finish out of order. Never replace a later
            # observation (or a correction) with an older concurrent result.
            with path.with_suffix('.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                other = read_cached(path, today)
                if other and observation_order(other) > observation_order(result):
                    return other
                with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as tmp:
                    json.dump(result, tmp)
                os.replace(tmp.name, path)
        except OSError:
            pass
    return result


def valuation_inputs(report):
    balances = sorted([*report.get('years', []), *report.get('quarters', [])],
                      key=lambda row: row['end'], reverse=True)
    for row in balances:
        # Yahoo TotalDebt already includes its reported capital lease obligations.
        debt = row.get('debt')
        source = 'TotalDebt'
        if debt is None:
            long_debt = row.get('longDebtAndLeases')
            short_debt = row.get('currentDebtAndLeases')
            if long_debt is None or short_debt is None:
                continue
            debt = long_debt + short_debt
            source = 'LongTermDebtAndCapitalLeaseObligation + CurrentDebtAndCapitalLeaseObligation'
        cash = row.get('cash')
        if cash is not None:
            return {'grossDebt': debt, 'cash': cash, 'netDebt': debt - cash,
                    'balanceDate': row['end'], 'debtSource': source}
    return {'netDebt': None, 'balanceDate': None}


def yahoo_ten_year_quote(cache_dir=None, now=None):
    """Last ^TNX close in percentage points. Reuse the benchmark during batch runs."""
    import yfinance as yf
    now = now or datetime.now(timezone.utc)
    cache_dir = cache_dir or os.environ.get('TICKERTWISTER_CACHE')
    path = Path(cache_dir) / 'wacc-tnx.json' if cache_dir else None
    if path:
        try:
            cached = json.loads(path.read_text())
            if (isinstance(cached, dict) and cache_is_recent(cached, now)
                    and isinstance(cached.get('yield'), (float, int))
                    and -100 < cached['yield'] < 100
                    and date.fromisoformat(cached['date']) <= now.date()):
                return {'date': cached['date'], 'yield': cached['yield']}
        except (KeyError, ValueError, OSError, TypeError):
            pass
    try:
        history = yf.Ticker('^TNX').history(period='5d', interval='1d', auto_adjust=False,
                                            actions=False, timeout=5)
        closing = history['Close'].dropna().sort_index()
        if closing.empty:
            return None
        rate, day = float(closing.iloc[-1]), closing.index[-1].date()
        if not -100 < rate < 100 or day > now.date():
            return None
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        return None
    result = {'date': day.isoformat(), 'yield': rate}
    if path:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as tmp:
                json.dump({**result, 'checkedAt': now.isoformat()}, tmp)
            os.replace(tmp.name, path)
        except OSError:
            pass
    return result
