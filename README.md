# FastAPI Haute Performance — Industrial Backend (Big Data Open Data: GDELT)

Backend **Python FastAPI** conçu pour démontrer un passage **POC → solution industrielle** :
- ingestion asynchrone de **Big Data open data** (GDELT)
- stockage en **Data Lake Parquet** (MinIO/S3)
- requêtage analytique rapide via **DuckDB**
- **observabilité** (logs JSON + métriques Prometheus)
- scripts de **benchmark** (k6 + Locust)

## Pourquoi ce projet est “industriel”
- **Non-bloquant** : ingestion via worker (Redis + Arq), l’API reste réactive.
- **Data Lake** : Parquet compressé, partitions temporelles.
- **Séparation OLTP / OLAP** : Postgres pour métadonnées, DuckDB pour analytics.
- **Mesurable** : métriques + tests + bench.

## Stack
- FastAPI, Uvicorn
- Redis, Arq worker
- MinIO (S3)
- DuckDB + PyArrow + Pandas
- SQLAlchemy (async) + asyncpg + Alembic
- Prometheus metrics, logs JSON

## Démo rapide
```bash
docker compose up --build
```

### Déclencher ingestion (N lots récents)
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/trigger?n_batches=2"
```

### Requête
```bash
curl "http://localhost:8000/api/v1/events/search?query=protest&limit=20"
```

### Bench
```bash
k6 run bench/k6-smoke.js
k6 run bench/k6-search.js
```

## Docs
- Architecture: `docs/ARCHITECTURE.md`
- Bench: `bench/README.md`

## Extension v3 (si tu veux aller plus loin)
- DuckDB direct sur S3 (`httpfs`) + pruning partitions
- Catalog partitions (Postgres) + index
- Auth JWT/OAuth2 + RBAC
- OpenTelemetry traces (API + worker)
- CI/CD + scans + SLO/SLA
