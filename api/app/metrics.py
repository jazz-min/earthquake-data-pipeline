from prometheus_client import Counter, Gauge, Histogram

# Circuit Breaker Metrics
circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Current circuit breaker state (0=closed, 1=open, 2=half_open)",
)

circuit_breaker_failure_count = Gauge(
    "circuit_breaker_failure_count",
    "Current consecutive failure count",
)

# USGS Client Metrics
usgs_request_duration_seconds = Histogram(
    "usgs_request_duration_seconds",
    "Duration of USGS API requests in seconds",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0],
)

usgs_requests_total = Counter(
    "usgs_requests_total",
    "Total USGS API requests",
    ["status"],  # success, failure, timeout, rate_limited
)

STATE_VALUES = {"closed": 0, "open": 1, "half_open": 2}
