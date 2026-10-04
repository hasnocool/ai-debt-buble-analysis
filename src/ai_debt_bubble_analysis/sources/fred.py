# src/ai_debt_bubble_analysis/sources/fred.py
from __future__ import annotations

import csv
import io
from datetime import UTC, datetime, timedelta
from statistics import mean, pstdev

import httpx


class FredClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            headers={"User-Agent": "ai-debt-bubble-analysis/0.1"},
            timeout=httpx.Timeout(20.0, connect=8.0),
            limits=httpx.Limits(max_connections=8, max_keepalive_connections=4),
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def series(self, series_id: str, lookback_days: int = 730) -> dict[str, float | None]:
        start = (datetime.now(UTC) - timedelta(days=lookback_days)).date().isoformat()
        response = await self._client.get(
            "https://fred.stlouisfed.org/graph/fredgraph.csv",
            params={"id": series_id, "cosd": start},
        )
        response.raise_for_status()

        values: list[float] = []
        for row in csv.DictReader(io.StringIO(response.text)):
            raw = row.get(series_id)
            if raw in (None, "", "."):
                continue
            try:
                values.append(float(raw))
            except ValueError:
                continue

        if not values:
            return {
                "latest": None,
                "one_year_change": None,
                "z_score": None,
                "observations": 0,
            }

        latest = values[-1]
        one_year_change = latest - values[0] if len(values) > 1 else None
        sigma = pstdev(values) if len(values) > 1 else 0.0
        z_score = (latest - mean(values)) / sigma if sigma > 0 else 0.0

        return {
            "latest": round(latest, 6),
            "one_year_change": round(one_year_change, 6) if one_year_change is not None else None,
            "z_score": round(z_score, 4),
            "observations": len(values),
        }
