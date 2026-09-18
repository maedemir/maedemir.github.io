from __future__ import annotations

from spatial_omics_litdb.config import Settings
from spatial_omics_litdb.ingest.http import HttpClient


def lookup_unpaywall(client: HttpClient, doi: str, settings: Settings) -> dict:
    try:
        payload = client.get_json(
            f"https://api.unpaywall.org/v2/{doi}",
            params={"email": settings.contact_email},
            pause=0.15,
        )
    except Exception:
        return {}
    best = payload.get("best_oa_location") or {}
    pdf_url = best.get("url_for_pdf") or best.get("url")
    is_oa = bool(payload.get("is_oa"))
    if not is_oa:
        pdf_url = None
    elif pdf_url and "pdf" not in pdf_url.lower() and not best.get("url_for_pdf"):
        # Landing pages are not treated as PDFs.
        pdf_url = best.get("url_for_pdf")
    return {
        "is_oa": is_oa,
        "oa_status": payload.get("oa_status"),
        "pdf_url": pdf_url if is_oa else None,
        "license": (best.get("license") if is_oa else None),
    }
