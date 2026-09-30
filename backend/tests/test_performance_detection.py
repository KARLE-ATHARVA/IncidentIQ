import time
from datetime import datetime, timezone
from uuid import uuid4

from backend.app.services.detection import (
    DetectionConfig,
    detect_anomaly,
)


def test_detection_performance():
    historical_values = [
        100.0,
        101.0,
        99.0,
        100.0,
        102.0,
        98.0,
        101.0,
        99.0,
        100.0,
        101.0,
        99.0,
        100.0,
        102.0,
        98.0,
        100.0,
        101.0,
        99.0,
        100.0,
        101.0,
        99.0,
    ]

    recent_values = [
        180.0,
        181.0,
        179.0,
        182.0,
        180.0,
    ]

    config = DetectionConfig(
        minimum_observations=10,
        z_score_threshold=3.0,
        robust_z_score_threshold=3.5,
        persistence_window=5,
        minimum_anomalous_observations=3,
    )

    iteration_count = 10_000

    start_time = time.perf_counter()

    for _ in range(iteration_count):
        result = detect_anomaly(
            service_id=uuid4(),
            metric_event_id=uuid4(),
            metric_name="checkout_latency",
            current_value=180.0,
            observed_at=datetime.now(timezone.utc),
            historical_values=historical_values,
            recent_values=recent_values,
            config=config,
        )

    elapsed_seconds = time.perf_counter() - start_time

    average_latency_us = (
        elapsed_seconds / iteration_count
    ) * 1_000_000

    throughput = iteration_count / elapsed_seconds

    print("\n" + "=" * 60)
    print("INCIDENTIQ DETECTION PERFORMANCE")
    print("=" * 60)
    print(f"Iterations:             {iteration_count}")
    print(f"Total time:             {elapsed_seconds:.4f} s")
    print(f"Average latency:        {average_latency_us:.2f} µs")
    print(f"Throughput:             {throughput:.2f} detections/s")
    print(f"Final status:           {result.status.value}")
    print("=" * 60)

    assert result.status.value == "anomaly"
    assert elapsed_seconds > 0
    assert average_latency_us > 0
    assert throughput > 0