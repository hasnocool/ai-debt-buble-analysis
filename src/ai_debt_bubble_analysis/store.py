# src/ai_debt_bubble_analysis/store.py
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite


class SnapshotStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    async def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    generated_at TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            await db.commit()

    async def save(self, payload: dict[str, Any]) -> None:
        generated_at = payload["generated_at"]
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO snapshots(generated_at, payload) VALUES(?, ?)",
                (generated_at, json.dumps(payload, separators=(",", ":"))),
            )
            await db.commit()

    async def recent(self, limit: int = 120) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT generated_at, payload FROM snapshots "
                "ORDER BY generated_at DESC LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
            await cursor.close()

        return [
            {"generated_at": generated_at, "payload": json.loads(payload)}
            for generated_at, payload in reversed(rows)
        ]
