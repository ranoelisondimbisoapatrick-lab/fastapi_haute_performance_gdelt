# FastAPI Haute Performance — POC → Industriel (GDELT Big Data)

Backend Python **FastAPI** conçu pour passer d’un **POC** à une **solution industrielle** avec ingestion **Big Data libre de droit** et observabilité.

## Données Big Data (libres / open data)

Ce projet ingère **GDELT 2.x** (Global Database of Events, Language, and Tone) via le flux *15 minutes* exposé par `lastupdate.txt` et archive les lots dans un Data Lake (Parquet).  
- GDELT est annoncé comme **100% free and open** (open data).  
- Les datasets sont mis à jour **toutes les 15 minutes** (live).  

Sources (à citer dans un document / publication) :
- GDELT “Data: Querying, Analyzing and Downloading”: https://www.gdeltproject.org/data.html
- Flux “lastupdate.txt”: https://data.gdeltproject.org/gdeltv2/lastupdate.txt

> **Note**: GDELT est massif. En local, ce repo ingère un volume contrôlé (ex: N derniers lots) mais le design est prêt à scaler (S3/MinIO, workers, partitionnement).

## Architecture

- **API** : FastAPI (async) + OpenAPI
- **DB** : PostgreSQL (métadonnées, suivi d’ingestion)
- **Data Lake** : Filesystem (Parquet) + Parquet (partitions par date)
- **Queue** : Redis + Arq (jobs async Python, léger et rapide)
- **Query Engine** : DuckDB (lit Parquet, très performant)
- **Observabilité** : Prometheus metrics + logs JSON + OpenTelemetry (optionnel)

```
Clients → FastAPI → (Postgres/Redis)
                 ↘  DuckDB → Parquet (filesystem)
Worker (Arq) → Ingestion GDELT → Parquet partitions → metadata Postgres
```

## Démarrage rapide (Docker)

### 1) Prérequis
- Docker + Docker Compose

### 2) Lancer la stack
```bash
docker compose up --build
```

### 3) Tester
- API: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics

## Endpoints

- `GET /health`
- `POST /api/v1/ingest/trigger?n_batches=2` : déclenche ingestion des *N derniers lots* GDELT
- `GET /api/v1/events/search?query=protest&since=2026-02-01&limit=50` : recherche plein texte (DuckDB) dans Parquet

## Perf (base)
- Endpoints async, pooling DB, timeouts HTTP, streaming unzip.
- La lecture analytique se fait via DuckDB directement sur Parquet (pattern industriel très courant).

## Développement local (sans Docker)
Voir `pyproject.toml` (Poetry) et `.env.example`.

---
## Licence
Code: MIT (fichier `LICENSE`).  
Données: voir conditions propres à la source (GDELT).


## Docs & Bench
- Architecture: `docs/ARCHITECTURE.md`
- Bench: `bench/README.md`
- README pro: `README_PRO.md`


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


## OpenAPI / Swagger
- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`
- ReDoc: `GET /redoc`
