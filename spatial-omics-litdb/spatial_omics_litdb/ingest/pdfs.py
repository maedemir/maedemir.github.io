from __future__ import annotations

import re
from pathlib import Path

from spatial_omics_litdb.config import Settings
from spatial_omics_litdb.ingest.http import HttpClient


def doi_filename(doi: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", doi)
    return f"{safe[:180]}.pdf"


def download_oa_pdf(client: HttpClient, pdf_url: str, doi: str, settings: Settings) -> Path | None:
    dest = settings.pdf_dir / doi_filename(doi)
    if dest.exists() and dest.stat().st_size > 1000:
        return dest
    try:
        ok = client.download(pdf_url, dest)
    except Exception:
        dest.unlink(missing_ok=True)
        return None
    return dest if ok else None
