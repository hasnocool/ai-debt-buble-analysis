# tests/test_scoring.py
from ai_debt_bubble_analysis.scoring import (
    company_risk_score,
    leverage_score,
    market_heat_score,
    wealth_at_risk,
)


def test_leverage_score_is_bounded():
    assert leverage_score(None) == 0
    assert leverage_score(0.0) == 0
    assert leverage_score(0.60) == 100
    assert leverage_score(2.0) == 100


def test_market_heat_and_wealth_math():
    assert market_heat_score(-0.20) == 0
    assert market_heat_score(0.40) == 100
    assert wealth_at_risk(1_000_000_000, 0.20) == 200_000_000


def test_composite_score():
    score = company_risk_score(
        debt_to_assets=0.60,
        commitment_score=100,
        return_1y=0.40,
        max_drawdown=-0.50,
        leverage_weight=0.30,
        commitment_weight=0.30,
        market_heat_weight=0.20,
        drawdown_weight=0.20,
    )
    assert score == 100
