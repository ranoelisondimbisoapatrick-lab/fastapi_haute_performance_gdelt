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
- **Data Lake** : MinIO (S3) + Parquet (partitions par date)
- **Queue** : Redis + Arq (jobs async Python, léger et rapide)
- **Query Engine** : DuckDB (lit Parquet, très performant)
- **Observabilité** : Prometheus metrics + logs JSON + OpenTelemetry (optionnel)

```
Clients → FastAPI → (Postgres/Redis)
                 ↘  DuckDB → Parquet (MinIO/S3)
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
