from fastapi import APIRouter, BackgroundTasks, Query
from app.schemas import IngestTriggerResponse, EventSearchResponse
from fastapi import BackgroundTasks
from app.tasks import enqueue_ingestion, run_ingestion_now
from app.services.query import search_events

router = APIRouter(prefix="/api/v1")


@router.post("/ingest/trigger", response_model=IngestTriggerResponse)
async def trigger_ingest(background_tasks: BackgroundTasks, n_batches: int = Query(2, ge=1, le=20)):
    queued = await enqueue_ingestion(n_batches=n_batches)
    background_tasks.add_task(run_ingestion_now, n_batches)
    return IngestTriggerResponse(queued=queued)


@router.get("/events/search", response_model=EventSearchResponse)
async def events_search(
    query: str = Query(..., min_length=2),
    since: str | None = None,
    limit: int = Query(50, ge=1, le=500),
):
    count, rows = search_events(query=query, since=since, limit=limit)
    return EventSearchResponse(count=count, rows=rows)
