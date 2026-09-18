from __future__ import annotations

from collections.abc import Iterator

from lxml import etree

from spatial_omics_litdb.classify import in_scope
from spatial_omics_litdb.config import Settings
from spatial_omics_litdb.ingest import RawRecord, normalize_doi, parse_date
from spatial_omics_litdb.ingest.http import HttpClient

PUBMED_TERM = (
    '("spatial transcriptomics"[Title/Abstract] OR "spatial transcriptomic"[Title/Abstract] '
    'OR "spatial proteomics"[Title/Abstract] OR "spatial proteomic"[Title/Abstract] '
    'OR Visium[Title/Abstract] OR MERFISH[Title/Abstract] OR Xenium[Title/Abstract] '
    'OR CosMx[Title/Abstract] OR CODEX[Title/Abstract] OR "Stereo-seq"[Title/Abstract] '
    'OR "imaging mass cytometry"[Title/Abstract] OR MIBI[Title/Abstract] '
    'OR seqFISH[Title/Abstract] OR "Slide-seq"[Title/Abstract])'
)

NS = {"m": "https://www.ncbi.nlm.nih.gov"}


def _text(node, path: str) -> str | None:
    found = node.find(path)
    if found is None or found.text is None:
        return None
    return found.text.strip()


def _parse_article(article) -> RawRecord | None:
    pmid = _text(article, "MedlineCitation/PMID")
    article_node = article.find("MedlineCitation/Article")
    if article_node is None:
        return None
    title = _text(article_node, "ArticleTitle") or ""
    abstract_bits = [
        (node.text or "").strip()
        for node in article_node.findall("Abstract/AbstractText")
        if node.text
    ]
    abstract = " ".join(abstract_bits) or None
    if not title or not in_scope(title, abstract):
        return None
    authors: list[str] = []
    for author in article_node.findall("AuthorList/Author"):
        last = _text(author, "LastName")
        fore = _text(author, "ForeName")
        collective = _text(author, "CollectiveName")
        if last and fore:
            authors.append(f"{fore} {last}")
        elif last:
            authors.append(last)
        elif collective:
            authors.append(collective)
    journal = _text(article_node, "Journal/Title")
    year_text = _text(article_node, "Journal/JournalIssue/PubDate/Year")
    medline_date = _text(article_node, "Journal/JournalIssue/PubDate/MedlineDate")
    year = int(year_text) if year_text and year_text.isdigit() else None
    pub_date = parse_date(
        "-".join(
            part
            for part in (
                year_text,
                _text(article_node, "Journal/JournalIssue/PubDate/Month"),
                _text(article_node, "Journal/JournalIssue/PubDate/Day"),
            )
            if part
        )
        or medline_date
    )
    doi = None
    pmcid = None
    for aid in article.findall("PubmedData/ArticleIdList/ArticleId"):
        id_type = aid.get("IdType")
        if id_type == "doi" and aid.text:
            doi = normalize_doi(aid.text)
        elif id_type == "pmc" and aid.text:
            pmcid = aid.text.strip()
    pub_status = _text(article, "PubmedData/PublicationStatus") or ""
    is_preprint = "preprint" in pub_status.lower() or bool(
        journal and "rxiv" in journal.lower()
    )
    return RawRecord(
        source="pubmed",
        source_id=pmid,
        doi=doi,
        pmid=pmid,
        pmcid=pmcid,
        title=title,
        abstract=abstract,
        authors=authors,
        venue=journal,
        year=year or (pub_date.year if pub_date else None),
        published_date=pub_date,
        is_preprint=is_preprint,
        record_type="preprint" if is_preprint else "journal",
        landing_url=(
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None
        ),
    )


def fetch_pubmed(client: HttpClient, settings: Settings, retmax: int = 400) -> Iterator[RawRecord]:
    search = client.get_json(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={
            "db": "pubmed",
            "term": PUBMED_TERM,
            "retmode": "json",
            "retmax": retmax,
            "datetype": "pdat",
            "mindate": settings.start_date.replace("-", "/"),
            "maxdate": "3000",
            "email": settings.contact_email,
            "tool": "spatial_omics_litdb",
        },
        pause=0.4,
    )
    ids = ((search.get("esearchresult") or {}).get("idlist")) or []
    for i in range(0, len(ids), 50):
        batch = ",".join(ids[i : i + 50])
        xml_text = client.get_text(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={
                "db": "pubmed",
                "id": batch,
                "retmode": "xml",
                "email": settings.contact_email,
                "tool": "spatial_omics_litdb",
            },
            pause=0.4,
        )
        root = etree.fromstring(xml_text.encode("utf-8"))
        for article in root.findall("PubmedArticle"):
            record = _parse_article(article)
            if record:
                yield record
