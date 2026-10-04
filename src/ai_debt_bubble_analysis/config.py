# src/ai_debt_bubble_analysis/config.py
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CompanyConfig:
    ticker: str
    name: str
    cik: str
    sector: str
    ai_exposure: float


@dataclass(frozen=True, slots=True)
class AppConfig:
    companies: tuple[CompanyConfig, ...]
    fred_series: tuple[str, ...]
    reported_leverage_weight: float
    commitment_pressure_weight: float
    market_heat_weight: float
    drawdown_weight: float
    concentration_top1_pct: float
    high_risk_score: float
    large_drawdown_pct: float
    credit_stress_z: float
    commitment_evidence_threshold: float
    sec_user_agent: str
    db_path: Path
    cache_ttl_seconds: int


def load_config(path: str | Path | None = None) -> AppConfig:
    config_path = Path(path or os.getenv("AIDBA_CONFIG", "config/universe.toml"))
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    companies = tuple(
        CompanyConfig(
            ticker=item["ticker"].upper(),
            name=item["name"],
            cik=str(item["cik"]).zfill(10),
            sector=item["sector"],
            ai_exposure=float(item.get("ai_exposure", 1.0)),
        )
        for item in raw["companies"]
    )

    scoring = raw.get("scoring", {})
    alerts = raw.get("alerts", {})

    return AppConfig(
        companies=companies,
        fred_series=tuple(raw.get("fred", {}).get("series", [])),
        reported_leverage_weight=float(scoring.get("reported_leverage_weight", 0.30)),
        commitment_pressure_weight=float(scoring.get("commitment_pressure_weight", 0.30)),
        market_heat_weight=float(scoring.get("market_heat_weight", 0.20)),
        drawdown_weight=float(scoring.get("drawdown_weight", 0.20)),
        concentration_top1_pct=float(alerts.get("concentration_top1_pct", 35.0)),
        high_risk_score=float(alerts.get("high_risk_score", 70.0)),
        large_drawdown_pct=float(alerts.get("large_drawdown_pct", -20.0)),
        credit_stress_z=float(alerts.get("credit_stress_z", 1.5)),
        commitment_evidence_threshold=float(
            alerts.get("commitment_evidence_threshold", 45.0)
        ),
        sec_user_agent=os.getenv(
            "SEC_USER_AGENT",
            "AI-Debt-Bubble-Analysis research contact: set SEC_USER_AGENT",
        ),
        db_path=Path(os.getenv("AIDBA_DB", "data/aibda.sqlite3")),
        cache_ttl_seconds=int(os.getenv("AIDBA_CACHE_TTL_SECONDS", "900")),
    )
