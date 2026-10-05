# src/ai_debt_bubble_analysis/sources/sec.py
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any

import httpx

from ..models import FilingEvidence


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data.strip():
            self.parts.append(data)


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


WATCH_TERMS = (
    "purchase obligations",
    "unconditional purchase",
    "minimum lease payments",
    "operating lease",
    "finance lease",
    "residual value guarantee",
    "residual value support",
    "variable interest entity",
    "special purpose vehicle",
    "special-purpose vehicle",
    "joint venture",
    "capacity agreement",
    "take-or-pay",
    "data center",
    "data centre",
    "commitment",
    "guarantee",
)


@dataclass(slots=True)
class Financials:
    assets: float | None
    liabilities: float | None
    debt: float | None
    equity: float | None
    revenue: float | None
    capex: float | None
    shares_outstanding: float | None


def _latest_fact(
    companyfacts: dict[str, Any],
    taxonomy: str,
    tags: tuple[str, ...],
    unit: str,
    *,
    annual_only: bool = False,
) -> float | None:
    facts = companyfacts.get("facts", {}).get(taxonomy, {})
    candidates: list[tuple[int, str, float]] = []

    for tag in tags:
        entries = facts.get(tag, {}).get("units", {}).get(unit, [])
        for entry in entries:
            form = entry.get("form")
            if form not in {"10-K", "10-Q"}:
                continue
            if annual_only and form != "10-K":
                continue
            end = entry.get("end", "")
            value = entry.get("val")
            if value is None:
                continue
            try:
                form_priority = 1 if form == "10-K" else 0
                candidates.append((form_priority, end, float(value)))
            except (TypeError, ValueError):
                continue

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[-1][2]


def extract_financials(companyfacts: dict[str, Any]) -> Financials:
    assets = _latest_fact(companyfacts, "us-gaap", ("Assets",), "USD")
    liabilities = _latest_fact(companyfacts, "us-gaap", ("Liabilities",), "USD")
    equity = _latest_fact(
        companyfacts,
        "us-gaap",
        (
            "StockholdersEquity",
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        ),
        "USD",
    )
    revenue = _latest_fact(
        companyfacts,
        "us-gaap",
        ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"),
        "USD",
        annual_only=True,
    )
    capex = _latest_fact(
        companyfacts,
        "us-gaap",
        ("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"),
        "USD",
        annual_only=True,
    )

    debt_parts = [
        _latest_fact(companyfacts, "us-gaap", (tag,), "USD")
        for tag in (
            "DebtCurrent",
            "LongTermDebtCurrent",
            "ShortTermBorrowings",
            "LongTermDebtNoncurrent",
        )
    ]
    debt_values = [value for value in debt_parts if value is not None]
    debt = sum(debt_values) if debt_values else None

    shares = _latest_fact(
        companyfacts,
        "dei",
        ("EntityCommonStockSharesOutstanding",),
        "shares",
    )

    return Financials(
        assets=assets,
        liabilities=liabilities,
        debt=debt,
        equity=equity,
        revenue=revenue,
        capex=capex,
        shares_outstanding=shares,
    )


def _money_candidates(text: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"(?P<currency>US\$|\$|USD)\s*"
        r"(?P<value>[0-9][0-9,]*(?:\.[0-9]+)?)\s*"
        r"(?P<scale>trillion|billion|million)?",
        re.IGNORECASE,
    )
    scale_map = {"trillion": 1e12, "billion": 1e9, "million": 1e6}
    out: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        raw_value = float(match.group("value").replace(",", ""))
        scale = match.group("scale")
        value = raw_value * scale_map.get(scale.lower(), 1.0) if scale else raw_value
        out.append(
            {"value": value, "display": match.group(0), "offset": match.start()}
        )
        if len(out) >= 30:
            break
    return out


def scan_filing_text(text: str, *, max_snippets: int = 12) -> FilingEvidence:
    normalized = re.sub(r"\s+", " ", text)
    lower = normalized.lower()
    snippets: list[str] = []
    money: list[dict[str, Any]] = []
    matched_terms: set[str] = set()
    mentions = 0

    for term in WATCH_TERMS:
        start = 0
        while True:
            idx = lower.find(term, start)
            if idx < 0:
                break
            mentions += 1
            matched_terms.add(term)
            if len(snippets) < max_snippets:
                left = max(0, idx - 300)
                right = min(len(normalized), idx + len(term) + 500)
                snippet = normalized[left:right].strip()
                if snippet not in snippets:
                    snippets.append(snippet)
                    money.extend(_money_candidates(snippet))
            start = idx + len(term)

    distinct = len(matched_terms)
    score = min(100.0, distinct * 8.0 + min(mentions, 20) * 2.5)

    seen: set[tuple[float, str]] = set()
    money_unique: list[dict[str, Any]] = []
    for item in money:
        key = (float(item["value"]), str(item["display"]))
        if key not in seen:
            seen.add(key)
            money_unique.append(item)

    return FilingEvidence(
        form="10-K",
        filed_at=None,
        url=None,
        score=round(score, 2),
        mentions=mentions,
        snippets=snippets,
        money_candidates=money_unique[:30],
    )


class SECClient:
    def __init__(self, user_agent: str) -> None:
        self._sem = asyncio.Semaphore(4)
        self._client = httpx.AsyncClient(
            base_url="https://data.sec.gov",
            headers={
                "User-Agent": user_agent,
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            },
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_connections=8, max_keepalive_connections=4),
            follow_redirects=True,
        )
        self._archive = httpx.AsyncClient(
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate",
            },
            timeout=httpx.Timeout(45.0, connect=10.0),
            limits=httpx.Limits(max_connections=4, max_keepalive_connections=2),
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self._client.aclose()
        await self._archive.aclose()

    async def companyfacts(self, cik: str) -> dict[str, Any]:
        async with self._sem:
            response = await self._client.get(f"/api/xbrl/companyfacts/CIK{cik}.json")
        response.raise_for_status()
        return response.json()

    async def submissions(self, cik: str) -> dict[str, Any]:
        async with self._sem:
            response = await self._client.get(f"/submissions/CIK{cik}.json")
        response.raise_for_status()
        return response.json()

    async def latest_10k(self, cik: str) -> tuple[str, str, str, str] | None:
        data = await self.submissions(cik)
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accessions = recent.get("accessionNumber", [])
        docs = recent.get("primaryDocument", [])
        filed = recent.get("filingDate", [])

        for i, form in enumerate(forms):
            if form == "10-K":
                accession = accessions[i]
                document = docs[i]
                filed_at = filed[i] if i < len(filed) else ""
                numeric_cik = str(int(cik))
                archive_path = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{numeric_cik}/{accession.replace('-', '')}/{document}"
                )
                return form, filed_at, archive_path, document
        return None

    async def filing_evidence(self, cik: str) -> FilingEvidence:
        latest = await self.latest_10k(cik)
        if latest is None:
            return FilingEvidence("10-K", None, None, 0.0, 0, [], [])

        form, filed_at, url, _ = latest
        async with self._sem:
            response = await self._archive.get(url)
        response.raise_for_status()
        text = html_to_text(response.text)
        evidence = scan_filing_text(text)
        evidence.form = form
        evidence.filed_at = filed_at
        evidence.url = url
        return evidence
