# distance-to-default

Distance-to-default and implied PD (1 year) for a public firm, via the
structural Merton model — equity treated as a call on the firm's asset
value, exactly like an option.

## The problem

Agency ratings are a black box and update slowly. A generic statistical
classifier over third-party tabular data doesn't always generalize to a real
firm. The Merton model (the basis of KMV, used by real credit risk desks)
does something else: it derives default probability from the capital
structure and the market vol of the equity itself — data any public firm
already discloses.

## Result

```console
$ uv run python -m distance_to_default evaluate --ticker F
field,value
equity,57800198736.82
equity_vol,0.373805
liabilities,253180000000.00
risk_free_rate,0.051000
asset_value,298383480893.35
asset_vol,0.072506
distance_to_default,2.9329
implied_pd,0.001679

$ uv run python -m distance_to_default evaluate --ticker AAPL | grep -E 'distance|implied_pd'
distance_to_default,12.0741
implied_pd,0.000000

$ uv run python -m distance_to_default evaluate --ticker AMC | grep -E 'distance|implied_pd'
distance_to_default,1.0737
implied_pd,0.141483
```

Three real tickers, run for real: Apple (low leverage relative to market
cap) gets a high distance-to-default and PD ~0%; Ford (heavy leverage, its
own financing arm) lands in the middle; AMC (historically stressed) gets a
distance below 1.1 standard deviations and a ~14% one-year PD. The model
discriminates credit risk plausibly across well-known names without having
seen any rating.

## Problem and scope

- **User:** me, and whoever reviews the portfolio evaluating for
  quantitative research/risk.
- **Decision:** structural PD can be estimated for any public firm with a
  liquid stock, with no institutional data.
- **Input:** `yfinance` — market capitalization, price history (annualized
  vol) and `Total Liabilities Net Minority Interest` from the balance
  sheet. Risk-free rate: FRED `DGS3MO` via Postgres from
  [`public-market-data`](../public-market-data).
- **Out of scope:** SEC EDGAR, the full KMV debt convention (short-term +
  0.5×long-term — this cut uses total liabilities), calibration against
  real historical default rates, multi-issuer portfolios.

## Architecture

```
yfinance                          Postgres (public-market-data)
    │  equity, vol, liabilities        │  DGS3MO via series_vintage
    ▼                                  ▼
sources/equity.py                risk_free_rate.py
    │                                  │
    └──────────────┬───────────────────┘
                    ▼
               merton.py          solves the 2-equation,
                    │              2-unknown system by fixed point
                    ▼
                 cli.py            distance-to-default, PD
```

Two decisions worth explaining:

**Fixed point, not multivariate Newton.** The Merton system is 2 equations
and 2 unknowns (asset value and asset vol), but solving it with
two-dimensional Newton requires assembling and inverting a 2×2 Jacobian
numerically — more code, more room for a sign or partial-derivative error.
The fixed-point iteration (Vassalou-Xing/KMV) decouples it: fix `sigma_V`,
find `V` by 1D bisection (reusing the same discipline as
`vol-implicita-spx`), update `sigma_V` from the second equation, repeat.
Slower, easier to verify line by line.

**No external ground truth — verification is a synthetic round trip.**
There's no "Yahoo IV" for credit: no public source publishes a firm's
structural PD to compare against. `tests/test_merton.py` generates `E` and
`sigma_E` from a chosen `(V, sigma_V)` (the forward problem, which has a
closed form), runs the solver backward, and confirms it recovers the
original pair — the same numerical-precision discipline, applied to the
inverse problem.

## Run locally

Requirements: Python 3.12, `uv`, Docker (for the ephemeral test Postgres),
and [`public-market-data`](../public-market-data) running with the
`DGS3MO` series ingested:

```bash
# in public-market-data:
docker compose up -d
uv run python -m public_market_data ingest --source fred --series DGS3MO
```

```bash
uv sync
cp .env.example .env
uv run python -m distance_to_default evaluate --ticker AAPL
```

Without the `DGS3MO` series ingested, the command explains why and exits
with code 2. If the solver doesn't converge for a firm with extreme
leverage/vol, it exits with code 1 and shows the inputs used, instead of
returning a bad number.

## Quality

```bash
uv run python scripts/check.py
```

The check runs format, lint, types and tests with coverage. It's the same
command CI runs, on Windows, Linux and macOS.

## Structure

```text
src/distance_to_default/
    merton.py             Merton system and the fixed-point solver
    sources/equity.py     yfinance adapter, testable with a fake ticker
    risk_free_rate.py     reads the public-market-data public interface
    cli.py                coordination
```

## Limitations

- Total liabilities from the most recent balance sheet, not the full KMV
  convention (short-term + half of long-term) — overstates "effective" debt
  for firms with significant long-term debt.
- Historical equity vol (1-year log return), not implied — mixes past vol
  regime with the current capital structure.
- No calibration: the implied PD hasn't been compared against real
  historical default rates for any rating class. The value is directional
  (discriminates relative risk across firms), not a calibrated probability.

## License

MIT. Third-party data keeps its own license and terms of use.
