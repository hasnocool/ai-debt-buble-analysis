# src/ai_debt_bubble_analysis/sources/market.py
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx


@dataclass(slots=True)
class PriceHistory:
    close: list[float]

    @property
    def latest(self) -> float | None:
        return self.close[-1] if self.close else None

    @property
    def return_1y(self) -> float | None:
        if len(self.close) < 2:
            return None
        return self.close[-1] / self.close[0] - 1.0

    @property
    def max_drawdown(self) -> float | None:
        if not self.close:
            return None
        peak = self.close[0]
        max_drawdown = 0.0
        for value in self.close:
            peak = max(peak, value)
            max_drawdown = min(max_drawdown, value / peak - 1.0)
        return max_drawdown


class MarketClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            headers={"User-Agent": "ai-debt-bubble-analysis/0.1"},
            timeout=httpx.Timeout(20.0, connect=8.0),
            limits=httpx.Limits(max_connections=12, max_keepalive_connections=6),
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def yahoo(self, ticker: str) -> PriceHistory:
        response = await self._client.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
            params={"range": "1y", "interval": "1d", "events": "history"},
        )
        response.raise_for_status()
        payload = response.json()
        result = payload["chart"]["result"][0]
        closes = [
            float(value)
            for value in result["indicators"]["quote"][0]["close"]
            if value is not None
        ]
        return PriceHistory(closes)

    async def stooq(self, ticker: str) -> PriceHistory:
        response = await self._client.get(
            "https://stooq.com/q/d/l/",
            params={"s": f"{ticker.lower()}.us", "i": "d"},
        )
        response.raise_for_status()
        rows = csv.DictReader(io.StringIO(response.text))
        cutoff = datetime.now(UTC) - timedelta(days=370)
        closes: list[float] = []
        for row in rows:
            try:
                date = datetime.fromisoformat(row["Date"]).replace(tzinfo=UTC)
                close = float(row["Close"])
            except (KeyError, ValueError, TypeError):
                continue
            if date >= cutoff:
                closes.append(close)
        return PriceHistory(closes)

    async def history(self, ticker: str) -> PriceHistory:
        try:
            return await self.yahoo(ticker)
        except (httpx.HTTPError, KeyError, IndexError, ValueError):
            return await self.stooq(ticker)
