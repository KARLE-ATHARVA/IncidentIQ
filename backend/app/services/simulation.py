from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.evidence_item import EvidenceItem
from backend.app.models.historical_incident import HistoricalIncident
from backend.app.models.historical_incident_embedding import (
    HistoricalIncidentEmbedding,
)
from backend.app.models.incident import Incident
from backend.app.models.investigation import Investigation
from backend.app.models.investigation_result import InvestigationResult
from backend.app.models.investigation_result_evidence import (
    InvestigationResultEvidence,
)
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent
from backend.app.models.simulation_run import SimulationRun
from backend.app.schemas.deployment_event import DeploymentEventCreate
from backend.app.schemas.log_event import LogEventCreate
from backend.app.schemas.metric_event import MetricEventCreate
from backend.app.services.incident_pipeline import (
    process_metric_event_for_incident,
)
from backend.app.services.telemetry import (
    create_deployment_event,
    create_log_event,
    create_metric_event,
)


ACTIVE_SIMULATION_STATUSES = {
    "running",
    "incident_detected",
}


def get_active_simulation_run(
    db: Session,
    project_id: UUID,
) -> SimulationRun | None:
    """
    Return the most recent active simulation for a project.

    A simulation remains active after an incident is detected until
    the user explicitly resets the simulation.
    """
    return (
        db.query(SimulationRun)
        .filter(
            SimulationRun.project_id == project_id,
            SimulationRun.status.in_(ACTIVE_SIMULATION_STATUSES),
        )
        .order_by(SimulationRun.started_at.desc())
        .first()
    )


def run_bad_deployment_simulation(
    db: Session,
    project_id: UUID,
    service_id: UUID,
) -> tuple[SimulationRun, Incident | None]:
    """
    Generate a bad-deployment scenario and process it through
    the existing IncidentIQ incident pipeline.

    The simulator generates telemetry only. Detection, correlation,
    incident formation, and incident persistence remain owned by
    the existing IncidentIQ pipeline.
    """

    active_run = get_active_simulation_run(
        db=db,
        project_id=project_id,
    )

    if active_run is not None:
        raise ValueError(
            "A simulation is already active for this project. "
            "Reset the current simulation before starting another one."
        )

    now = datetime.now(timezone.utc)

    simulation_run = SimulationRun(
        project_id=project_id,
        service_id=service_id,
        scenario="bad-deployment",
        status="running",
        started_at=now,
        metric_event_ids=[],
        log_event_ids=[],
        deployment_event_ids=[],
    )

    db.add(simulation_run)
    db.commit()
    db.refresh(simulation_run)

    try:
        # -----------------------------------------------------
        # Generate normal baseline telemetry
        # -----------------------------------------------------

        normal_values = [
            100,
            101,
            99,
            100,
            102,
            98,
            101,
            100,
            99,
            100,
            101,
            100,
            98,
            102,
            100,
            99,
            101,
            100,
            102,
            99,
        ]

        for index, value in enumerate(normal_values):
            timestamp = now - timedelta(minutes=26 - index)

            metric_event = create_metric_event(
                db=db,
                service_id=service_id,
                data=MetricEventCreate(
                    timestamp=timestamp,
                    name="checkout_latency",
                    value=value,
                ),
            )

            simulation_run.metric_event_ids = [
                *simulation_run.metric_event_ids,
                metric_event.id,
            ]

        # -----------------------------------------------------
        # Generate bad deployment
        # -----------------------------------------------------

        deployment_time = now - timedelta(minutes=2)

        deployment_event = create_deployment_event(
            db=db,
            service_id=service_id,
            data=DeploymentEventCreate(
                timestamp=deployment_time,
                version="v2.4.0",
                description=(
                    "Deployed checkout payment integration changes."
                ),
            ),
        )

        simulation_run.deployment_event_ids = [
            *simulation_run.deployment_event_ids,
            deployment_event.id,
        ]

        # -----------------------------------------------------
        # Generate anomalous telemetry
        # -----------------------------------------------------

        anomaly_values = [160, 165, 162, 168, 170]

        for index, value in enumerate(anomaly_values):
            timestamp = now - timedelta(minutes=6 - index)

            metric_event = create_metric_event(
                db=db,
                service_id=service_id,
                data=MetricEventCreate(
                    timestamp=timestamp,
                    name="checkout_latency",
                    value=value,
                ),
            )

            simulation_run.metric_event_ids = [
                *simulation_run.metric_event_ids,
                metric_event.id,
            ]

        # -----------------------------------------------------
        # Generate application error
        # -----------------------------------------------------

        log_event = create_log_event(
            db=db,
            service_id=service_id,
            data=LogEventCreate(
                timestamp=now - timedelta(seconds=30),
                level="ERROR",
                message=(
                    "Checkout requests are timing out while calling "
                    "payment service."
                ),
            ),
        )

        simulation_run.log_event_ids = [
            *simulation_run.log_event_ids,
            log_event.id,
        ]

        # -----------------------------------------------------
        # Generate current anomalous metric
        # -----------------------------------------------------

        current_metric = create_metric_event(
            db=db,
            service_id=service_id,
            data=MetricEventCreate(
                timestamp=now,
                name="checkout_latency",
                value=175,
            ),
        )

        simulation_run.metric_event_ids = [
            *simulation_run.metric_event_ids,
            current_metric.id,
        ]

        # -----------------------------------------------------
        # Existing IncidentIQ pipeline
        #
        # Detection -> Correlation -> Incident Formation
        # -> Incident Persistence
        # -----------------------------------------------------

        incident = process_metric_event_for_incident(
            db=db,
            metric_event_id=current_metric.id,
        )

        simulation_run.status = (
            "incident_detected"
            if incident is not None
            else "completed"
        )

        simulation_run.completed_at = datetime.now(timezone.utc)

        if incident is not None:
            simulation_run.incident_id = incident.id

        db.commit()
        db.refresh(simulation_run)

        return simulation_run, incident

    except Exception:
        simulation_run.status = "failed"
        simulation_run.completed_at = datetime.now(timezone.utc)

        db.commit()

        raise


