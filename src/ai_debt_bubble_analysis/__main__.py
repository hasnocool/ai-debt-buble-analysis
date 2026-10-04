# src/ai_debt_bubble_analysis/__main__.py
from __future__ import annotations

import argparse
import asyncio
import json

from .app import app
from .config import load_config
from .service import AnalysisEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aidba",
        description="Monitor AI infrastructure wealth, leverage and shadow obligations.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="Run the web dashboard.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    subparsers.add_parser("refresh", help="Fetch a fresh snapshot and print JSON.")

    export = subparsers.add_parser("export", help="Fetch a fresh snapshot and write JSON.")
    export.add_argument("--output", default="snapshot.json")

    return parser


async def _refresh() -> dict:
    engine = AnalysisEngine(load_config())
    await engine.initialize()
    try:
        return (await engine.refresh(force=True)).to_dict()
    finally:
        await engine.close()


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "serve":
        import uvicorn

        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            workers=1,
            log_level="info",
        )
        return

    payload = asyncio.run(_refresh())
    if args.command == "refresh":
        print(json.dumps(payload, indent=2))
    else:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        print(f"wrote {args.output}")
