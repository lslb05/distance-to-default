"""Command-line interface. Logic lives in the package; this only coordinates."""

import argparse
import sys
from datetime import UTC, datetime

import psycopg
import yfinance as yf

from distance_to_default.config import Settings
from distance_to_default.merton import solve
from distance_to_default.risk_free_rate import RateUnavailable, rate_3_months
from distance_to_default.sources.equity import (
    InsufficientData,
    annualized_historical_vol,
    market_value,
    total_liabilities,
)


def _arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="distance-to-default")
    subparsers = parser.add_subparsers(dest="command", required=True)

    evaluate = subparsers.add_parser(
        "evaluate", help="distance-to-default for a ticker"
    )
    evaluate.add_argument("--ticker", required=True)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _arguments(argv)
    config = Settings()
    today = datetime.now(UTC).date()

    try:
        with psycopg.connect(config.market_data_dsn) as connection:
            rate = rate_3_months(connection, at=today)
    except RateUnavailable as error:
        print(str(error), file=sys.stderr)
        return 2
    except psycopg.OperationalError as error:
        print(
            f"could not connect to dados-mercado-publico's Postgres: {error}",
            file=sys.stderr,
        )
        return 2

    ticker = yf.Ticker(args.ticker)
    try:
        equity = market_value(ticker=ticker)
        equity_vol = annualized_historical_vol(ticker=ticker)
        liabilities = total_liabilities(ticker=ticker)
    except InsufficientData as error:
        print(f"insufficient data for {args.ticker}: {error}", file=sys.stderr)
        return 2

    result = solve(
        equity=equity, equity_vol=equity_vol, liabilities=liabilities, rate=rate
    )
    if result is None:
        print(
            f"the Merton solver did not converge for {args.ticker} "
            f"(equity={equity:.0f}, equity_vol={equity_vol:.4f}, "
            f"liabilities={liabilities:.0f})",
            file=sys.stderr,
        )
        return 1

    print("field,value")
    print(f"equity,{equity:.2f}")
    print(f"equity_vol,{equity_vol:.6f}")
    print(f"liabilities,{liabilities:.2f}")
    print(f"risk_free_rate,{rate:.6f}")
    print(f"asset_value,{result.asset_value:.2f}")
    print(f"asset_vol,{result.asset_vol:.6f}")
    print(f"distance_to_default,{result.distance_to_default:.4f}")
    print(f"implied_pd,{result.implied_pd:.6f}")
    return 0
