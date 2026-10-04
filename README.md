# AI Debt Bubble Analysis

A live research dashboard for monitoring the **wealth, leverage, financing structures, and risk transmission** behind the AI infrastructure boom.

This project is inspired by the October 4, 2026 video **“Big Tech Can't Hide This For Much Longer”** (YouTube: https://www.youtube.com/watch?v=DS6p9pEwCPs). The video's central idea is that the important question is not simply “how much debt does an AI company report?” but:

> **Where is the economic obligation, who is connected to it, and who ultimately carries the downside if the expected AI economics fail?**

The dashboard therefore follows a chain:

**AI capex → corporate balance sheet → leases / purchase commitments → SPVs & JVs → private credit → institutional holders → public equity wealth → systemic stress**

## What it measures

The first release combines public, no-key data sources:

- **SEC EDGAR/XBRL** for assets, liabilities, debt, equity, revenue, capex, filings and filing metadata.
- **SEC 10-K text scanning** for evidence of leases, purchase obligations, residual-value guarantees, VIE/SPV structures, data-center commitments and related language.
- **Yahoo Finance chart endpoint with Stooq fallback** for market prices and drawdowns.
- **FRED public CSV feeds** for VIX, high-yield spreads, the S&P 500 and financial-stress indicators.
- **U.S. Treasury daily yield data** can be added through the source layer as the project expands.

SEC's EDGAR data APIs are public and do not require API keys. The system still asks you to provide a descriptive SEC User-Agent through `SEC_USER_AGENT`, which is good practice for automated access.

## Important interpretation rule

This is a **research and monitoring system, not an accounting restatement engine**.

A filing mention of an obligation is not automatically equivalent to reported debt. The project deliberately separates:

1. **Reported leverage** — numbers extracted from XBRL.
2. **Commitment evidence** — language found in the company's filings.
3. **Market wealth exposure** — equity value that can be repriced.
4. **Transmission risk** — a heuristic score describing how many risk channels are active.

The “shadow risk” score is transparent and deterministic. It is **not** a probability of default, crash prediction, or investment recommendation.

## Dashboard

The web UI is intentionally lightweight:

- total monitored AI-complex market value
- wealth-at-risk under configurable equity drawdown scenarios
- top-company concentration and HHI
- reported leverage
- filing-derived commitment pressure
- price return and drawdown
- macro/credit stress
- filing evidence snippets
- risk alerts
- historical snapshots stored locally in SQLite

The visual language uses a black background, white text and bright signal colors so the important state changes are obvious at a glance.

## Install

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

export SEC_USER_AGENT='AI Debt Bubble Analysis research contact: you@example.com'
python -m ai_debt_bubble_analysis serve
```

Then open http://127.0.0.1:8000.

## CLI

```bash
python -m ai_debt_bubble_analysis refresh
python -m ai_debt_bubble_analysis export --output snapshot.json
python -m ai_debt_bubble_analysis serve --host 127.0.0.1 --port 8000
```

## Configuration

Edit `config/universe.toml` to change the monitored companies, macro series, scoring weights and alert thresholds.

No paid API subscription is required by the default configuration.

## Project roadmap

### Phase 1 — Live wealth/risk monitor

Included in this repository:

- async data collection
- SEC/XBRL fundamentals
- filing evidence scanner
- market prices and drawdowns
- macro stress series
- transparent risk scoring
- SQLite snapshots
- browser dashboard
- tests

### Phase 2 — Shadow financing graph

Add a normalized entity graph:

```
Company
  ├── SPV / VIE / JV
  │     ├── Lender
  │     ├── Bond
  │     └── Asset
  ├── Lease / capacity agreement
  └── Guarantee / residual-value support
```

Each edge will carry an amount, maturity, source filing, confidence and last-seen date.

### Phase 3 — Institutional wealth transmission

Add public holdings and ownership sources to answer:

- Which funds hold the affected debt?
- Which insurers and pension pools are exposed?
- How concentrated is exposure?
- Which instruments become correlated under stress?

The project should prefer primary filings and disclosed holdings rather than guessing private-credit ownership.

### Phase 4 — Stress engine

Run scenarios such as:

- AI capex growth stops.
- Hyperscaler revenue growth misses expectations.
- GPU residual values fall rapidly.
- Data-center utilization stays below underwriting assumptions.
- Credit spreads widen by configurable amounts.
- Equity valuations fall by 10/20/30/50%.
- Refinancing costs rise while commitments remain fixed.

The result should be a **transmission map**, not a single scary number.

### Phase 5 — Historical research

Build a comparable dataset for:

- dot-com infrastructure
- telecom buildouts
- 2008 structured-credit channels
- shale/energy financing
- modern AI infrastructure

Then compare leverage, duration, collateral decay, concentration and financing structures across cycles.

## Why this exists

The useful output is not a headline like “$X trillion hidden debt.”

The useful output is a continuously updated answer to:

> **How much market wealth is connected to the AI buildout, what obligations support it, where are those obligations recorded, and which links become fragile when the underlying economics weaken?**

## License

MIT
