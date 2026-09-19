from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.evidence_item import EvidenceItem
from backend.app.models.incident import Incident
from backend.app.services.historical_retrieval import (
    DEFAULT_SIMILARITY_THRESHOLD,
    RetrievedHistoricalIncident,
)
from backend.app.services.incident_retrieval import retrieve_historical_context
from backend.app.services.timeline import reconstruct_incident_timeline
import json


@dataclass(frozen=True)
class IncidentContext:
    """
    Core operational context for an incident.

    This represents what the system knows about the incident itself.
    It does not represent a root-cause conclusion.
    """

    incident_id: UUID
    title: str
    description: str | None
    severity: str
    status: str
    detected_at: datetime
    resolved_at: datetime | None


@dataclass(frozen=True)
class EvidenceContext:
    """
    Evidence associated with an incident.

    Evidence remains traceable to its original telemetry source.
    """

    evidence_id: UUID
    source_type: str
    source_id: UUID
    title: str
    description: str
    collected_at: datetime


@dataclass(frozen=True)
class HistoricalIncidentContext:
    """
    A historically recorded incident retrieved as contextual knowledge.

    Similarity indicates relatedness, not causality.
    """

    historical_incident_id: UUID
    title: str
    summary: str
    symptoms: str
    root_cause: str | None
    resolution: str | None
    severity: str
    service_id: UUID | None
    occurred_at: datetime
    similarity_score: float


@dataclass(frozen=True)
class InvestigationContext:
    """
    Structured context supplied to the investigation/reasoning layer.

    The reasoning layer should consume this context rather than
    independently querying operational database tables.
    """

    incident: IncidentContext
    timeline_events: list[dict]
    evidence_items: list[EvidenceContext]
    historical_incidents: list[HistoricalIncidentContext]


def build_incident_context(
    incident: Incident,
) -> IncidentContext:
    """
    Convert an Incident database model into investigation context.
    """

    return IncidentContext(
        incident_id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        detected_at=incident.detected_at,
        resolved_at=incident.resolved_at,
    )


def build_evidence_context(
    evidence_items: list[EvidenceItem],
) -> list[EvidenceContext]:
    """
    Convert database evidence records into investigation context.
    """

    return [
        EvidenceContext(
            evidence_id=evidence.id,
            source_type=evidence.source_type,
            source_id=evidence.source_id,
            title=evidence.title,
            description=evidence.description,
            collected_at=evidence.collected_at,
        )
        for evidence in evidence_items
    ]


def build_historical_incident_context(
    historical_incidents: list[RetrievedHistoricalIncident],
) -> list[HistoricalIncidentContext]:
    """
    Convert retrieval results into investigation context.
    """

    return [
        HistoricalIncidentContext(
            historical_incident_id=incident.historical_incident_id,
            title=incident.title,
            summary=incident.summary,
            symptoms=incident.symptoms,
            root_cause=incident.root_cause,
            resolution=incident.resolution,
            severity=incident.severity,
            service_id=incident.service_id,
            occurred_at=incident.occurred_at,
            similarity_score=incident.similarity_score,
        )
        for incident in historical_incidents
    ]


