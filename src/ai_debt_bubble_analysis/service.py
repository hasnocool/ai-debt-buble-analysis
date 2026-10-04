# src/ai_debt_bubble_analysis/service.py
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from .config import AppConfig, CompanyConfig
from .models import (
    CompanySnapshot,
    FilingEvidence,
    MacroSnapshot,
    OverviewSnapshot,
)
from .scoring import clamp, company_risk_score
from .sources.fred import FredClient
from .sources.market import MarketClient, PriceHistory
from .sources.sec import Financials, SECClient
from .store import SnapshotStore


class AnalysisEngine:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.sec = SECClient(config.sec_user_agent)
        self.market = MarketClient()
        self.fred = FredClient()
        self.store = SnapshotStore(config.db_path)
        self._overview: OverviewSnapshot | None = None
        self._refresh_lock = asyncio.Lock()
        self._last_refresh: datetime | None = None

    async def initialize(self) -> None:
        await self.store.initialize()

    async def close(self) -> None:
        await asyncio.gather(
            self.sec.close(),
            self.market.close(),
            self.fred.close(),
        )

    async def refresh(self, force: bool = False) -> OverviewSnapshot:
        now = datetime.now(UTC)
        if (
            not force
            and self._overview is not None
            and self._last_refresh is not None
            and now - self._last_refresh
            < timedelta(seconds=self.config.cache_ttl_seconds)
        ):
            return self._overview

        async with self._refresh_lock:
            now = datetime.now(UTC)
            if (
                not force
                and self._overview is not None
                and self._last_refresh is not None
                and now - self._last_refresh
                < timedelta(seconds=self.config.cache_ttl_seconds)
            ):
                return self._overview

            company_results = await asyncio.gather(
                *(self._load_company(company) for company in self.config.companies)
            )
            macro = await self._load_macro()

            market_caps = [
                company.ai_weighted_market_cap
                for company in company_results
                if company.ai_weighted_market_cap is not None
            ]
            total_market_cap = sum(market_caps)
            sorted_caps = sorted(market_caps, reverse=True)
            top1 = (
                sorted_caps[0] / total_market_cap * 100.0
                if total_market_cap > 0 and sorted_caps
                else 0.0
            )
            shares = [
                cap / total_market_cap for cap in market_caps
            ] if total_market_cap > 0 else []
            hhi = sum(value * value for value in shares) * 10000.0

            alerts = self._build_alerts(company_results, macro, top1)

            overview = OverviewSnapshot(
                generated_at=now.isoformat(),
                monitored_companies=len(company_results),
                monitored_market_cap=round(total_market_cap, 2),
                top1_concentration_pct=round(top1, 2),
                hhi=round(hhi, 2),
                wealth_at_10=round(total_market_cap * 0.10, 2),
                wealth_at_20=round(total_market_cap * 0.20, 2),
                wealth_at_30=round(total_market_cap * 0.30, 2),
                macro=macro,
                companies=sorted(
                    company_results,
                    key=lambda company: (
                        company.risk_score,
                        company.ai_weighted_market_cap or 0.0,
                    ),
                    reverse=True,
                ),
                alerts=alerts,
            )

            self._overview = overview
            self._last_refresh = now
            await self.store.save(overview.to_dict())
            return overview

    async def history(self, limit: int = 120) -> list[dict[str, Any]]:
        return await self.store.recent(limit=limit)

    async def _load_company(self, company: CompanyConfig) -> CompanySnapshot:
        financial_result, evidence_result, market_result = await asyncio.gather(
            self._safe_companyfacts(company),
            self._safe_evidence(company),
            self._safe_market(company),
        )

        debt_to_assets = (
            financial_result.debt / financial_result.assets
            if financial_result.debt is not None and financial_result.assets
            and financial_result.assets > 0
            else None
        )
        risk = company_risk_score(
            debt_to_assets=debt_to_assets,
            commitment_score=evidence_result.score,
            return_1y=market_result.return_1y,
            max_drawdown=market_result.max_drawdown,
            leverage_weight=self.config.reported_leverage_weight,
            commitment_weight=self.config.commitment_pressure_weight,
            market_heat_weight=self.config.market_heat_weight,
            drawdown_weight=self.config.drawdown_weight,
        )

        market_cap = (
            financial_result.shares_outstanding * market_result.latest
            if financial_result.shares_outstanding is not None
            and market_result.latest is not None
            else None
        )
        ai_weighted_market_cap = (
            market_cap * company.ai_exposure if market_cap is not None else None
        )

        return CompanySnapshot(
            ticker=company.ticker,
            name=company.name,
            sector=company.sector,
            ai_exposure=company.ai_exposure,
            market_cap=market_cap,
            shares_outstanding=financial_result.shares_outstanding,
            ai_weighted_market_cap=ai_weighted_market_cap,
            assets=financial_result.assets,
            liabilities=financial_result.liabilities,
            debt=financial_result.debt,
            equity=financial_result.equity,
            revenue=financial_result.revenue,
            capex=financial_result.capex,
            debt_to_assets=debt_to_assets,
            commitment_score=evidence_result.score,
            commitment_mentions=evidence_result.mentions,
            return_1y=market_result.return_1y,
            max_drawdown=market_result.max_drawdown,
            risk_score=risk,
            wealth_at_10=(market_cap * 0.10 if market_cap is not None else None),
            wealth_at_20=(market_cap * 0.20 if market_cap is not None else None),
            wealth_at_30=(market_cap * 0.30 if market_cap is not None else None),
            filing=evidence_result,
        )

    async def _safe_companyfacts(self, company: CompanyConfig) -> Financials:
        try:
            facts = await self.sec.companyfacts(company.cik)
            from .sources.sec import extract_financials
            return extract_financials(facts)
        except Exception:
            return Financials(None, None, None, None, None, None, None)

    async def _safe_evidence(self, company: CompanyConfig) -> FilingEvidence:
        try:
            return await self.sec.filing_evidence(company.cik)
        except Exception:
            return FilingEvidence("10-K", None, None, 0.0, 0, [], [])

    async def _safe_market(self, company: CompanyConfig) -> PriceHistory:
        try:
            return await self.market.history(company.ticker)
        except Exception:
            return PriceHistory([])

    async def _load_macro(self) -> MacroSnapshot:
        results = await asyncio.gather(
            *(self._safe_fred(series_id) for series_id in self.config.fred_series)
        )
        series = {
            series_id: result
            for series_id, result in zip(self.config.fred_series, results)
        }
        stress_inputs = []
        for series_id in ("VIXCLS", "BAMLH0A0HYM2", "STLFSI4"):
            z_score = series.get(series_id, {}).get("z_score")
            if z_score is not None:
                stress_inputs.append(max(-2.0, min(3.0, float(z_score))))
        stress_score = (
            clamp(50.0 + sum(stress_inputs) / max(len(stress_inputs), 1) * 14.0)
            if stress_inputs
            else 0.0
        )
        return MacroSnapshot(series=series, stress_score=round(stress_score, 2))

    async def _safe_fred(self, series_id: str) -> dict[str, float | None]:
        try:
            return await self.fred.series(series_id)
        except Exception:
            return {
                "latest": None,
                "one_year_change": None,
                "z_score": None,
                "observations": 0,
            }

    def _build_alerts(
        self,
        companies: list[CompanySnapshot],
        macro: MacroSnapshot,
        top1: float,
    ) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []

        if top1 >= self.config.concentration_top1_pct:
            alerts.append(
                {
                    "severity": "high",
                    "type": "concentration",
                    "title": "Single-name wealth concentration is elevated",
                    "detail": f"Top monitored company represents {top1:.1f}% of AI-weighted monitored market value.",
                }
            )

        if macro.stress_score >= 65.0:
            alerts.append(
                {
                    "severity": "high",
                    "type": "macro",
                    "title": "Macro / credit stress is elevated",
                    "detail": f"Composite stress score is {macro.stress_score:.1f}/100.",
                }
            )

        for company in companies:
            if company.risk_score >= self.config.high_risk_score:
                alerts.append(
                    {
                        "severity": "high",
                        "type": "company",
                        "ticker": company.ticker,
                        "title": f"{company.ticker} has a high composite risk signal",
                        "detail": (
                            f"Risk {company.risk_score:.1f}; commitment evidence "
                            f"{company.commitment_score:.1f}; drawdown "
                            f"{(company.max_drawdown or 0.0) * 100:.1f}%."
                        ),
                    }
                )
            if (
                company.max_drawdown is not None
                and company.max_drawdown * 100.0 <= self.config.large_drawdown_pct
            ):
                alerts.append(
                    {
                        "severity": "medium",
                        "type": "drawdown",
                        "ticker": company.ticker,
                        "title": f"{company.ticker} has a large observed drawdown",
                        "detail": f"Maximum one-year drawdown is {company.max_drawdown * 100:.1f}%.",
                    }
                )
            if company.commitment_score >= self.config.commitment_evidence_threshold:
                alerts.append(
                    {
                        "severity": "medium",
                        "type": "filing",
                        "ticker": company.ticker,
                        "title": f"{company.ticker} filing contains dense commitment evidence",
                        "detail": (
                            f"{company.commitment_mentions} watch-term mentions across "
                            "the latest 10-K text."
                        ),
                    }
                )
        return alerts[:30]
