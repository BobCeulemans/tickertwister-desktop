"""Optional current FX snapshot; never infer an ADR ratio from a price difference."""
from datetime import datetime, timezone
import math
import re
import yfinance as yf

# Sony's issuer disclosure confirms 1 ADR = 1 common share after its 2024 split.
# Other foreign listings are deliberately not assumed to have the same share basis.
VERIFIED_BASES = {'SONY': {'verified': True, 'ordinaryPerQuote': 1,
    'source': 'https://www.sec.gov/Archives/edgar/data/313838/000110465924060803/tm2414258d1_6k.htm'}}

def supplement_currency(report, factory=yf.Ticker, now=None):
    q = report.get('quote') or {}
    source, target = q.get('currency'), report.get('currency')
    if not source or not target or source == target:
        return
    if report.get('symbol') in VERIFIED_BASES:
        report['quoteBasis'] = dict(VERIFIED_BASES[report['symbol']])
    if not all(re.fullmatch(r'[A-Z]{3}', c) for c in (source, target)):
        return
    now = now or datetime.now(timezone.utc)
    symbol = source + target + '=X'
    try:
        frame = factory(symbol).history(period='5d', auto_adjust=False)
        closes = frame['Close'].dropna()
        if closes.empty:
            return
        rate = float(closes.iloc[-1])
        stamp = closes.index[-1].to_pydatetime()
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        if not math.isfinite(rate) or rate <= 0 or abs((now-stamp).total_seconds()) > 7*86400:
            return
        report['fx'] = dict(fromCurrency=source, to=target, rate=rate, at=stamp.isoformat(), source='Yahoo Finance', symbol=symbol)
        report['fx']['from'] = report['fx'].pop('fromCurrency')
    except Exception:
        # Missing optional FX must not discard the financial analysis.
        return
