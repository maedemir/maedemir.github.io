from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    value = doi.strip()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value, flags=re.I)
    value = value.strip().lower().rstrip(".")
    return value or None


def make_uid(doi: str | None, source: str, source_id: str | None, title: str) -> str:
    if doi:
        return f"doi:{normalize_doi(doi)}"
    if source_id:
        return f"{source}:{source_id}"
    digest = hashlib.sha256(title.strip().lower().encode("utf-8")).hexdigest()[:16]
    return f"title:{digest}"


def reconstruct_inverted_abstract(index: dict[str, list[int]] | None) -> str | None:
    if not index:
        return None
    positions: dict[int, str] = {}
    for word, idxs in index.items():
        for idx in idxs:
            positions[idx] = word
    if not positions:
        return None
    return " ".join(positions[i] for i in sorted(positions))


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m"):
        try:
            parsed = datetime.strptime(value if fmt != "%Y-%m" else value[:7], fmt)
            return parsed.date()
        except ValueError:
            continue
    if re.fullmatch(r"\d{4}", value[:4] or ""):
        try:
            return date(int(value[:4]), 1, 1)
        except ValueError:
            return None
    return None


@dataclass
class RawRecord:
    source: str
    source_id: str | None
    doi: str | None
    pmid: str | None = None
    pmcid: str | None = None
    openalex_id: str | None = None
    title: str = ""
    abstract: str | None = None
    authors: list[str] = field(default_factory=list)
    venue: str | None = None
    year: int | None = None
    published_date: date | None = None
    is_preprint: bool = False
    record_type: str = "other"
    is_oa: bool | None = None
    oa_status: str | None = None
    pdf_url: str | None = None
    landing_url: str | None = None
    license: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def uid(self) -> str:
        return make_uid(self.doi, self.source, self.source_id, self.title)
