# src/ai_debt_bubble_analysis/models.py
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class MarketSnapshot:
    price: float | None
    return_1y: float | None
    max_drawdown: float | None
    observations: int


@dataclass(slots=True)
class FilingEvidence:
    form: str
    filed_at: str | None
    url: str | None
    score: float
    mentions: int
    snippets: list[str]
    money_candidates: list[dict[str, Any]]


@dataclass(slots=True)
class CompanySnapshot:
    ticker: str
    name: str
    sector: str
    ai_exposure: float
    market_cap: float | None
    shares_outstanding: float | None
    ai_weighted_market_cap: float | None
    assets: float | None
    liabilities: float | None
    debt: float | None
    equity: float | None
    revenue: float | None
    capex: float | None
    debt_to_assets: float | None
    commitment_score: float
    commitment_mentions: int
    return_1y: float | None
    max_drawdown: float | None
    risk_score: float
    wealth_at_10: float | None
    wealth_at_20: float | None
    wealth_at_30: float | None
    filing: FilingEvidence


@dataclass(slots=True)
class MacroSnapshot:
    series: dict[str, dict[str, float | None]]
    stress_score: float


@dataclass(slots=True)
class OverviewSnapshot:
    generated_at: str
    monitored_companies: int
    monitored_market_cap: float
    top1_concentration_pct: float
    hhi: float
    wealth_at_10: float
    wealth_at_20: float
    wealth_at_30: float
    macro: MacroSnapshot
    companies: list[CompanySnapshot]
    alerts: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
