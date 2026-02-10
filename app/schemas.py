from pydantic import BaseModel, Field
from datetime import date


class IngestTriggerResponse(BaseModel):
    queued: int


class EventSearchResponse(BaseModel):
    count: int
    rows: list[dict] = Field(default_factory=list)
