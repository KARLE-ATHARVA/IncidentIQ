from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.services.correlation import CorrelationLevel
from backend.app.services.correlation_integration import (
    correlate_metric_event_with_telemetry,
)


def test_correlate_metric_event_with_real_telemetry():
    db = SessionLocal()

    try:
        user = User(
            email=f"correlation-integration-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )

        db.add(user)
        db.flush()

        project = Project(
            name="Correlation Integration Project",
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

        base_time = datetime.now(timezone.utc)

        metric = MetricEvent(
            service_id=service.id,
            timestamp=base_time,
            name="checkout_latency",
            value=250.0,
        )

        error_log = LogEvent(
            service_id=service.id,
            timestamp=base_time + timedelta(seconds=30),
            level="ERROR",
            message="Payment provider timeout",
        )

        deployment = DeploymentEvent(
            service_id=service.id,
            timestamp=base_time - timedelta(seconds=60),
            version="checkout-v42",
            description="Payment timeout fix",
        )

        unrelated_log = LogEvent(
            service_id=service.id,
            timestamp=base_time + timedelta(seconds=30),
            level="INFO",
            message="Checkout request completed",
        )

        db.add_all(
            [
                metric,
                error_log,
                deployment,
                unrelated_log,
            ]
        )

        db.flush()

        results = correlate_metric_event_with_telemetry(
            db=db,
            metric_event_id=metric.id,
        )

        assert len(results) == 2

        levels = {
            result.correlation_level
            for result in results
        }

        assert (
            CorrelationLevel.STRONG in levels
            or CorrelationLevel.VERY_STRONG in levels
        )

        for result in results:
            assert result.same_service is True
            assert result.temporal_score > 0

    finally:
        db.rollback()
        db.close()
