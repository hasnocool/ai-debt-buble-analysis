# docs/METHODOLOGY.md

# Methodology

## 1. Start with the economic obligation

The system treats corporate leverage as more than the `debt` line on a balance sheet.

It tracks four separate dimensions:

- **Reported leverage:** XBRL debt relative to assets.
- **Commitment evidence:** filing language pointing to leases, guarantees, purchase obligations, SPVs/VIEs, JVs, capacity contracts and data-center commitments.
- **Market wealth:** equity market value represented by shares outstanding multiplied by the latest observed price.
- **Macro stress:** public credit and volatility indicators.

## 2. Why the filing scanner exists

The video's example is important because a project can be economically connected to a company without appearing as a conventional corporate debt liability.

The scanner does not claim that every detected phrase represents debt.

Instead it produces an evidence score:

`evidence_score = 8 × distinct_watch_terms + 2.5 × min(total_mentions, 20)`

The score is capped at 100.

The resulting snippets are shown verbatim enough to let the researcher open the underlying 10-K and verify context.

## 3. Composite risk signal

The company score is:

`R = wL + wC + wM + wD`

Where:

- `L` = normalized reported debt/assets
- `C` = filing commitment evidence
- `M` = one-year market heat
- `D` = maximum observed one-year drawdown

Default weights are 30/30/20/20.

This is deliberately not a statistical probability. It is a transparent prioritization score for investigation.

## 4. Market wealth

For each company:

`market_cap = shares_outstanding × latest_price`

The dashboard also applies an AI-exposure factor from configuration:

`ai_weighted_market_cap = market_cap × ai_exposure`

Scenario wealth loss is simply:

`wealth_at_r = monitored_market_cap × r`

This answers a different question from credit loss:

> How much quoted equity wealth would be repriced under a broad market decline?

## 5. Concentration

Top-1 concentration is:

`largest_ai_weighted_market_cap / total_ai_weighted_market_cap`

HHI is:

`10000 × Σ(weight_i²)`

Higher values mean a more concentrated monitored universe.

## 6. Macro stress

FRED series are converted to rolling z-scores using the downloaded lookback window.

The current release uses:

- VIX
- high-yield spread
- St. Louis Fed Financial Stress Index

Those z-scores are combined into a bounded 0–100 dashboard signal centered around 50.

## 7. What the system intentionally does not do

It does not:

- call off-balance-sheet obligations “hidden debt” automatically
- infer private-credit ownership without disclosed evidence
- pretend lease commitments are identical to bonds
- produce default probabilities from a handful of ratios
- make investment recommendations
- rely on an LLM to invent financial facts

The next major step is a source-backed obligation graph where every edge has an amount, date, maturity, counterparty, filing source and confidence.
