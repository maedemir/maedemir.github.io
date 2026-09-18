from __future__ import annotations

import argparse
import sys

import uvicorn

from spatial_omics_litdb.config import get_settings
from spatial_omics_litdb.db import init_db, make_engine, session_factory
from spatial_omics_litdb.ingest.pipeline import run_ingest
from spatial_omics_litdb.seed import seed_demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="spatial-omics-litdb")
    sub = parser.add_subparsers(dest="cmd", required=True)

    serve = sub.add_parser("serve", help="Run the dashboard")
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)

    ingest = sub.add_parser("ingest", help="Discover and upsert papers")
    ingest.add_argument(
        "--source",
        action="append",
        dest="sources",
        choices=["openalex", "pubmed", "preprints"],
        help="Repeatable. Default: all three sources.",
    )
    ingest.add_argument("--no-pdfs", action="store_true", help="Metadata only; skip OA PDF download")
    ingest.add_argument(
        "--preprint-days",
        type=int,
        default=None,
        help="Limit bioRxiv/medRxiv scan to the last N days (nightly). Full backfill if omitted.",
    )

    seed = sub.add_parser("seed", help="Load demo records (no API key required)")
    seed.add_argument("--reset", action="store_true")

    args = parser.parse_args(argv)
    settings = get_settings()
    engine = make_engine(settings)
    init_db(engine)
    factory = session_factory(engine)

    if args.cmd == "serve":
        uvicorn.run(
            "spatial_omics_litdb.main:app",
            host=args.host or settings.host,
            port=args.port or settings.port,
            reload=False,
        )
        return 0

    db = factory()
    try:
        if args.cmd == "seed":
            n = seed_demo(db, reset=args.reset)
            print(f"Seeded {n} demo papers into {settings.database_url}")
            return 0
        if args.cmd == "ingest":
            sources = tuple(args.sources) if args.sources else ("openalex", "pubmed", "preprints")
            run = run_ingest(
                db,
                settings,
                sources=sources,
                download_pdfs=not args.no_pdfs,
                preprint_days=args.preprint_days,
            )
            print(
                f"Ingest {run.status}: seen={run.records_seen} "
                f"upserted={run.records_upserted} pdfs={run.pdfs_downloaded}"
            )
            if run.error:
                print(run.error, file=sys.stderr)
                return 1
            return 0
    finally:
        db.close()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
