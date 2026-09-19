from sqlalchemy.orm import Session

from backend.app.models.historical_incident import HistoricalIncident
from backend.app.models.historical_incident_embedding import (
    HistoricalIncidentEmbedding,
)
from backend.app.services.embeddings import MODEL_NAME, generate_embedding


def build_embedding_text(
    historical_incident: HistoricalIncident,
) -> str:
    """
    Build the canonical text representation used for semantic retrieval.
    """

    root_cause = (
        historical_incident.root_cause
        if historical_incident.root_cause
        else "Unknown"
    )

    resolution = (
        historical_incident.resolution
        if historical_incident.resolution
        else "Unknown"
    )

    return (
        f"Historical Incident\n"
        f"Title: {historical_incident.title}\n"
        f"Summary: {historical_incident.summary}\n"
        f"Symptoms: {historical_incident.symptoms}\n"
        f"Root Cause: {root_cause}\n"
        f"Resolution: {resolution}"
    )


def create_historical_incident_embedding(
    db: Session,
    historical_incident: HistoricalIncident,
) -> HistoricalIncidentEmbedding:
    """
    Generate and persist an embedding for a historical incident.

    Each historical incident can have only one active embedding.
    """

    existing = (
        db.query(HistoricalIncidentEmbedding)
        .filter(
            HistoricalIncidentEmbedding.historical_incident_id
            == historical_incident.id
        )
        .first()
    )

    if existing is not None:
        raise ValueError(
            "An embedding already exists for this historical incident."
        )

    embedding_text = build_embedding_text(historical_incident)
    embedding = generate_embedding(embedding_text)

    historical_incident_embedding = HistoricalIncidentEmbedding(
        historical_incident_id=historical_incident.id,
        embedding=embedding,
        model_name=MODEL_NAME,
        embedding_text=embedding_text,
    )

    db.add(historical_incident_embedding)
    db.commit()
    db.refresh(historical_incident_embedding)

    return historical_incident_embedding