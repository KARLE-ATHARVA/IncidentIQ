
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.schemas.metric_event import MetricEventCreate
from backend.app.services.telemetry import create_metric_event


def create_test_environment(db):
    user = User(
        email=f"performance-{uuid4()}@example.com",
        password_hash="test-password-hash",
    )
    db.add(user)
    db.flush()

    project = Project(
        name=f"Performance Project {uuid4()}",
        owner_id=user.id,
    )
    db.add(project)
    db.flush()

    service = Service(
        name="checkout",
        project_id=project.id,
    )
    db.add(service)
    db.flush()

    return project, service


def test_metric_ingestion_performance():
    db = SessionLocal()

    try:
        _, service = create_test_environment(db)
        db.commit()

        event_count = 100

        start_time = time.perf_counter()

        for index in range(event_count):
            event = MetricEventCreate(
                timestamp=datetime.now(timezone.utc)
                + timedelta(seconds=index),
                name="checkout_latency",
                value=100.0 + (index % 10),
            )

            create_metric_event(
                db=db,
                service_id=service.id,
                data=event,
            )

        elapsed_seconds = time.perf_counter() - start_time

        average_latency_ms = (
            elapsed_seconds / event_count
        ) * 1000

        throughput = event_count / elapsed_seconds

        print("\n" + "=" * 60)
        print("INCIDENTIQ TELEMETRY PERFORMANCE")
        print("=" * 60)
        print(f"Events processed:       {event_count}")
        print(f"Total time:             {elapsed_seconds:.4f} s")
        print(f"Average latency/event:  {average_latency_ms:.2f} ms")
        print(f"Throughput:             {throughput:.2f} events/s")
        print("=" * 60)

        assert event_count == 100
        assert elapsed_seconds > 0
        assert average_latency_ms > 0
        assert throughput > 0

    finally:
        db.rollback()
        db.close()