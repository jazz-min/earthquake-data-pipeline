from datetime import datetime
from typing import Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas import EarthquakeItem
from app.settings import settings


def get_earthquakes(
    db: Session,
    start: datetime | None = None,
    end: datetime | None = None,
    min_magnitude: float | None = None,
    max_magnitude: float | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    limit: int = 50,
    offset: int = 0,
    order: Literal["asc", "desc"] = "desc",
) -> list[EarthquakeItem]:
    """
    Fetch earthquakes from the database with filtering and pagination.

    Args:
        db: Database session
        start: Filter events after this time
        end: Filter events before this time
        min_magnitude: Minimum magnitude
        max_magnitude: Maximum magnitude
        bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat)
        limit: Maximum number of results
        offset: Number of results to skip
        order: Sort order by time ('asc' or 'desc')
    """
    schema = settings.db_schema

    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if start:
        conditions.append("time >= :start")
        params["start"] = start
    if end:
        conditions.append("time <= :end")
        params["end"] = end
    if min_magnitude is not None:
        conditions.append("magnitude >= :min_magnitude")
        params["min_magnitude"] = min_magnitude
    if max_magnitude is not None:
        conditions.append("magnitude <= :max_magnitude")
        params["max_magnitude"] = max_magnitude
    if bbox:
        min_lon, min_lat, max_lon, max_lat = bbox
        conditions.append("longitude >= :min_lon")
        conditions.append("longitude <= :max_lon")
        conditions.append("latitude >= :min_lat")
        conditions.append("latitude <= :max_lat")
        params["min_lon"] = min_lon
        params["max_lon"] = max_lon
        params["min_lat"] = min_lat
        params["max_lat"] = max_lat

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    order_direction = "ASC" if order == "asc" else "DESC"

    query = text(f"""
        SELECT id, time, place, magnitude, latitude, longitude, depth_km, url
        FROM {schema}.stg_earthquakes
        WHERE {where_clause}
        ORDER BY time {order_direction}, id
        LIMIT :limit OFFSET :offset
    """)

    result = db.execute(query, params)
    rows = result.fetchall()

    return [
        EarthquakeItem(
            event_id=row.id,
            time=row.time,
            place=row.place,
            magnitude=row.magnitude,
            latitude=row.latitude,
            longitude=row.longitude,
            depth_km=row.depth_km,
            url=row.url,
        )
        for row in rows
    ]


def get_earthquake_by_id(db: Session, event_id: str) -> EarthquakeItem | None:
    """Fetch a single earthquake by its ID."""
    schema = settings.db_schema

    query = text(f"""
        SELECT id, time, place, magnitude, latitude, longitude, depth_km, url
        FROM {schema}.stg_earthquakes
        WHERE id = :event_id
    """)

    result = db.execute(query, {"event_id": event_id})
    row = result.fetchone()

    if row is None:
        return None

    return EarthquakeItem(
        event_id=row.id,
        time=row.time,
        place=row.place,
        magnitude=row.magnitude,
        latitude=row.latitude,
        longitude=row.longitude,
        depth_km=row.depth_km,
        url=row.url,
    )


def get_max_event_time(db: Session) -> datetime | None:
    """Get the most recent event time in the database."""
    schema = settings.db_schema

    query = text(f"""
        SELECT MAX(time) as max_time
        FROM {schema}.stg_earthquakes
    """)

    result = db.execute(query)
    row = result.fetchone()

    return row.max_time if row else None
