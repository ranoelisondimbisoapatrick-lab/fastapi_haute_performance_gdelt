# FastAPI Haute Performance — Industrial Backend (Big Data Open Data: GDELT)

Backend **Python FastAPI** conçu pour démontrer un passage **POC → solution industrielle** :
- ingestion asynchrone de **Big Data open data** (GDELT)
- stockage en **Data Lake Parquet** (filesystem local)
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
- Filesystem local
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


## Mode 100% local (sans Docker)

```bash
poetry install
# (optionnel) copie .env.example -> .env et ajuste DATA_LAKE_PATH
poetry run python run_api.py
```

- Swagger: http://127.0.0.1:8000/docs

Déclencher ingestion (background task):
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ingest/trigger?n_batches=1"
```

One-shot ingestion (sans API):
```bash
poetry run python run_ingest_once.py --n 1
```

## Scheduler local (ingestion périodique)

Lance une ingestion automatique toutes les **15 minutes** (modifiable) :

```bash
# défaut: 15 minutes, 1 batch
poetry run python run_scheduler.py

# exemple: toutes les 60 minutes, 2 batches
INGEST_INTERVAL_MINUTES=60 INGEST_N_BATCHES=2 poetry run python run_scheduler.py
```

## Ingestion “streaming” (mémoire optimisée)
- téléchargement HTTP **en streaming** vers fichier temporaire (pas tout en RAM)
- extraction zip **en streaming**
- conversion CSV → Parquet via **PyArrow**

## Schéma Events (colonnes nommées)
Quand la largeur du fichier correspond au schéma Events GDELT, les colonnes Parquet sont **nommées** (`GlobalEventID`, `EventCode`, `AvgTone`, `SOURCEURL`, etc.).
Sinon, fallback automatique vers `c1..cN`.

## Endpoints analytics (DuckDB)

- `GET /api/v1/analytics/top-event-codes?since=YYYY-MM-DD&limit=10`
- `GET /api/v1/analytics/top-countries?since=YYYY-MM-DD&limit=10`
- `GET /api/v1/analytics/tone?since=YYYY-MM-DD`

> Astuce: commence par ingérer au moins 1 batch, puis teste ces endpoints.
