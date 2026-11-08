"""Tickertwister. Copyright ©2022 Bob Ceulemans, MD. Apache-2.0.
Modern data adapter and financial analysis. Missing values remain None.
"""
import math
import re
import logging
from datetime import datetime, timezone
import pandas as pd
import yfinance as yf


def number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def divide(a, b):
    return a / b if a is not None and b is not None and b > 0 else None


class DataUnavailable(RuntimeError):
    pass


class MarketData:
    def __init__(self, ticker, provider=None):
        self.ticker = ticker.strip().upper()
        if not re.fullmatch(r'[A-Z0-9^][A-Z0-9.^=\-]{0,19}', self.ticker):
            raise ValueError('Ongeldig tickersymbool.')
        self.stock = provider if provider is not None else yf.Ticker(self.ticker)
        self.warnings = []
        self.info = self._fetch('get_info', {})
        self.income = self._fetch('get_income_stmt', pd.DataFrame(), freq='yearly', pretty=False)
        self.balance = self._fetch('get_balance_sheet', pd.DataFrame(), freq='yearly', pretty=False)
        self.cashflow = self._fetch('get_cashflow', pd.DataFrame(), freq='yearly', pretty=False)
        if not self.info and all(f.empty for f in (self.income, self.balance, self.cashflow)):
            raise DataUnavailable('Geen gegevens beschikbaar. Controleer de ticker of probeer later opnieuw; Yahoo kan tijdelijk onbereikbaar zijn.')
        self.fetched_at = datetime.now(timezone.utc).isoformat(timespec='seconds')

    def _fetch(self, method, fallback, **kwargs):
        try:
            result = getattr(self.stock, method)(**kwargs)
            if result is None or (isinstance(result, pd.DataFrame) and result.empty) or (isinstance(result, dict) and not result):
                self.warnings.append(f'{method}: geen gegevens beschikbaar.')
                return fallback
            return result
        except Exception:
            logging.getLogger(__name__).exception('Yahoo request failed: %s', method)
            self.warnings.append(f'{method}: ophalen mislukt; deze gegevens ontbreken.')
            return fallback
