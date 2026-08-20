# Decisions

Record only decisions that change the future cost of change.

## Template

### YYYY-MM-DD — Title

- **Context:** what constraint or problem required a decision.
- **Decision:** the path chosen.
- **Alternatives:** relevant options discarded.
- **Consequences:** gains, costs and the trigger to revisit.

### 2026-08-18 — Keep `CLAUDE.md` and `AGENTS.md` in the public repository

- **Context:** both files declare that the repository is built with agent
  support. The alternative was ignoring them in git so the public
  repository wouldn't reveal the workflow.
- **Decision:** keep both versioned and public.
- **Alternatives:** ignore `AGENTS.md` in `.gitignore`; keep it local only.
  Both break delegation to Codex, which reads this file from the
  repository — the cost is functional and immediate, the gain is cosmetic.
- **Consequences:** the repository states the method instead of hiding it,
  which is also verifiable by whoever reads it. Revisit if some destination
  ever requires the opposite.

### 2026-08-19 — Fixed point (Vassalou-Xing) instead of multivariate Newton

- **Context:** the Merton system has 2 equations and 2 unknowns (`V`,
  `sigma_V`), with no closed form. Multivariate Newton converges faster,
  but requires assembling and solving a 2×2 Jacobian on every iteration.
- **Decision:** fixed-point iteration — fix `sigma_V`, solve `V` by 1D
  bisection (pricing equation), update `sigma_V` from the second equation,
  repeat until both converge.
- **Alternatives:** multivariate Newton — faster (few iterations), but the
  Jacobian for these two equations isn't trivial to derive without a sign
  error, and the speed gain doesn't matter for a CLI that runs once per
  ticker.
- **Consequences:** more outer iterations (dozens, not few), but each piece
  is independently verifiable — the internal `_solve_v` is the same kind of
  1D root-finding already used elsewhere in the portfolio. Revisit if this
  project ever needs to evaluate a whole portfolio and speed becomes a real
  bottleneck.

### 2026-08-19 — Total balance-sheet liabilities, not the KMV debt convention

- **Context:** classic KMV uses "default point" = short-term debt + half of
  long-term debt, not total balance-sheet liabilities. Replicating that
  requires separating short- and long-term debt lines from `yfinance`,
  which aren't always cleanly broken out for every firm.
- **Decision:** use `Total Liabilities Net Minority Interest` as the
  model's `D` — simpler to extract reliably for any ticker.
- **Alternatives:** the full KMV convention — more faithful to the
  literature, but adds a second balance-sheet extraction with more chance
  of missing data per firm, in a cut that already carries enough technical
  risk in the solver.
- **Consequences:** total liabilities overstate the "default point" for a
  firm with a lot of long-term debt — the implied PD comes out conservative
  (higher) in those cases, documented in the README, not hidden. Revisit if
  a future cut needs a calibrated PD, not just one comparable across firms.
