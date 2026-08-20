import math

import pytest

from distance_to_default.merton import _cdf, _d1_d2, equity_price, solve

_RATE = 0.05
_HORIZON = 1.0


def _generate_equity_and_vol(
    *, asset_value: float, asset_vol: float, liabilities: float
) -> tuple[float, float]:
    """Derives (E, sigma_E) from a known (V, sigma_V) — the forward problem."""
    equity = equity_price(asset_value, liabilities, _RATE, _HORIZON, asset_vol)
    d1, _ = _d1_d2(asset_value, liabilities, _RATE, _HORIZON, asset_vol)
    equity_vol = _cdf(d1) * asset_vol * asset_value / equity
    return equity, equity_vol


@pytest.mark.parametrize(
    ("asset_value", "asset_vol", "liabilities"),
    [
        (1_000.0, 0.25, 400.0),  # moderate leverage
        (1_000.0, 0.15, 150.0),  # low leverage, low vol
        (1_000.0, 0.45, 800.0),  # high leverage, high vol
    ],
)
def test_solver_recovers_original_v_and_sigma_v(
    asset_value: float, asset_vol: float, liabilities: float
) -> None:
    equity, equity_vol = _generate_equity_and_vol(
        asset_value=asset_value, asset_vol=asset_vol, liabilities=liabilities
    )

    result = solve(
        equity=equity, equity_vol=equity_vol, liabilities=liabilities, rate=_RATE
    )

    assert result is not None
    assert result.asset_value == pytest.approx(asset_value, rel=1e-4)
    assert result.asset_vol == pytest.approx(asset_vol, rel=1e-4)


def test_distance_to_default_and_pd_are_consistent_with_d2() -> None:
    asset_value, asset_vol, liabilities = 1_000.0, 0.3, 500.0
    equity, equity_vol = _generate_equity_and_vol(
        asset_value=asset_value, asset_vol=asset_vol, liabilities=liabilities
    )

    result = solve(
        equity=equity, equity_vol=equity_vol, liabilities=liabilities, rate=_RATE
    )

    assert result is not None
    _, expected_d2 = _d1_d2(asset_value, liabilities, _RATE, _HORIZON, asset_vol)
    assert result.distance_to_default == pytest.approx(expected_d2, rel=1e-3)
    assert result.implied_pd == pytest.approx(
        0.5 * (1 - math.erf(expected_d2 / math.sqrt(2))), rel=1e-3
    )


def test_higher_leverage_produces_higher_pd() -> None:
    low_leverage_equity, low_leverage_vol = _generate_equity_and_vol(
        asset_value=1_000.0, asset_vol=0.3, liabilities=200.0
    )
    high_leverage_equity, high_leverage_vol = _generate_equity_and_vol(
        asset_value=1_000.0, asset_vol=0.3, liabilities=800.0
    )

    low_result = solve(
        equity=low_leverage_equity,
        equity_vol=low_leverage_vol,
        liabilities=200.0,
        rate=_RATE,
    )
    high_result = solve(
        equity=high_leverage_equity,
        equity_vol=high_leverage_vol,
        liabilities=800.0,
        rate=_RATE,
    )

    assert low_result is not None
    assert high_result is not None
    assert high_result.implied_pd > low_result.implied_pd


@pytest.mark.parametrize(
    ("equity", "equity_vol", "liabilities"),
    [(0.0, 0.3, 500.0), (1000.0, 0.0, 500.0), (1000.0, 0.3, 0.0)],
)
def test_invalid_input_returns_none(
    equity: float, equity_vol: float, liabilities: float
) -> None:
    assert (
        solve(equity=equity, equity_vol=equity_vol, liabilities=liabilities, rate=_RATE)
        is None
    )
