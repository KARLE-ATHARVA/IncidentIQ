from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.deployment_event import DeploymentEvent
from backend.app.models.evidence_item import EvidenceItem
from backend.app.models.log_event import LogEvent
from backend.app.models.metric_event import MetricEvent


@dataclass(frozen=True)
class EvidenceInspection:
    """
    Fully resolved representation of an evidence item.

    EvidenceItem provides the investigation-level description.
    This object additionally resolves the original telemetry event
    referenced by source_type + source_id.
    """

    evidence_id: UUID
    incident_id: UUID

    source_type: str
    source_id: UUID

    title: str
    description: str
    collected_at: datetime

    service_id: UUID | None
    timestamp: datetime | None

    details: dict[str, Any]


def inspect_evidence(
    db: Session,
    evidence: EvidenceItem,
) -> EvidenceInspection:
    """
    Resolve an EvidenceItem to its original telemetry source.

    Supported source types:
        - metric
        - log
        - deployment
        - telemetry

    The source_id must resolve to an existing telemetry record.
    Evidence is never fabricated if the original source cannot
    be found.
    """

    source_type = evidence.source_type.lower().strip()

    # ------------------------------------------------------------------
    # Metric evidence
    # ------------------------------------------------------------------

    if source_type == "metric":
        metric = (
            db.query(MetricEvent)
            .filter(
                MetricEvent.id == evidence.source_id,
            )
            .first()
        )

        if metric is None:
            raise ValueError(
                "Metric source for evidence was not found."
            )

        return EvidenceInspection(
            evidence_id=evidence.id,
            incident_id=evidence.incident_id,
            source_type=evidence.source_type,
            source_id=evidence.source_id,
            title=evidence.title,
            description=evidence.description,
            collected_at=evidence.collected_at,
            service_id=metric.service_id,
            timestamp=metric.timestamp,
            details={
                "metric_name": metric.name,
                "value": metric.value,
            },
        )

    # ------------------------------------------------------------------
    # Log evidence
    # ------------------------------------------------------------------

    if source_type == "log":
        log = (
            db.query(LogEvent)
            .filter(
                LogEvent.id == evidence.source_id,
            )
            .first()
        )

        if log is None:
            raise ValueError(
                "Log source for evidence was not found."
            )

        return EvidenceInspection(
            evidence_id=evidence.id,
            incident_id=evidence.incident_id,
            source_type=evidence.source_type,
            source_id=evidence.source_id,
            title=evidence.title,
            description=evidence.description,
            collected_at=evidence.collected_at,
            service_id=log.service_id,
            timestamp=log.timestamp,
            details={
                "level": log.level,
                "message": log.message,
            },
        )

    # ------------------------------------------------------------------
    # Deployment evidence
    # ------------------------------------------------------------------

    if source_type == "deployment":
        deployment = (
            db.query(DeploymentEvent)
            .filter(
                DeploymentEvent.id == evidence.source_id,
            )
            .first()
        )

        if deployment is None:
            raise ValueError(
                "Deployment source for evidence was not found."
            )

        return EvidenceInspection(
            evidence_id=evidence.id,
            incident_id=evidence.incident_id,
            source_type=evidence.source_type,
            source_id=evidence.source_id,
            title=evidence.title,
            description=evidence.description,
            collected_at=evidence.collected_at,
            service_id=deployment.service_id,
            timestamp=deployment.timestamp,
            details={
                "version": deployment.version,
                "deployment_description": deployment.description,
            },
        )

    # ------------------------------------------------------------------
    # Generic telemetry fallback
    # ------------------------------------------------------------------

    if source_type == "telemetry":
        metric = (
            db.query(MetricEvent)
            .filter(
                MetricEvent.id == evidence.source_id,
            )
            .first()
        )

        if metric is not None:
            return EvidenceInspection(
                evidence_id=evidence.id,
                incident_id=evidence.incident_id,
                source_type=evidence.source_type,
                source_id=evidence.source_id,
                title=evidence.title,
                description=evidence.description,
                collected_at=evidence.collected_at,
                service_id=metric.service_id,
                timestamp=metric.timestamp,
                details={
                    "metric_name": metric.name,
                    "value": metric.value,
                },
            )

        log = (
            db.query(LogEvent)
            .filter(
                LogEvent.id == evidence.source_id,
            )
            .first()
        )

        if log is not None:
            return EvidenceInspection(
                evidence_id=evidence.id,
                incident_id=evidence.incident_id,
                source_type=evidence.source_type,
                source_id=evidence.source_id,
                title=evidence.title,
                description=evidence.description,
                collected_at=evidence.collected_at,
                service_id=log.service_id,
                timestamp=log.timestamp,
                details={
                    "level": log.level,
                    "message": log.message,
                },
            )

        deployment = (
            db.query(DeploymentEvent)
            .filter(
                DeploymentEvent.id == evidence.source_id,
            )
            .first()
        )

        if deployment is not None:
            return EvidenceInspection(
                evidence_id=evidence.id,
                incident_id=evidence.incident_id,
                source_type=evidence.source_type,
                source_id=evidence.source_id,
                title=evidence.title,
                description=evidence.description,
                collected_at=evidence.collected_at,
                service_id=deployment.service_id,
                timestamp=deployment.timestamp,
                details={
                    "version": deployment.version,
                    "deployment_description": deployment.description,
                },
            )

        raise ValueError(
            "Telemetry source for evidence was not found."
        )

    # ------------------------------------------------------------------
    # Unsupported source type
    # ------------------------------------------------------------------

    raise ValueError(
        f"Unsupported evidence source type: {evidence.source_type}."
    )