def build_investigation_context(
    db: Session,
    incident: Incident,
    top_k: int = 5,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> InvestigationContext:
    """
    Assemble all evidence available for investigating an incident.

    Context sources:

        Incident
            ↓
        Timeline
            ↓
        Evidence
            ↓
        Historical retrieval

    This function only assembles evidence/context.

    It does not infer root cause or generate an investigation result.
    """

    start_time, end_time, timeline_events = reconstruct_incident_timeline(
        db=db,
        incident=incident,
    )

    evidence_items = (
        db.query(EvidenceItem)
        .filter(
            EvidenceItem.incident_id == incident.id,
            EvidenceItem.collected_at >= start_time,
            EvidenceItem.collected_at <= end_time,
        )
        .order_by(EvidenceItem.collected_at.asc())
        .all()
    )

    historical_incidents = retrieve_historical_context(
        db=db,
        incident=incident,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
    )

    return InvestigationContext(
        incident=build_incident_context(incident),
        timeline_events=[
            event.model_dump(mode="json")
            for event in timeline_events
        ],
        evidence_items=build_evidence_context(evidence_items),
        historical_incidents=build_historical_incident_context(
            historical_incidents
        ),
    )

def serialize_investigation_context(
    context: InvestigationContext,
) -> dict:
    """
    Convert InvestigationContext into a deterministic,
    JSON-compatible structure for the reasoning layer.

    This function does not generate conclusions.
    It only serializes existing evidence and context.
    """

    return {
        "incident": {
            "incident_id": str(context.incident.incident_id),
            "title": context.incident.title,
            "description": context.incident.description,
            "severity": context.incident.severity,
            "status": context.incident.status,
            "detected_at": context.incident.detected_at.isoformat(),
            "resolved_at": (
                context.incident.resolved_at.isoformat()
                if context.incident.resolved_at is not None
                else None
            ),
        },
        "timeline_events": [
            {
                "id": str(event["id"]),
                "timestamp": event["timestamp"],
                "event_type": event["event_type"],
                "service_id": str(event["service_id"]),
                "title": event["title"],
                "description": event["description"],
                "source_id": str(event["source_id"]),
                "severity": event["severity"],
                "metadata": event["metadata"],
            }
            for event in context.timeline_events
        ],
        "evidence_items": [
            {
                "evidence_id": str(evidence.evidence_id),
                "source_type": evidence.source_type,
                "source_id": str(evidence.source_id),
                "title": evidence.title,
                "description": evidence.description,
                "collected_at": evidence.collected_at.isoformat(),
            }
            for evidence in context.evidence_items
        ],
        "historical_incidents": [
            {
                "historical_incident_id": str(
                    historical.historical_incident_id
                ),
                "title": historical.title,
                "summary": historical.summary,
                "symptoms": historical.symptoms,
                "root_cause": historical.root_cause,
                "resolution": historical.resolution,
                "severity": historical.severity,
                "service_id": (
                    str(historical.service_id)
                    if historical.service_id is not None
                    else None
                ),
                "occurred_at": historical.occurred_at.isoformat(),
                "similarity_score": historical.similarity_score,
            }
            for historical in context.historical_incidents
        ],
    }

@dataclass(frozen=True)
class InvestigationHypothesis:
    """
    A possible explanation for an incident.

    This is a hypothesis, not a confirmed root cause.
    """

    hypothesis: str
    confidence: float
    reasoning: str
    supporting_evidence_ids: list[UUID]
    alternative_explanations: list[str]
    next_steps: list[str]

@dataclass(frozen=True)
class InvestigationResultContext:
    """
    Structured output produced by the investigation/reasoning layer.

    The result explicitly separates a hypothesis from evidence and
    from a confirmed root cause.
    """

    hypothesis: InvestigationHypothesis

@dataclass(frozen=True)
class ReasoningInput:
    """
    Controlled input supplied to the investigation reasoning engine.

    The reasoning engine receives serialized investigation context
    rather than direct database access.
    """

    system_instruction: str
    investigation_context: dict
def validate_investigation_hypothesis(
    hypothesis: InvestigationHypothesis,
) -> None:
    """
    Validate the structural constraints of an investigation hypothesis.
    """

    if not hypothesis.hypothesis.strip():
        raise ValueError(
            "Investigation hypothesis cannot be empty."
        )

    if not 0.0 <= hypothesis.confidence <= 1.0:
        raise ValueError(
            "Investigation confidence must be between 0.0 and 1.0."
        )

    if not hypothesis.reasoning.strip():
        raise ValueError(
            "Investigation reasoning cannot be empty."
        )

    if not hypothesis.supporting_evidence_ids:
        raise ValueError(
            "Investigation hypothesis must reference at least one "
            "supporting evidence item."
        )

    if any(
        not explanation.strip()
        for explanation in hypothesis.alternative_explanations
    ):
        raise ValueError(
            "Alternative explanations cannot contain empty values."
        )

    if any(
        not step.strip()
        for step in hypothesis.next_steps
    ):
        raise ValueError(
            "Next steps cannot contain empty values."
        )

def serialize_investigation_result(
    result: InvestigationResultContext,
) -> dict:
    """
    Convert an investigation result into a JSON-compatible structure.
    """

    validate_investigation_hypothesis(result.hypothesis)

    return {
        "hypothesis": result.hypothesis.hypothesis,
        "confidence": result.hypothesis.confidence,
        "reasoning": result.hypothesis.reasoning,
        "supporting_evidence_ids": [
            str(evidence_id)
            for evidence_id in result.hypothesis.supporting_evidence_ids
        ],
        "alternative_explanations": [
            explanation
            for explanation in result.hypothesis.alternative_explanations
        ],
        "next_steps": [
            step
            for step in result.hypothesis.next_steps
        ],
    }


def build_reasoning_input(
    context: InvestigationContext,
) -> ReasoningInput:
    """
    Build the controlled input consumed by the reasoning engine.

    This function does not perform reasoning and does not generate
    a root-cause conclusion.
    """

    serialized_context = serialize_investigation_context(
        context
    )

    system_instruction = (
        "You are an incident investigation reasoning engine. "
        "Analyze only the evidence and context provided to you. "
        "Do not invent telemetry, logs, deployments, historical incidents, "
        "or other facts that are not present in the provided context. "
        "Treat retrieved historical incidents as contextual evidence, "
        "not proof of causality. "
        "Treat the investigation hypothesis as a hypothesis, not a "
        "confirmed root cause. "
        "Every proposed hypothesis must reference supporting evidence "
        "from the provided evidence items. "
        "Consider alternative explanations when the evidence permits. "
        "Return uncertainty explicitly when the available evidence "
        "is insufficient."
    )

    return ReasoningInput(
        system_instruction=system_instruction,
        investigation_context=serialized_context,
    )

def render_reasoning_input_as_text(
    reasoning_input: ReasoningInput,
) -> str:
    """
    Render reasoning input as deterministic JSON text.

    JSON is used so that field names and evidence identifiers remain
    explicit and machine-readable.
    """

    payload = {
        "system_instruction": reasoning_input.system_instruction,
        "investigation_context": reasoning_input.investigation_context,
    }

    return json.dumps(
        payload,
        indent=2,
        sort_keys=True,
    )