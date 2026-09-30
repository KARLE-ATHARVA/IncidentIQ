import threading
from collections import defaultdict


class ApplicationMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()

        self._total_requests = 0
        self._successful_requests = 0
        self._error_requests = 0
        self._total_duration_ms = 0.0

        self._requests_by_path: dict[str, int] = defaultdict(int)
        self._requests_by_status: dict[str, int] = defaultdict(int)

    def record_request(
        self,
        path: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        with self._lock:
            self._total_requests += 1
            self._total_duration_ms += duration_ms

            self._requests_by_path[path] += 1
            self._requests_by_status[str(status_code)] += 1

            if status_code < 400:
                self._successful_requests += 1
            else:
                self._error_requests += 1

    def snapshot(self) -> dict:
        with self._lock:
            average_duration_ms = (
                self._total_duration_ms / self._total_requests
                if self._total_requests
                else 0.0
            )

            return {
                "requests": {
                    "total": self._total_requests,
                    "successful": self._successful_requests,
                    "errors": self._error_requests,
                },
                "latency": {
                    "total_duration_ms": round(
                        self._total_duration_ms,
                        2,
                    ),
                    "average_duration_ms": round(
                        average_duration_ms,
                        2,
                    ),
                },
                "requests_by_path": dict(
                    self._requests_by_path
                ),
                "requests_by_status": dict(
                    self._requests_by_status
                ),
            }


metrics = ApplicationMetrics()
