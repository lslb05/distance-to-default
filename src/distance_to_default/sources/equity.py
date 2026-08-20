"""Equity data access via yfinance: market value, vol and total liabilities."""

from __future__ import annotations

import math
from typing import Any, Protocol

_TRADING_DAYS_PER_YEAR = 252
_LIABILITIES_LINE = "Total Liabilities Net Minority Interest"


class InsufficientData(Exception):
    """Not enough price history or balance-sheet data was available."""


class TickerLike(Protocol):
    """The subset of `yfinance.Ticker` used here — injectable in tests."""

    fast_info: Any
    balance_sheet: Any

    def history(self, period: str) -> Any: ...


def market_value(*, ticker: TickerLike) -> float:
    """Current market capitalization — the `E` in the Merton model."""
    return float(ticker.fast_info["marketCap"])


def annualized_historical_vol(*, ticker: TickerLike) -> float:
    """Annualized standard deviation of daily log returns over the last year."""
    closes = ticker.history(period="1y")["Close"]
    log_returns = closes.apply(math.log).diff().dropna()
    if len(log_returns) < 2:
        raise InsufficientData("not enough price history to estimate vol")
    return float(log_returns.std() * math.sqrt(_TRADING_DAYS_PER_YEAR))


def total_liabilities(*, ticker: TickerLike) -> float:
    """Most recent `Total Liabilities Net Minority Interest` from the balance sheet."""
    balance_sheet = ticker.balance_sheet
    if _LIABILITIES_LINE not in balance_sheet.index:
        raise InsufficientData(f"'{_LIABILITIES_LINE}' not found in balance sheet")
    values = balance_sheet.loc[_LIABILITIES_LINE].dropna()
    if values.empty:
        raise InsufficientData(f"'{_LIABILITIES_LINE}' has no non-null value")
    return float(values.iloc[0])
