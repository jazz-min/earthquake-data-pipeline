import threading
import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    In-memory circuit breaker implementation.

    State machine:
    - CLOSED: Allow calls. On failure, increment counter. If >= threshold -> OPEN
    - OPEN: Reject calls immediately. After recovery_secs -> HALF_OPEN
    - HALF_OPEN: Allow 1 trial call. Success -> CLOSED, Failure -> OPEN

    Note: In production, consider using Redis for state persistence across instances.
    """

    def __init__(self, failure_threshold: int = 5, recovery_secs: int = 60):
        self._failure_threshold = failure_threshold
        self._recovery_secs = recovery_secs
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._check_recovery()
            return self._state

    def _check_recovery(self) -> None:
        """Check if circuit should transition from OPEN to HALF_OPEN."""
        if self._state == CircuitState.OPEN and self._last_failure_time is not None:
            if time.time() - self._last_failure_time >= self._recovery_secs:
                self._state = CircuitState.HALF_OPEN

    def should_allow_request(self) -> bool:
        """Check if a request should be allowed through."""
        with self._lock:
            self._check_recovery()
            if self._state == CircuitState.CLOSED:
                return True
            elif self._state == CircuitState.HALF_OPEN:
                return True
            else:  # OPEN
                return False

    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None

    def record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self._failure_threshold:
                    self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Reset the circuit breaker to initial state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None

    def get_status(self) -> dict:
        """Get current circuit breaker status."""
        with self._lock:
            self._check_recovery()
            seconds_until_recovery = None
            if self._state == CircuitState.OPEN and self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                seconds_until_recovery = max(0, self._recovery_secs - elapsed)

            return {
                "state": self._state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self._failure_threshold,
                "recovery_secs": self._recovery_secs,
                "seconds_until_recovery": seconds_until_recovery,
                "allowing_requests": self._state != CircuitState.OPEN,
            }
