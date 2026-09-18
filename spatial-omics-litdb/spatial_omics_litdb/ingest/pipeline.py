from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from spatial_omics_litdb.classify import classify
from spatial_omics_litdb.config import Settings
from spatial_omics_litdb.ingest import RawRecord, normalize_doi
from spatial_omics_litdb.ingest.http import HttpClient
from spatial_omics_litdb.ingest.openalex import fetch_openalex
from spatial_omics_litdb.ingest.pdfs import download_oa_pdf
from spatial_omics_litdb.ingest.preprints import fetch_preprints
from spatial_omics_litdb.ingest.pubmed import fetch_pubmed
from spatial_omics_litdb.ingest.unpaywall import lookup_unpaywall
from spatial_omics_litdb.models import IngestRun, Paper


def _merge_authors(existing: list, incoming: list[str]) -> list:
    if len(incoming) > len(existing or []):
        return incoming
    return existing or incoming


def _search_text(paper: Paper) -> str:
    platforms = " ".join(paper.platforms or [])
    authors = " ".join(paper.authors or [])
    return " ".join(
        part
        for part in (
            paper.title,
            paper.abstract or "",
            paper.venue or "",
            authors,
            platforms,
            paper.organism or "",
            paper.tissue or "",
            paper.disease_or_system or "",
            paper.modality,
            paper.study_type,
        )
        if part
    ).lower()


def upsert_record(db: Session, record: RawRecord, settings: Settings, client: HttpClient, download_pdfs: bool) -> tuple[Paper, bool]:
    uid = record.uid()
    paper = db.execute(select(Paper).where(Paper.uid == uid)).scalar_one_or_none()
    created = paper is None
    if paper is None:
        paper = Paper(uid=uid, title=record.title)
        db.add(paper)

    paper.doi = paper.doi or normalize_doi(record.doi)
    paper.pmid = paper.pmid or record.pmid
    paper.pmcid = paper.pmcid or record.pmcid
    paper.openalex_id = paper.openalex_id or record.openalex_id
    paper.title = record.title or paper.title
    if record.abstract and (not paper.abstract or len(record.abstract) > len(paper.abstract or "")):
        paper.abstract = record.abstract
    paper.authors = _merge_authors(paper.authors or [], record.authors)
    paper.venue = record.venue or paper.venue
    paper.year = record.year or paper.year
    paper.published_date = record.published_date or paper.published_date
    paper.is_preprint = paper.is_preprint or record.is_preprint
    if record.record_type != "other" or not paper.record_type:
        paper.record_type = "preprint" if paper.is_preprint else record.record_type
    if record.landing_url:
        paper.landing_url = paper.landing_url or record.landing_url
    if record.license:
        paper.license = paper.license or record.license

    sources = list(paper.sources or [])
    if record.source not in sources:
        sources.append(record.source)
    paper.sources = sources

    oa_info = {}
    if paper.doi and (record.is_oa is None or not record.pdf_url):
        oa_info = lookup_unpaywall(client, paper.doi, settings)
    if oa_info:
        paper.is_oa = bool(oa_info.get("is_oa") or record.is_oa)
        paper.oa_status = oa_info.get("oa_status") or record.oa_status
        paper.pdf_url = oa_info.get("pdf_url") or record.pdf_url
        paper.license = oa_info.get("license") or paper.license
    else:
        if record.is_oa is not None:
            paper.is_oa = bool(record.is_oa) or paper.is_oa
        paper.oa_status = record.oa_status or paper.oa_status
        if record.is_oa and record.pdf_url:
            paper.pdf_url = record.pdf_url

    # Paywalled items stay metadata-only. Never fetch non-OA PDFs.
    if paper.is_oa and paper.pdf_url and download_pdfs and paper.doi:
        path = download_oa_pdf(client, paper.pdf_url, paper.doi, settings)
        if path:
            paper.pdf_path = str(path)
            paper.full_text_available = True
    paper.access_needed = not bool(paper.is_oa and (paper.pdf_url or paper.full_text_available))

    tagged = classify(paper.title, paper.abstract)
    paper.modality = tagged.modality
    paper.platforms = tagged.platforms
    paper.resolution = tagged.resolution
    paper.organism = tagged.organism
    paper.tissue = tagged.tissue
    paper.disease_or_system = tagged.disease_or_system
    paper.study_type = tagged.study_type
    paper.data_availability = tagged.data_availability
    paper.code_availability = tagged.code_availability
    if not paper.enriched_at:
        paper.impactful_experiments = tagged.impactful_experiments
        paper.novel_approaches = tagged.novel_approaches
        paper.why_it_matters = tagged.why_it_matters
    paper.search_text = _search_text(paper)
    paper.updated_at = datetime.now(UTC)
    return paper, created


def run_ingest(
    db: Session,
    settings: Settings,
    sources: tuple[str, ...] = ("openalex", "pubmed", "preprints"),
    download_pdfs: bool = True,
    preprint_days: int | None = None,
) -> IngestRun:
    run = IngestRun(status="running", source_filter=",".join(sources))
    db.add(run)
    db.commit()
    client = HttpClient(settings)
    seen = 0
    upserted = 0
    pdfs = 0
    try:
        streams = []
        if "openalex" in sources:
            streams.append(fetch_openalex(client, settings))
        if "pubmed" in sources:
            streams.append(fetch_pubmed(client, settings))
        if "preprints" in sources or "biorxiv" in sources or "medrxiv" in sources:
            streams.append(fetch_preprints(client, settings, days=preprint_days))
        for stream in streams:
            for record in stream:
                seen += 1
                paper, _created = upsert_record(db, record, settings, client, download_pdfs)
                upserted += 1
                if paper.full_text_available:
                    pdfs += 1
                if seen % 25 == 0:
                    db.commit()
        run.status = "ok"
    except Exception as exc:  # noqa: BLE001
        run.status = "error"
        run.error = str(exc)
        db.commit()
        raise
    finally:
        client.close()
        run.finished_at = datetime.now(UTC)
        run.records_seen = seen
        run.records_upserted = upserted
        run.pdfs_downloaded = pdfs
        db.commit()
    return run
