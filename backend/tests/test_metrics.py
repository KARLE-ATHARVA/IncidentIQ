from backend.app.core.metrics import ApplicationMetrics


def test_metrics_start_empty():
    metrics = ApplicationMetrics()

    snapshot = metrics.snapshot()

    assert snapshot["requests"]["total"] == 0
    assert snapshot["requests"]["successful"] == 0
    assert snapshot["requests"]["errors"] == 0
    assert snapshot["latency"]["total_duration_ms"] == 0.0
    assert snapshot["latency"]["average_duration_ms"] == 0.0


def test_metrics_record_successful_request():
    metrics = ApplicationMetrics()

    metrics.record_request(
        path="/health",
        status_code=200,
        duration_ms=10.5,
    )

    snapshot = metrics.snapshot()

    assert snapshot["requests"]["total"] == 1
    assert snapshot["requests"]["successful"] == 1
    assert snapshot["requests"]["errors"] == 0
    assert snapshot["latency"]["total_duration_ms"] == 10.5
    assert snapshot["latency"]["average_duration_ms"] == 10.5
    assert snapshot["requests_by_path"]["/health"] == 1
    assert snapshot["requests_by_status"]["200"] == 1


def test_metrics_record_error_request():
    metrics = ApplicationMetrics()

    metrics.record_request(
        path="/api/test",
        status_code=500,
        duration_ms=25.0,
    )

    snapshot = metrics.snapshot()

    assert snapshot["requests"]["total"] == 1
    assert snapshot["requests"]["successful"] == 0
    assert snapshot["requests"]["errors"] == 1
    assert snapshot["requests_by_path"]["/api/test"] == 1
    assert snapshot["requests_by_status"]["500"] == 1


def test_metrics_calculate_average_latency():
    metrics = ApplicationMetrics()

    metrics.record_request(
        path="/health",
        status_code=200,
        duration_ms=10.0,
    )

    metrics.record_request(
        path="/health",
        status_code=200,
        duration_ms=30.0,
    )

    snapshot = metrics.snapshot()

    assert snapshot["requests"]["total"] == 2
    assert snapshot["requests"]["successful"] == 2
    assert snapshot["latency"]["total_duration_ms"] == 40.0
    assert snapshot["latency"]["average_duration_ms"] == 20.0
    assert snapshot["requests_by_path"]["/health"] == 2
    assert snapshot["requests_by_status"]["200"] == 2


def test_metrics_track_multiple_paths_and_statuses():
    metrics = ApplicationMetrics()

    metrics.record_request(
        path="/health",
        status_code=200,
        duration_ms=5.0,
    )

    metrics.record_request(
        path="/api/incidents",
        status_code=200,
        duration_ms=15.0,
    )

    metrics.record_request(
        path="/api/incidents",
        status_code=404,
        duration_ms=20.0,
    )

    snapshot = metrics.snapshot()

    assert snapshot["requests"]["total"] == 3
    assert snapshot["requests"]["successful"] == 2
    assert snapshot["requests"]["errors"] == 1

    assert snapshot["requests_by_path"]["/health"] == 1
    assert snapshot["requests_by_path"]["/api/incidents"] == 2

    assert snapshot["requests_by_status"]["200"] == 2
    assert snapshot["requests_by_status"]["404"] == 1