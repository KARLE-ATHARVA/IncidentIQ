from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.core.security import create_access_token
from backend.app.db.database import SessionLocal
from backend.app.main import app
from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.incident import Incident
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.simulation_run import SimulationRun
from backend.app.models.user import User


client = TestClient(app)


def test_reset_removes_only_simulation_data_and_allows_another_run():
    db = SessionLocal()

    try:
        user = User(
            email=f"simulation-reset-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )
        db.add(user)
        db.flush()

        project = Project(
            name=f"Simulation reset test {uuid4()}",
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

        unrelated_incident = Incident(
            project_id=project.id,
            title="Unrelated incident",
            description="Must survive simulation cleanup.",
            severity="low",
            status="open",
            detected_at=datetime.now(timezone.utc),
        )
        db.add(unrelated_incident)

        unrelated_timestamp = datetime.now(timezone.utc) - timedelta(hours=2)
        unrelated_metric = MetricEvent(
            service_id=service.id,
            timestamp=unrelated_timestamp,
            name="unrelated_metric",
            value=42,
        )
        unrelated_log = LogEvent(
            service_id=service.id,
            timestamp=unrelated_timestamp,
            level="INFO",
            message="Unrelated log event",
        )
        unrelated_deployment = DeploymentEvent(
            service_id=service.id,
            timestamp=unrelated_timestamp,
            version="unrelated-v1",
            description="Unrelated deployment event",
        )
        db.add_all([
            unrelated_metric,
            unrelated_log,
            unrelated_deployment,
        ])
        db.commit()

        headers = {
            "Authorization": f"Bearer {create_access_token(str(user.id))}"
        }
        base_path = f"/api/projects/{project.id}/simulation"

        run_response = client.post(
            f"{base_path}/bad-deployment",
            headers=headers,
        )

        assert run_response.status_code == 200
        simulated_incident_id = run_response.json()["incident_id"]
        assert simulated_incident_id is not None

        simulation_run = (
            db.query(SimulationRun)
            .filter(SimulationRun.project_id == project.id)
            .one()
        )
        simulation_run_id = simulation_run.id
        metric_event_ids = simulation_run.metric_event_ids
        log_event_ids = simulation_run.log_event_ids
        deployment_event_ids = simulation_run.deployment_event_ids

        reset_response = client.post(
            f"{base_path}/reset",
            headers=headers,
        )

        assert reset_response.status_code == 200
        assert reset_response.json() == {
            "status": "reset",
            "deleted_run_id": str(simulation_run_id),
        }

        db.expire_all()

        assert db.get(SimulationRun, simulation_run_id) is None
        assert db.get(Incident, simulated_incident_id) is None
        assert (
            db.query(MetricEvent)
            .filter(MetricEvent.id.in_(metric_event_ids))
            .count()
            == 0
        )
        assert (
            db.query(LogEvent)
            .filter(LogEvent.id.in_(log_event_ids))
            .count()
            == 0
        )
        assert (
            db.query(DeploymentEvent)
            .filter(DeploymentEvent.id.in_(deployment_event_ids))
            .count()
            == 0
        )

        assert db.get(Incident, unrelated_incident.id) is not None
        assert db.get(MetricEvent, unrelated_metric.id) is not None
        assert db.get(LogEvent, unrelated_log.id) is not None
        assert db.get(DeploymentEvent, unrelated_deployment.id) is not None

        rerun_response = client.post(
            f"{base_path}/bad-deployment",
            headers=headers,
        )

        assert rerun_response.status_code == 200
        assert rerun_response.json()["incident_id"] is not None

        cleanup_response = client.post(
            f"{base_path}/reset",
            headers=headers,
        )
        assert cleanup_response.status_code == 200

    finally:
        db.close()
