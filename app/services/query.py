from __future__ import annotations

"""app.services.query

Thin service wrapper for event search.

This module exists to keep the API layer decoupled from the DuckDB implementation.
In an industrial evolution, you might:
- add caching
- add precomputed indexes/materialized views
- add more structured filtering instead of full-text LIKE
"""

from app.services.duckdb_queries import search_fulltext


def search_events(query: str, since: str | None, limit: int) -> tuple[int, list[dict]]:
    """Backward-compatible wrapper around DuckDB full-text search."""
    return search_fulltext(query=query, since=since, until=None, limit=limit)
