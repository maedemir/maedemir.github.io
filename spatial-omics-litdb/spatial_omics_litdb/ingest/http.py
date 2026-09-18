from __future__ import annotations

import time
from typing import Any

import httpx

from spatial_omics_litdb.config import Settings


class HttpClient:
    def __init__(self, settings: Settings, timeout: float = 45.0):
        self.settings = settings
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": f"{settings.user_agent} mailto:{settings.contact_email}"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def get_json(self, url: str, params: dict[str, Any] | None = None, pause: float = 0.2) -> Any:
        response = self._client.get(url, params=params)
        response.raise_for_status()
        if pause:
            time.sleep(pause)
        return response.json()

    def get_text(self, url: str, params: dict[str, Any] | None = None, pause: float = 0.35) -> str:
        response = self._client.get(url, params=params)
        response.raise_for_status()
        if pause:
            time.sleep(pause)
        return response.text

    def download(self, url: str, dest, max_bytes: int = 80_000_000) -> bool:
        with self._client.stream("GET", url) as response:
            response.raise_for_status()
            content_type = (response.headers.get("content-type") or "").lower()
            if "html" in content_type and "pdf" not in content_type:
                return False
            written = 0
            with open(dest, "wb") as handle:
                for chunk in response.iter_bytes(65536):
                    written += len(chunk)
                    if written > max_bytes:
                        handle.close()
                        dest.unlink(missing_ok=True)
                        return False
                    handle.write(chunk)
        return dest.exists() and dest.stat().st_size > 1000
