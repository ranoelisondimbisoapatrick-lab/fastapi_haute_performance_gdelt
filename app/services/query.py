from __future__ import annotations

from app.services.duckdb_queries import search_fulltext


def search_events(query: str, since: str | None, limit: int) -> tuple[int, list[dict]]:
    # Backward compatible wrapper (since only)
    return search_fulltext(query=query, since=since, until=None, limit=limit)
