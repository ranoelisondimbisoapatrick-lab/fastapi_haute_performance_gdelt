from __future__ import annotations

"""app.services.gdelt

GDELT discovery utilities.

This service fetches the `lastupdate.txt` file and parses it into a list of
downloadable batches (URLs).

The `lastupdate.txt` format typically contains lines like:
  <size> <md5> <url>

We focus on "Events" exports (files ending with `.export.CSV.zip`), because
they are frequent and massive, and ideal for Big Data ingestion demos.

Reliability:
- Network calls are retried using tenacity.
- Default URL uses HTTP to avoid SSL/certificate issues in some environments.
"""

import logging
from dataclasses import dataclass
from typing import Iterable

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GdeltFile:
    """Represents one GDELT batch file entry."""

    size: int
    md5: str
    url: str
    ts: str  # extracted timestamp like YYYYMMDDHHMMSS, or "unknown"


def _parse_ts_from_url(url: str) -> str:
    """Extract timestamp from a GDELT filename, if possible."""
    # Example: 20260210001500.export.CSV.zip
    name = url.split("/")[-1]
    if len(name) >= 14 and name[:14].isdigit():
        return name[:14]
    return "unknown"


def _parse_lastupdate_text(text: str) -> list[GdeltFile]:
    """Parse lastupdate.txt into structured entries."""
    files: list[GdeltFile] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        size_str, md5, url = parts[0], parts[1], parts[2]
        try:
            size = int(size_str)
        except ValueError:
            continue
        files.append(GdeltFile(size=size, md5=md5, url=url, ts=_parse_ts_from_url(url)))
    return files


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def fetch_lastupdate() -> list[GdeltFile]:
    """Fetch and parse GDELT lastupdate.txt.

    Returns:
        List of GdeltFile entries.

    Raises:
        httpx.HTTPError if network request fails after retries.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(settings.gdelt_lastupdate_url)
        r.raise_for_status()
        files = _parse_lastupdate_text(r.text)

    logger.info("Fetched lastupdate: %s entries", len(files))
    return files


def pick_recent(files: list[GdeltFile], n: int) -> list[GdeltFile]:
    """Pick N most recent *Events export* batches from the parsed list."""
    exports = [f for f in files if f.url.endswith(".export.CSV.zip")]
    # lastupdate is typically ordered newest-first; keep it simple:
    return exports[:n]
