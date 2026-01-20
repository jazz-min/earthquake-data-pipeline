from datetime import datetime
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.openapi.docs import get_redoc_html
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import earthquakes as earthquake_repo
from app.schemas import (
    CircuitBreakerStatusResponse,
    EarthquakeDetailResponse,
    EarthquakeListResponse,
    HealthResponse,
    ReadyResponse,
)
from app.services.circuit_breaker import CircuitBreaker
from app.services.usgs_client import USGSClientError, fetch_earthquakes as fetch_usgs_earthquakes
from app.settings import settings

app = FastAPI(
    title="Earthquake API",
    description="Read-only API for earthquake data from Postgres with optional live USGS data",
    version="1.0.0",
    redoc_url=None,  # Disable default ReDoc to use custom route
)


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Custom ReDoc endpoint with stable CDN version."""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
    )


# Prometheus metrics instrumentation
Instrumentator(
    excluded_handlers=["/metrics", "/health"],
).instrument(app).expose(app, include_in_schema=False)

# Global circuit breaker instance
circuit_breaker = CircuitBreaker(
    failure_threshold=settings.cb_failure_threshold,
    recovery_secs=settings.cb_recovery_secs,
)


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint."""
    return HealthResponse(status="ok")


@app.get("/ready", response_model=ReadyResponse)
def ready(db: Session = Depends(get_db)):
    """Readiness check - verifies database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return ReadyResponse(status="ok", db="ok")
    except Exception:
        return ReadyResponse(status="degraded", db="down")


@app.get("/circuit-breaker/status", response_model=CircuitBreakerStatusResponse)
def circuit_breaker_status():
    """Get current circuit breaker state and metrics."""
    return CircuitBreakerStatusResponse(**circuit_breaker.get_status())


@app.get("/earthquakes", response_model=EarthquakeListResponse)
def list_earthquakes(
    db: Session = Depends(get_db),
    start: datetime | None = Query(None, description="Filter events after this time (ISO format)"),
    end: datetime | None = Query(None, description="Filter events before this time (ISO format)"),
    min_magnitude: float | None = Query(None, ge=0, le=10, description="Minimum magnitude"),
    max_magnitude: float | None = Query(None, ge=0, le=10, description="Maximum magnitude"),
    bbox: Annotated[
        str | None,
        Query(
            description="Bounding box as min_lon,min_lat,max_lon,max_lat",
            pattern=r"^-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*$",
        ),
    ] = None,
    limit: int = Query(50, ge=1, le=200, description="Maximum results to return"),
    offset: int = Query(0, ge=0, le=5000, description="Number of results to skip"),
    order: Literal["asc", "desc"] = Query("desc", description="Sort order by time"),
):
    """
    List earthquakes from the database.

    Supports filtering by time range, magnitude range, and bounding box.
    Results are paginated with limit/offset.
    """
    parsed_bbox = None
    if bbox:
        coords = [float(x) for x in bbox.split(",")]
        parsed_bbox = (coords[0], coords[1], coords[2], coords[3])

    items = earthquake_repo.get_earthquakes(
        db=db,
        start=start,
        end=end,
        min_magnitude=min_magnitude,
        max_magnitude=max_magnitude,
        bbox=parsed_bbox,
        limit=limit,
        offset=offset,
        order=order,
    )

    data_fresh_as_of = earthquake_repo.get_max_event_time(db)

    return EarthquakeListResponse(
        source="db",
        data_fresh_as_of=data_fresh_as_of,
        count=len(items),
        limit=limit,
        offset=offset,
        items=items,
    )


@app.get("/earthquakes/live", response_model=EarthquakeListResponse)
def list_live_earthquakes(
    db: Session = Depends(get_db),
    start: datetime | None = Query(None, description="Filter events after this time (ISO format)"),
    end: datetime | None = Query(None, description="Filter events before this time (ISO format)"),
    min_magnitude: float | None = Query(None, ge=0, le=10, description="Minimum magnitude"),
    bbox: Annotated[
        str | None,
        Query(
            description="Bounding box as min_lon,min_lat,max_lon,max_lat",
            pattern=r"^-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*$",
        ),
    ] = None,
    limit: int = Query(50, ge=1, le=200, description="Maximum results to return"),
):
    """
    Fetch live earthquake data from USGS API with circuit breaker protection.

    If USGS is unavailable or circuit breaker is open, falls back to database.
    Response includes breaker_state and fallback_reason when applicable.
    """
    parsed_bbox = None
    if bbox:
        coords = [float(x) for x in bbox.split(",")]
        parsed_bbox = (coords[0], coords[1], coords[2], coords[3])

    breaker_state = circuit_breaker.state.value
    fallback_reason = None

    # Check if circuit breaker allows the request
    if circuit_breaker.should_allow_request():
        try:
            items = fetch_usgs_earthquakes(
                start=start,
                end=end,
                min_magnitude=min_magnitude,
                bbox=parsed_bbox,
                limit=limit,
            )
            circuit_breaker.record_success()

            return EarthquakeListResponse(
                source="usgs",
                data_fresh_as_of=datetime.utcnow(),
                count=len(items),
                limit=limit,
                offset=0,
                items=items,
                breaker_state=circuit_breaker.state.value,
            )
        except USGSClientError as e:
            circuit_breaker.record_failure()
            fallback_reason = str(e)
            breaker_state = circuit_breaker.state.value
    else:
        fallback_reason = "Circuit breaker is open"

    # Fallback to database
    items = earthquake_repo.get_earthquakes(
        db=db,
        start=start,
        end=end,
        min_magnitude=min_magnitude,
        bbox=parsed_bbox,
        limit=limit,
        offset=0,
        order="desc",
    )

    data_fresh_as_of = earthquake_repo.get_max_event_time(db)

    return EarthquakeListResponse(
        source="db_fallback",
        data_fresh_as_of=data_fresh_as_of,
        count=len(items),
        limit=limit,
        offset=0,
        items=items,
        breaker_state=breaker_state,
        fallback_reason=fallback_reason,
    )


@app.get("/earthquakes/{event_id}", response_model=EarthquakeDetailResponse)
def get_earthquake(event_id: str, db: Session = Depends(get_db)):
    """Fetch a single earthquake by its event ID."""
    item = earthquake_repo.get_earthquake_by_id(db, event_id)

    if item is None:
        raise HTTPException(status_code=404, detail=f"Earthquake with id '{event_id}' not found")

    return EarthquakeDetailResponse(source="db", item=item)
