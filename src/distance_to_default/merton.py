"""Structural Merton model: distance-to-default via fixed-point iteration.

Equity is a call option on the firm's asset value (Black-Scholes-Merton).
Two equations, two unknowns (asset value and asset vol), no closed form:

    E = V * N(d1) - D * exp(-r*T) * N(d2)
    sigma_E * E = N(d1) * sigma_V * V

Solved with the classic Vassalou-Xing/KMV iteration: fix sigma_V, find the V
that prices equity correctly (1D root-finding via bisection); then update
sigma_V from the second equation; repeat until both stop changing.
"""

import math
from dataclasses import dataclass

_RELATIVE_TOLERANCE = 1e-8
_MAX_OUTER_ITERATIONS = 100
_MAX_INNER_ITERATIONS = 100
_LOWER_BOUND_V = 1e-6
_UPPER_BOUND_MULTIPLIER = 50.0


def _cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _d1_d2(
    v: float, liabilities: float, rate: float, horizon: float, sigma_v: float
) -> tuple[float, float]:
    d1 = (math.log(v / liabilities) + (rate + 0.5 * sigma_v * sigma_v) * horizon) / (
        sigma_v * math.sqrt(horizon)
    )
    return d1, d1 - sigma_v * math.sqrt(horizon)


def equity_price(
    v: float, liabilities: float, rate: float, horizon: float, sigma_v: float
) -> float:
    """Equity value as a European call on the assets, strike = liabilities."""
    d1, d2 = _d1_d2(v, liabilities, rate, horizon, sigma_v)
    return v * _cdf(d1) - liabilities * math.exp(-rate * horizon) * _cdf(d2)


@dataclass(frozen=True)
class Merton:
    asset_value: float
    asset_vol: float
    distance_to_default: float
    implied_pd: float


def solve(
    *,
    equity: float,
    equity_vol: float,
    liabilities: float,
    rate: float,
    horizon: float = 1.0,
) -> Merton | None:
    """Solves the Merton system. `None` if it doesn't converge.

    Extreme leverage or equity vol may have no stable fixed point within the
    iteration limit — better to report that than to return a number that
    only looked like it converged.
    """
    if equity <= 0 or equity_vol <= 0 or liabilities <= 0 or horizon <= 0:
        return None

    v = equity + liabilities
    sigma_v = equity_vol * equity / v

    for _ in range(_MAX_OUTER_ITERATIONS):
        v_new = _solve_v(equity, liabilities, rate, horizon, sigma_v)
        if v_new is None:
            return None

        d1, _ = _d1_d2(v_new, liabilities, rate, horizon, sigma_v)
        density_d1 = _cdf(d1)
        if density_d1 < 1e-12:
            return None
        sigma_v_new = equity_vol * equity / (density_d1 * v_new)

        converged = (
            abs(v_new - v) < _RELATIVE_TOLERANCE * v_new
            and abs(sigma_v_new - sigma_v) < _RELATIVE_TOLERANCE
        )
        v, sigma_v = v_new, sigma_v_new
        if converged:
            break
    else:
        return None

    _, d2 = _d1_d2(v, liabilities, rate, horizon, sigma_v)
    return Merton(
        asset_value=v,
        asset_vol=sigma_v,
        distance_to_default=d2,
        implied_pd=_cdf(-d2),
    )


def _solve_v(
    equity: float, liabilities: float, rate: float, horizon: float, sigma_v: float
) -> float | None:
    """V that prices equity correctly, for a fixed `sigma_v` — bisection."""
    low = _LOWER_BOUND_V
    high = (equity + liabilities) * _UPPER_BOUND_MULTIPLIER
    f_low = equity_price(low, liabilities, rate, horizon, sigma_v) - equity
    f_high = equity_price(high, liabilities, rate, horizon, sigma_v) - equity
    if f_low * f_high > 0:
        return None

    mid = low
    absolute_tolerance = _RELATIVE_TOLERANCE * max(equity, 1.0)
    for _ in range(_MAX_INNER_ITERATIONS):
        mid = (low + high) / 2
        f_mid = equity_price(mid, liabilities, rate, horizon, sigma_v) - equity
        if abs(f_mid) < absolute_tolerance:
            return mid
        if f_low * f_mid < 0:
            high = mid
        else:
            low, f_low = mid, f_mid
    return mid
