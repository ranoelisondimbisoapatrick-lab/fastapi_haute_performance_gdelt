import re
from dataclasses import dataclass
from typing import Iterable
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings


GDELT_LINE_RE = re.compile(r"^(\d+)\s+([a-fA-F0-9]{32})\s+(https?://\S+)$")


@dataclass(frozen=True)
class GdeltFile:
    bytes: int
    md5: str
    url: str
    ts: str  # YYYYMMDDHHMMSS

    @staticmethod
    def parse(line: str) -> "GdeltFile | None":
        m = GDELT_LINE_RE.match(line.strip())
        if not m:
            return None
        size = int(m.group(1))
        md5 = m.group(2)
        url = m.group(3)
        # Try to extract timestamp (first 14 digits in filename)
        ts_match = re.search(r"/(\d{14})\.", url)
        ts = ts_match.group(1) if ts_match else "unknown"
        return GdeltFile(bytes=size, md5=md5, url=url, ts=ts)


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=0.5, min=1, max=8))
async def fetch_lastupdate() -> list[GdeltFile]:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(settings.gdelt_lastupdate_url)
        r.raise_for_status()
        files: list[GdeltFile] = []
        for line in r.text.splitlines():
            gf = GdeltFile.parse(line)
            if gf:
                files.append(gf)
        return files


def pick_recent(files: list[GdeltFile], n: int) -> list[GdeltFile]:
    # lastupdate.txt often contains multiple datasets; we keep *export* (Events) by default.
    export = [f for f in files if ".export.CSV.zip" in f.url or ".export" in f.url]
    export_sorted = sorted(export, key=lambda x: x.ts, reverse=True)
    return export_sorted[: max(0, n)]
