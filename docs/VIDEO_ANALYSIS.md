# docs/VIDEO_ANALYSIS.md

# Video-derived project thesis

Source video:

https://www.youtube.com/watch?v=DS6p9pEwCPs

Title:

**Big Tech Can't Hide This For Much Longer**

The indexed description describes a financing system in which large AI companies can move economically connected obligations into separate legal entities. It uses Meta's Hyperion data center as the central example and argues that the important risk is not just headline corporate debt, but where the economic burden ultimately lands.

## Core claims translated into engineering requirements

| Video idea | Monitoring capability |
| --- | --- |
| AI infrastructure is financed with debt | Track reported debt, capex and market value |
| Debt can sit in SPVs/JVs | Search filings for VIE/SPV/JV language |
| Long-term leases can replace upfront ownership | Detect lease and purchase-commitment language |
| Guarantees can leave economic exposure outside reported debt | Detect residual-value and guarantee disclosures |
| Risk can move to private credit | Create a future lender/institution graph |
| Institutions can hold the downstream exposure | Add future 13F/insurance/pension ownership adapters |
| Equity wealth can be destroyed if expectations reset | Calculate 10/20/30/50% market-value scenarios |
| Concentration makes a local shock systemic | Track top-1 concentration and HHI |
| A “hidden debt” headline may mix different accounting concepts | Preserve source type, evidence text, confidence and definitions |

## The Meta / Hyperion case

Current reporting describes Meta's Hyperion infrastructure as a joint-venture/project-finance structure in which the project vehicle raises debt while Meta remains economically connected through its use of the facility and contractual arrangements.

That makes Hyperion an ideal **template object** for the project's future obligation graph:

```
Meta
 |
 | long-term lease / usage
 v
Beignet / project vehicle
 |
 +--> project debt
 |
 +--> outside equity
 |
 +--> data-center assets
 |
 +--> residual-value / support terms
```

The graph should never flatten this into one fake “hidden debt” number.

Instead every edge should answer:

- What obligation exists?
- Who owes whom?
- Is it debt, lease, guarantee, purchase commitment or equity?
- What is the amount?
- What is the maturity?
- What collateral supports it?
- Which filing disclosed it?
- How certain is the extraction?
- Has the value changed since the last filing?

## Why the project tracks wealth separately

The stock market gives a visible mark-to-market value for the equity claim.

That lets the system answer a different question:

> “How much quoted equity wealth is connected to this financing complex, and how much would be repriced under a stress scenario?”

This is why the dashboard reports both balance-sheet ratios and market-value scenarios.

## Important correction to the headline framing

The video description uses the phrase “hidden debt.”

The project intentionally does not hard-code that classification.

Current reporting has noted that broad $1.65 trillion figures can combine items with different accounting meanings, including total liabilities and off-balance-sheet commitments. The system therefore stores evidence and category labels instead of silently converting every commitment into debt.

That distinction is essential for a credible research tool.

## Expansion target

The mature system should become a continuously updated **AI Financial Plumbing Monitor**:

```
                 +----------------------+
                 |  AI CAPEX / DEMAND   |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 | HYPERSCALER / OEM    |
                 +----------+-----------+
                            |
          +-----------------+------------------+
          |                 |                  |
          v                 v                  v
       balance         lease / PPA /      SPV / JV /
       sheet debt      purchase terms      VIE financing
          |                 |                  |
          +-----------------+------------------+
                            |
                            v
                 +----------------------+
                 | PRIVATE CREDIT /     |
                 | PROJECT FINANCE      |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 | FUNDS / INSURERS /   |
                 | PENSIONS / BANKS     |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 | PUBLIC EQUITY /      |
                 | MARKET WEALTH        |
                 +----------------------+
                            |
                            v
                 +----------------------+
                 | STRESS / REPRICING   |
                 +----------------------+
```

The current release implements the first half of that map. The next major engineering step is the evidence-backed obligation graph.
