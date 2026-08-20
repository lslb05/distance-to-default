import math

import pandas as pd
import pytest

from distance_to_default.sources.equity import (
    InsufficientData,
    annualized_historical_vol,
    market_value,
    total_liabilities,
)


class _FakeTicker:
    def __init__(
        self,
        *,
        market_cap: float = 1.0,
        prices: list[float] | None = None,
        balance_sheet: pd.DataFrame | None = None,
    ) -> None:
        self.fast_info = {"marketCap": market_cap}
        self._prices = prices or []
        self.balance_sheet = (
            balance_sheet if balance_sheet is not None else pd.DataFrame()
        )

    def history(self, period: str) -> pd.DataFrame:
        return pd.DataFrame({"Close": self._prices})


def test_market_value_reads_market_cap() -> None:
    ticker = _FakeTicker(market_cap=57_800_198_736.82)

    assert market_value(ticker=ticker) == pytest.approx(57_800_198_736.82)


def test_historical_vol_of_constant_series_is_zero() -> None:
    ticker = _FakeTicker(prices=[100.0] * 30)

    assert annualized_historical_vol(ticker=ticker) == pytest.approx(0.0, abs=1e-9)


def test_historical_vol_recovers_known_vol_from_synthetic_series() -> None:
    # Constant 1% daily log return in magnitude, alternating sign — sample
    # standard deviation is exactly 0.01 before annualizing.
    prices = [100.0]
    for i in range(60):
        step = 0.01 if i % 2 == 0 else -0.01
        prices.append(prices[-1] * math.exp(step))
    ticker = _FakeTicker(prices=prices)

    result = annualized_historical_vol(ticker=ticker)

    assert result == pytest.approx(0.01 * math.sqrt(252), rel=2e-2)


def test_historical_vol_with_few_prices_raises() -> None:
    ticker = _FakeTicker(prices=[100.0])

    with pytest.raises(InsufficientData):
        annualized_historical_vol(ticker=ticker)


def test_total_liabilities_picks_the_most_recent_column() -> None:
    balance_sheet = pd.DataFrame(
        {"2025-12-31": [253_180.0], "2024-12-31": [240_000.0]},
        index=["Total Liabilities Net Minority Interest"],
    )
    ticker = _FakeTicker(balance_sheet=balance_sheet)

    assert total_liabilities(ticker=ticker) == pytest.approx(253_180.0)


def test_total_liabilities_without_the_line_raises() -> None:
    balance_sheet = pd.DataFrame({"2025-12-31": [1.0]}, index=["Other Line"])
    ticker = _FakeTicker(balance_sheet=balance_sheet)

    with pytest.raises(InsufficientData):
        total_liabilities(ticker=ticker)
