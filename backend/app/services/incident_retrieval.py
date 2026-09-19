from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.incident import Incident
from backend.app.services.embeddings import generate_embedding
from backend.app.services.historical_retrieval import (
    DEFAULT_SIMILARITY_THRESHOLD,
    RetrievedHistoricalIncident,
    retrieve_similar_historical_incidents,
)


def build_incident_embedding_text(incident: Incident) -> str:
    return (
        f"Current Incident\n"
        f"Title: {incident.title}\n"
        f"Description: {incident.description or 'Unknown'}\n"
        f"Severity: {incident.severity}\n"
        f"Status: {incident.status}"
    )


def retrieve_historical_context(
    db: Session,
    incident: Incident,
    top_k: int = 5,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> list[RetrievedHistoricalIncident]:
    embedding_text = build_incident_embedding_text(incident)

    query_embedding = generate_embedding(embedding_text)

    return retrieve_similar_historical_incidents(
        db=db,
        project_id=incident.project_id,
        query_embedding=query_embedding,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
    )