# src/ai_debt_bubble_analysis/scoring.py
from __future__ import annotations


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def normalize(value: float, low: float, high: float) -> float:
    if high == low:
        return 0.0
    return clamp((value - low) / (high - low) * 100.0)


def leverage_score(debt_to_assets: float | None) -> float:
    if debt_to_assets is None:
        return 0.0
    # 0% -> 0, 60%+ -> 100. This is a signal scale, not a rating.
    return normalize(debt_to_assets, 0.0, 0.60)


def market_heat_score(return_1y: float | None) -> float:
    if return_1y is None:
        return 0.0
    # Positive momentum can increase fragility when leverage/commitments are also high.
    return normalize(return_1y, -0.20, 0.40)


def drawdown_score(max_drawdown: float | None) -> float:
    if max_drawdown is None:
        return 0.0
    return normalize(-max_drawdown, 0.0, 0.50)


def company_risk_score(
    *,
    debt_to_assets: float | None,
    commitment_score: float,
    return_1y: float | None,
    max_drawdown: float | None,
    leverage_weight: float,
    commitment_weight: float,
    market_heat_weight: float,
    drawdown_weight: float,
) -> float:
    total_weight = (
        leverage_weight
        + commitment_weight
        + market_heat_weight
        + drawdown_weight
    )
    if total_weight <= 0:
        return 0.0

    score = (
        leverage_score(debt_to_assets) * leverage_weight
        + clamp(commitment_score) * commitment_weight
        + market_heat_score(return_1y) * market_heat_weight
        + drawdown_score(max_drawdown) * drawdown_weight
    ) / total_weight
    return round(clamp(score), 2)


def wealth_at_risk(market_cap: float | None, decline: float) -> float | None:
    if market_cap is None:
        return None
    return market_cap * decline
