# Project contract — Distance to Default

Read the global `CLAUDE.md` and use this file for what's specific to this
repository.

## Product outcome

- **Problem:** a public firm's PD is normally a black box (agency rating)
  or a statistical classifier over third-party tabular data. The structural
  Merton/KMV model — equity as a call on the firm's asset value — connects
  credit risk to real option pricing.
- **User:** me, and whoever reviews the portfolio evaluating for
  quantitative research/risk.
- **Verifiable output:** for a company and a date, distance-to-default and
  implied PD (1 year), via numerical inversion of the Merton system (2
  non-linear equations, 2 unknowns: asset value and asset vol).
- **Allowed data source:** `yfinance` — equity price/vol and
  `Total Liabilities Net Minority Interest` from the balance sheet.
  Risk-free rate: FRED `DGS3MO` via Postgres from `dados-mercado-publico`.
- **Smallest end-to-end cut:** a CLI that takes a ticker and returns
  distance-to-default, implied PD and the inputs used (equity value, equity
  vol, total liabilities, risk-free rate).
- **Out of scope:** SEC EDGAR, the full KMV debt convention (short-term +
  0.5×long-term — this cut uses total liabilities), calibration against
  real historical default rates, multi-issuer portfolios.

Do not implement while a `FILL_IN` that changes the design is still open.

## Commands

```bash
uv sync
uv run python scripts/format.py
uv run python scripts/check.py
```

## Local rules

- The package is `distance_to_default` and lives in `src/distance_to_default`.
- Notebooks import from `src/`; production code never imports a notebook.
- Configuration comes from the environment via `Settings`.
- Preserve raw data and time-vintage metadata whenever there's ingestion.
- Update this file when a structural decision changes.

## Style

Public code, read by people. The rule is restraint — the full list is in
`AGENTS.md`, "Style" section, and applies equally to me and to Codex.

- A comment explains *why*, never *what*. If it paraphrases the line below,
  delete it; if the line needs paraphrasing, rename the variable instead.
- Docstrings only where the signature isn't enough (unit, timezone, side
  effect, what it raises). A three-line private helper doesn't need one.
- Tests assert behavior that can break, not a constant. Coverage is a
  consequence of testing what matters, never a target to inflate.
- Don't catch an exception you don't know how to handle; don't abstract for
  a single caller.

## Commit authorship

Author and committer are one and the same: the repository owner. No
`Co-Authored-By:`, no session trailer, no mention of Claude, Codex or any
tool. Don't change `user.name` or `user.email`.

## Session state

- **Decided:** first cut delivered — CLI `evaluate --ticker` that solves the
  Merton system by fixed point and returns distance-to-default and implied
  PD. Validated by a synthetic round trip (no external ground truth is
  possible for credit) and by a real run against AAPL/F/AMC — discriminates
  risk plausibly (PD ~0% for AAPL, ~14% for AMC).
- **Pending:** nothing blocking; next cuts are scope extensions.
- **Next step:** evaluate whether to swap total liabilities for the KMV
  debt convention (short-term + 0.5×long-term), or whether calibration
  against real historical default rates (SEC EDGAR) is the more valuable
  cut.
