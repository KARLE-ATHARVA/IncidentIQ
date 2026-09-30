import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.services.incident_pipeline import (
    process_metric_event_for_incident,
)


def create_test_environment(db, index):
    user = User(
        email=f"pipeline-performance-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )
    db.add(user)
    db.flush()

    project = Project(
        name=f"Pipeline Performance Project {index}-{uuid4()}",
        owner_id=user.id,
    )
    db.add(project)
    db.flush()

    service = Service(
        name=f"checkout-{index}",
        project_id=project.id,
    )
    db.add(service)
    db.flush()

    return service


def create_metric(
    db,
    *,
    service_id,
    timestamp,
    value,
):
    event = MetricEvent(
        service_id=service_id,
        timestamp=timestamp,
        name="checkout_latency",
        value=value,
    )

    db.add(event)
    db.flush()

    return event


def create_log(
    db,
    *,
    service_id,
    timestamp,
):
    event = LogEvent(
        service_id=service_id,
        timestamp=timestamp,
        level="ERROR",
        message="Checkout request latency exceeded threshold",
    )

    db.add(event)
    db.flush()

    return event


def create_deployment(
    db,
    *,
    service_id,
    timestamp,
):
    event = DeploymentEvent(
        service_id=service_id,
        timestamp=timestamp,
        version="v2.4.0",
        description="Performance benchmark deployment",
    )

    db.add(event)
    db.flush()

    return event


def prepare_anomalous_event(db, index):
    service = create_test_environment(db, index)

    base_time = datetime.now(timezone.utc)

    # ---------------------------------------------------------
    # 20 historical normal observations
    # ---------------------------------------------------------

    for offset in range(20, 0, -1):
        create_metric(
            db,
            service_id=service.id,
            timestamp=base_time - timedelta(minutes=offset + 5),
            value=100.0 + (offset % 3),
        )

    # ---------------------------------------------------------
    # 5 recent anomalous observations
    # ---------------------------------------------------------

    for offset in range(5, 0, -1):
        create_metric(
            db,
            service_id=service.id,
            timestamp=base_time - timedelta(minutes=offset),
            value=180.0 + (offset % 3),
        )

    # ---------------------------------------------------------
    # Current anomalous observation
    # ---------------------------------------------------------

    current_event = create_metric(
        db,
        service_id=service.id,
        timestamp=base_time,
        value=180.0,
    )

    # ---------------------------------------------------------
    # Correlated error log
    # ---------------------------------------------------------

    create_log(
        db,
        service_id=service.id,
        timestamp=base_time + timedelta(seconds=10),
    )

    # ---------------------------------------------------------
    # Correlated deployment
    # ---------------------------------------------------------

    create_deployment(
        db,
        service_id=service.id,
        timestamp=base_time - timedelta(seconds=30),
    )

    return current_event


def test_incident_pipeline_performance():
    db = SessionLocal()

    try:
        benchmark_cases = []

        for index in range(10):
            benchmark_cases.append(
                prepare_anomalous_event(
                    db=db,
                    index=index,
                )
            )

        db.commit()

        # ---------------------------------------------------------
        # Benchmark
        # ---------------------------------------------------------

        start_time = time.perf_counter()

        created_incidents = 0

        for event in benchmark_cases:
            incident = process_metric_event_for_incident(
                db=db,
                metric_event_id=event.id,
            )

            if incident is not None:
                created_incidents += 1

        elapsed_seconds = time.perf_counter() - start_time

        average_latency_ms = (
            elapsed_seconds / len(benchmark_cases)
        ) * 1000

        throughput = (
            len(benchmark_cases) / elapsed_seconds
        )

        print("\n" + "=" * 60)
        print("INCIDENTIQ INCIDENT PIPELINE PERFORMANCE")
        print("=" * 60)
        print(f"Events processed:       {len(benchmark_cases)}")
        print(f"Incidents created:      {created_incidents}")
        print(f"Total time:             {elapsed_seconds:.4f} s")
        print(
            f"Average latency/event:  "
            f"{average_latency_ms:.2f} ms"
        )
        print(
            f"Throughput:             "
            f"{throughput:.2f} events/s"
        )
        print("=" * 60)

        assert len(benchmark_cases) == 10
        assert created_incidents == 10
        assert elapsed_seconds > 0
        assert average_latency_ms > 0
        assert throughput > 0

    finally:
        db.rollback()
        db.close()
