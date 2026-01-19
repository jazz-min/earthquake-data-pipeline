from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EarthquakeItem(BaseModel):
    event_id: str
    time: datetime
    magnitude: float | None = None
    place: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    depth_km: float | None = None
    url: str | None = None

    class Config:
        from_attributes = True


class EarthquakeListResponse(BaseModel):
    source: Literal["db", "usgs", "db_fallback"]
    data_fresh_as_of: datetime | None = None
    count: int
    limit: int
    offset: int
    items: list[EarthquakeItem]
    breaker_state: str | None = None
    fallback_reason: str | None = None


class EarthquakeDetailResponse(BaseModel):
    source: Literal["db"]
    item: EarthquakeItem


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    db: str
