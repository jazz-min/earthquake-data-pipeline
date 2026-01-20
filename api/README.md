# Earthquake API

A FastAPI service providing read-only access to earthquake data from a Postgres database, with an optional live endpoint that fetches data from the USGS API with circuit breaker protection.

## API Specification

* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* OpenAPI JSON: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## Endpoints

### Health & Readiness

**GET /health**
```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

**GET /ready**
```bash
curl http://localhost:8000/ready
# {"status":"ok","db":"ok"}
```

### Earthquake Data

**GET /earthquakes**

List earthquakes from the database with optional filtering and pagination.

Query Parameters:
- `start` - Filter events after this time (ISO format)
- `end` - Filter events before this time (ISO format)
- `min_magnitude` - Minimum magnitude (0-10)
- `max_magnitude` - Maximum magnitude (0-10)
- `bbox` - Bounding box as `min_lon,min_lat,max_lon,max_lat`
- `limit` - Maximum results (default: 50, max: 200)
- `offset` - Skip results (default: 0, max: 5000)
- `order` - Sort order by time: `asc` or `desc` (default: desc)

```bash
# Basic request
curl "http://localhost:8000/earthquakes?limit=5"

# With filters
curl "http://localhost:8000/earthquakes?min_magnitude=4.0&limit=10"

# With time range
curl "http://localhost:8000/earthquakes?start=2024-01-01T00:00:00&end=2024-01-31T23:59:59"

# With bounding box (California)
curl "http://localhost:8000/earthquakes?bbox=-125,32,-114,42&min_magnitude=3.0"
```

**GET /earthquakes/{event_id}**

Fetch a single earthquake by its event ID.

```bash
curl http://localhost:8000/earthquakes/us7000abcd
```

**GET /earthquakes/live**

Fetch live earthquake data from USGS API with circuit breaker protection. Falls back to database if USGS is unavailable.

Query Parameters:
- `start` - Filter events after this time (ISO format)
- `end` - Filter events before this time (ISO format)
- `min_magnitude` - Minimum magnitude (0-10)
- `bbox` - Bounding box as `min_lon,min_lat,max_lon,max_lat`
- `limit` - Maximum results (default: 50, max: 200)

```bash
# Fetch recent significant earthquakes
curl "http://localhost:8000/earthquakes/live?min_magnitude=5.0&limit=10"
```

Response includes:
- `source` - Data source: `usgs`, `db_fallback`
- `breaker_state` - Circuit breaker state: `closed`, `open`, `half_open`
- `fallback_reason` - Reason for fallback if applicable

## Running with Docker Compose

```bash
cd earthquake-data-pipeline
docker compose up --build -d

# Verify the API is running
curl http://localhost:8000/health

# Check database connectivity
curl http://localhost:8000/ready
```

## Running Tests

```bash
docker compose exec earthquake-api pytest
```

## Circuit Breaker Demo

The circuit breaker protects against cascading failures when USGS is unavailable.

**States:**
- `closed` - Normal operation, requests go to USGS
- `open` - USGS unavailable, requests go directly to database
- `half_open` - Testing if USGS has recovered

**Trigger the circuit breaker:**

1. Set an invalid USGS URL or very low timeout in `.env`:
   ```
   USGS_BASE_URL=https://invalid.example.com
   # or
   USGS_TIMEOUT_SECS=0.001
   ```

2. Make several requests to `/earthquakes/live`:
   ```bash
   for i in {1..6}; do
     curl -s "http://localhost:8000/earthquakes/live?limit=1" | jq '.breaker_state, .source'
   done
   ```

3. After 5 failures, the breaker opens and requests fall back to the database.

4. After 60 seconds (default), the breaker enters `half_open` state and tries USGS again.

## Configuration

Environment variables (with defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| DB_NAME | earthquake_db | Database name |
| DB_USER | earthquake_user | Database user |
| DB_PASS | earthquake_pass | Database password |
| DB_HOST | postgres | Database host |
| DB_PORT | 5432 | Database port |
| DB_SCHEMA | transformed_data | Schema containing earthquake data |
| USGS_BASE_URL | https://earthquake.usgs.gov/fdsnws/event/1/query | USGS API URL |
| USGS_TIMEOUT_SECS | 3 | Request timeout in seconds |
| USGS_RETRY_MAX | 2 | Maximum retry attempts |
| CB_FAILURE_THRESHOLD | 5 | Failures before circuit opens |
| CB_RECOVERY_SECS | 60 | Seconds before trying USGS again |

## Port Summary

| Service | Port |
|---------|------|
| earthquake-api | 8000 |
| postgres | 5432 |
| pgadmin | 8080 |
| airflow-webserver | 8081 |
| superset | 8089 |
