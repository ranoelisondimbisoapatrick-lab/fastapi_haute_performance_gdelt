# Contributing (Style & Best Practices)

## Python style
- Use type hints everywhere.
- Prefer small functions and clear names.
- Add module docstrings at the top of every file.
- Add docstrings to public functions/classes.
- Keep business logic in `app/services/*`, not in routers.

## API / OpenAPI
- Always set `response_model=...` for endpoints.
- Use `summary`, `description`, and Query constraints to make Swagger useful.
- Avoid returning raw `dict` when a stable schema can be declared.

## Observability
- Use JSON logs for structured data.
- Catch per-item errors in batch ingestion (avoid failing the whole run).
- Keep metrics low-cardinality in production.

## Testing
- Add unit tests for parsers and pure functions.
- Add integration tests for ingestion and DuckDB queries (small samples).
