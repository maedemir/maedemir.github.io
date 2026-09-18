from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta

from spatial_omics_litdb.classify import in_scope
from spatial_omics_litdb.config import Settings
from spatial_omics_litdb.ingest import RawRecord, normalize_doi, parse_date
from spatial_omics_litdb.ingest.http import HttpClient


def _to_record(item: dict, server: str) -> RawRecord | None:
    title = (item.get("title") or "").strip()
    abstract = item.get("abstract")
    if not title or not in_scope(title, abstract):
        return None
    doi = normalize_doi(item.get("doi"))
    authors = []
    raw_authors = item.get("authors") or ""
    if isinstance(raw_authors, str):
        authors = [part.strip() for part in raw_authors.split(";") if part.strip()]
    elif isinstance(raw_authors, list):
        authors = [str(a) for a in raw_authors]
    published = parse_date(item.get("date"))
    landing = f"https://www.{server}.org/content/{doi}v{item.get('version', '1')}" if doi else None
    pdf_url = f"https://www.{server}.org/content/{doi}v{item.get('version', '1')}.full.pdf" if doi else None
    return RawRecord(
        source=server,
        source_id=doi,
        doi=doi,
        title=title,
        abstract=abstract,
        authors=authors,
        venue=f"{server} preprint",
        year=published.year if published else None,
        published_date=published,
        is_preprint=True,
        record_type="preprint",
        is_oa=True,
        oa_status="green",
        pdf_url=pdf_url,
        landing_url=landing,
        license=item.get("license"),
    )


def fetch_preprints(
    client: HttpClient,
    settings: Settings,
    days: int | None = None,
    max_pages: int = 40,
) -> Iterator[RawRecord]:
    end = date.today()
    start = date.fromisoformat(settings.start_date)
    if days is not None:
        start = max(start, end - timedelta(days=days))
    if start > end:
        return
    seen: set[str] = set()
    for server in ("biorxiv", "medrxiv"):
        cursor = 0
        pages = 0
        while pages < max_pages:
            payload = client.get_json(
                f"https://api.{server}.org/details/{server}/{start.isoformat()}/{end.isoformat()}/{cursor}",
                pause=0.3,
            )
            collection = payload.get("collection") or []
            if not collection:
                break
            for item in collection:
                record = _to_record(item, server)
                if not record:
                    continue
                uid = record.uid()
                if uid in seen:
                    continue
                seen.add(uid)
                yield record
            cursor += len(collection)
            pages += 1
            if len(collection) < 100:
                break
