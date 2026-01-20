import time
from datetime import datetime

import httpx

from app.metrics import usgs_request_duration_seconds, usgs_requests_total
from app.schemas import EarthquakeItem
from app.settings import settings


class USGSClientError(Exception):
    """Error communicating with USGS API."""

    pass


def fetch_earthquakes(
    start: datetime | None = None,
    end: datetime | None = None,
    min_magnitude: float | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    limit: int = 50,
) -> list[EarthquakeItem]:
    """
    Fetch earthquakes from USGS API.

    Args:
        start: Filter events after this time
        end: Filter events before this time
        min_magnitude: Minimum magnitude
        bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat)
        limit: Maximum number of results

    Returns:
        List of EarthquakeItem objects

    Raises:
        USGSClientError: If the request fails after retries
    """
    params: dict = {
        "format": "geojson",
        "limit": limit,
        "orderby": "time",
    }

    if start:
        params["starttime"] = start.isoformat()
    if end:
        params["endtime"] = end.isoformat()
    if min_magnitude is not None:
        params["minmagnitude"] = min_magnitude
    if bbox:
        min_lon, min_lat, max_lon, max_lat = bbox
        params["minlongitude"] = min_lon
        params["maxlongitude"] = max_lon
        params["minlatitude"] = min_lat
        params["maxlatitude"] = max_lat

    last_exception: Exception | None = None
    backoff_times = [0.5, 1.0]  # Exponential backoff delays

    for attempt in range(settings.usgs_retry_max + 1):
        request_start = time.monotonic()
        try:
            with httpx.Client(timeout=settings.usgs_timeout_secs) as client:
                response = client.get(settings.usgs_base_url, params=params)

                duration = time.monotonic() - request_start
                usgs_request_duration_seconds.observe(duration)

                if response.status_code == 429:
                    usgs_requests_total.labels(status="rate_limited").inc()
                    raise USGSClientError("Rate limited by USGS API")

                if response.status_code >= 500:
                    usgs_requests_total.labels(status="failure").inc()
                    raise USGSClientError(f"USGS API server error: {response.status_code}")

                response.raise_for_status()
                data = response.json()

                usgs_requests_total.labels(status="success").inc()
                return _parse_geojson_features(data.get("features", []))

        except httpx.TimeoutException as e:
            duration = time.monotonic() - request_start
            usgs_request_duration_seconds.observe(duration)
            usgs_requests_total.labels(status="timeout").inc()
            last_exception = USGSClientError(f"Request timeout: {e}")
        except httpx.HTTPStatusError as e:
            duration = time.monotonic() - request_start
            usgs_request_duration_seconds.observe(duration)
            usgs_requests_total.labels(status="failure").inc()
            last_exception = USGSClientError(f"HTTP error: {e}")
        except httpx.RequestError as e:
            duration = time.monotonic() - request_start
            usgs_request_duration_seconds.observe(duration)
            usgs_requests_total.labels(status="failure").inc()
            last_exception = USGSClientError(f"Request error: {e}")
        except USGSClientError:
            # Already tracked above (rate_limited or server error)
            raise

        # Apply backoff before retry (if not last attempt)
        if attempt < settings.usgs_retry_max and attempt < len(backoff_times):
            time.sleep(backoff_times[attempt])

    raise last_exception or USGSClientError("Unknown error")


def _parse_geojson_features(features: list[dict]) -> list[EarthquakeItem]:
    """Parse USGS GeoJSON features into EarthquakeItem objects."""
    items = []

    for feature in features:
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        coordinates = geometry.get("coordinates", [None, None, None])

        # USGS time is in milliseconds since epoch
        time_ms = props.get("time")
        event_time = datetime.fromtimestamp(time_ms / 1000) if time_ms else None

        items.append(
            EarthquakeItem(
                event_id=feature.get("id", ""),
                time=event_time,
                magnitude=props.get("mag"),
                place=props.get("place"),
                latitude=coordinates[1] if len(coordinates) > 1 else None,
                longitude=coordinates[0] if len(coordinates) > 0 else None,
                depth_km=coordinates[2] if len(coordinates) > 2 else None,
                url=props.get("url"),
            )
        )

    return items
