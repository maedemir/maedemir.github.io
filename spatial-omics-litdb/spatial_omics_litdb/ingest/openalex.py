from __future__ import annotations

from collections.abc import Iterator

from spatial_omics_litdb.classify import in_scope
from spatial_omics_litdb.config import Settings
from spatial_omics_litdb.ingest import RawRecord, normalize_doi, parse_date, reconstruct_inverted_abstract
from spatial_omics_litdb.ingest.http import HttpClient

OPENALEX_QUERIES = (
    "spatial transcriptomics",
    "spatial proteomics",
    "spatial multi-omics",
    "Visium HD",
    "MERFISH",
    "Xenium spatial",
    "CosMx spatial",
    "CODEX spatial",
    "imaging mass cytometry",
    "Stereo-seq",
    "MIBI spatial",
)


def _authors(work: dict) -> list[str]:
    names: list[str] = []
    for authorship in work.get("authorships") or []:
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            names.append(name)
    return names


def _record_from_work(work: dict) -> RawRecord | None:
    title = (work.get("display_name") or "").strip()
    if not title:
        return None
    abstract = reconstruct_inverted_abstract(work.get("abstract_inverted_index"))
    if not in_scope(title, abstract):
        return None
    loc = work.get("primary_location") or {}
    source = loc.get("source") or {}
    oa = work.get("open_access") or {}
    work_type = (work.get("type") or "").lower()
    venue = source.get("display_name")
    is_preprint = work_type == "preprint" or bool(
        venue and "rxiv" in venue.lower()
    )
    pdf_url = oa.get("oa_url") or loc.get("pdf_url")
    doi = normalize_doi(work.get("doi"))
    ids = work.get("ids") or {}
    pmid = None
    if ids.get("pmid"):
        pmid = str(ids["pmid"]).rsplit("/", 1)[-1]
    return RawRecord(
        source="openalex",
        source_id=work.get("id"),
        doi=doi,
        pmid=pmid,
        openalex_id=work.get("id"),
        title=title,
        abstract=abstract,
        authors=_authors(work),
        venue=venue,
        year=work.get("publication_year"),
        published_date=parse_date(work.get("publication_date")),
        is_preprint=is_preprint,
        record_type="preprint" if is_preprint else "journal",
        is_oa=bool(oa.get("is_oa")),
        oa_status=oa.get("oa_status"),
        pdf_url=pdf_url if oa.get("is_oa") else None,
        landing_url=loc.get("landing_page_url") or (f"https://doi.org/{doi}" if doi else work.get("id")),
        license=(loc.get("license")),
    )


def fetch_openalex(
    client: HttpClient,
    settings: Settings,
    per_query: int = 200,
    max_pages: int = 8,
) -> Iterator[RawRecord]:
    seen: set[str] = set()
    for query in OPENALEX_QUERIES:
        cursor = "*"
        pages = 0
        while cursor and pages < max_pages:
            payload = client.get_json(
                "https://api.openalex.org/works",
                params={
                    "filter": (
                        f"from_publication_date:{settings.start_date},"
                        f"title_and_abstract.search:{query}"
                    ),
                    "per_page": min(per_query, 200),
                    "cursor": cursor,
                    "mailto": settings.contact_email,
                },
            )
            for work in payload.get("results") or []:
                record = _record_from_work(work)
                if not record:
                    continue
                uid = record.uid()
                if uid in seen:
                    continue
                seen.add(uid)
                yield record
            cursor = (payload.get("meta") or {}).get("next_cursor")
            pages += 1
            if not payload.get("results"):
                break