def get_simulation_state(
    db: Session,
    project_id: UUID,
) -> SimulationRun | None:
    """
    Return the currently active simulation for a project.
    """
    return get_active_simulation_run(
        db=db,
        project_id=project_id,
    )


def reset_simulation(
    db: Session,
    project_id: UUID,
) -> SimulationRun | None:
    """
    Remove the currently active simulation and only the records
    generated by that simulation.

    Deletion order respects the foreign-key dependencies between:

        InvestigationResultEvidence
            ↓
        InvestigationResult
            ↓
        Investigation
            ↓
        HistoricalIncidentEmbedding
            ↓
        HistoricalIncident
            ↓
        EvidenceItem
            ↓
        Incident
            ↓
        Telemetry
            ↓
        SimulationRun
    """

    simulation_run = get_active_simulation_run(
        db=db,
        project_id=project_id,
    )

    if simulation_run is None:
        return None

    incident_id = simulation_run.incident_id

    # ---------------------------------------------------------
    # Incident-related cleanup
    # ---------------------------------------------------------

    if incident_id is not None:

        # SimulationRun references the incident that the simulator's
        # telemetry caused the existing pipeline to create. Detach that
        # reference before deleting the incident so PostgreSQL can enforce
        # the foreign key throughout the cleanup transaction.
        simulation_run.incident_id = None
        db.flush()

        # -----------------------------------------------------
        # Historical knowledge
        #
        # A resolved simulated incident may have been converted
        # into HistoricalIncident + HistoricalIncidentEmbedding.
        #
        # Delete the embedding first because it references the
        # historical incident.
        # -----------------------------------------------------

        historical_incident = (
            db.query(HistoricalIncident)
            .filter(
                HistoricalIncident.incident_id == incident_id
            )
            .first()
        )

        if historical_incident is not None:

            db.query(HistoricalIncidentEmbedding).filter(
                HistoricalIncidentEmbedding.historical_incident_id
                == historical_incident.id
            ).delete(
                synchronize_session=False
            )

            db.delete(historical_incident)
            db.flush()

        # -----------------------------------------------------
        # Investigation results
        # -----------------------------------------------------

        result_ids = [
            result.id
            for result in (
                db.query(InvestigationResult)
                .join(
                    Investigation,
                    InvestigationResult.investigation_id
                    == Investigation.id,
                )
                .filter(
                    Investigation.incident_id == incident_id,
                )
                .all()
            )
        ]

        # -----------------------------------------------------
        # Investigation result evidence links
        # -----------------------------------------------------

        if result_ids:
            db.query(InvestigationResultEvidence).filter(
                InvestigationResultEvidence.investigation_result_id.in_(
                    result_ids
                )
            ).delete(
                synchronize_session=False
            )

            # -------------------------------------------------
            # Investigation results
            # -------------------------------------------------

            db.query(InvestigationResult).filter(
                InvestigationResult.id.in_(result_ids)
            ).delete(
                synchronize_session=False
            )

        # -----------------------------------------------------
        # Investigations
        # -----------------------------------------------------

        db.query(Investigation).filter(
            Investigation.incident_id == incident_id
        ).delete(
            synchronize_session=False
        )

        # -----------------------------------------------------
        # Incident evidence
        # -----------------------------------------------------

        db.query(EvidenceItem).filter(
            EvidenceItem.incident_id == incident_id
        ).delete(
            synchronize_session=False
        )

        # -----------------------------------------------------
        # Incident
        # -----------------------------------------------------

        db.query(Incident).filter(
            Incident.id == incident_id
        ).delete(
            synchronize_session=False
        )

    # ---------------------------------------------------------
    # Delete ONLY telemetry generated by this simulation run
    # ---------------------------------------------------------

    if simulation_run.metric_event_ids:
        db.query(MetricEvent).filter(
            MetricEvent.id.in_(
                simulation_run.metric_event_ids
            )
        ).delete(
            synchronize_session=False
        )

    if simulation_run.log_event_ids:
        db.query(LogEvent).filter(
            LogEvent.id.in_(
                simulation_run.log_event_ids
            )
        ).delete(
            synchronize_session=False
        )

    if simulation_run.deployment_event_ids:
        db.query(DeploymentEvent).filter(
            DeploymentEvent.id.in_(
                simulation_run.deployment_event_ids
            )
        ).delete(
            synchronize_session=False
        )

    # ---------------------------------------------------------
    # Delete simulation run itself
    # ---------------------------------------------------------

    db.delete(simulation_run)
    db.commit()

    return simulation_run
