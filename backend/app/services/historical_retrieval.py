from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.historical_incident import HistoricalIncident
from backend.app.models.historical_incident_embedding import (
    HistoricalIncidentEmbedding,
)


DEFAULT_SIMILARITY_THRESHOLD = 0.65


@dataclass
class RetrievedHistoricalIncident:
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


def retrieve_similar_historical_incidents(
    db: Session,
    project_id: UUID,
    query_embedding: list[float],
    top_k: int = 5,
    service_id: UUID | None = None,
    similarity_threshold: float | None = None,
) -> list[RetrievedHistoricalIncident]:
    """
    Retrieve historically similar incidents within a project.

    Similarity is based on cosine similarity between embeddings.

    Retrieval flow:
        1. Retrieve candidate historical incidents.
        2. Calculate cosine similarity.
        3. Filter candidates below the similarity threshold.
        4. Rank remaining candidates by similarity.
        5. Return the top K results.
    """

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    if top_k > 20:
        raise ValueError("top_k cannot exceed 20.")

    if similarity_threshold is not None and not 0.0 <= similarity_threshold <= 1.0:
        raise ValueError("similarity_threshold must be between 0.0 and 1.0.")

    query = (
        db.query(
            HistoricalIncident,
            HistoricalIncidentEmbedding.embedding.cosine_distance(
                query_embedding
            ).label("distance"),
        )
        .join(
            HistoricalIncidentEmbedding,
            HistoricalIncidentEmbedding.historical_incident_id
            == HistoricalIncident.id,
        )
        .filter(
            HistoricalIncident.project_id == project_id,
        )
    )

    if service_id is not None:
        query = query.filter(
            HistoricalIncident.service_id == service_id,
        )

    rows = query.all()

    results: list[RetrievedHistoricalIncident] = []

    for historical_incident, distance in rows:
        similarity_score = max(
            0.0,
            min(
                1.0,
                1.0 - float(distance),
            ),
        )

        if (
            similarity_threshold is not None
            and similarity_score < similarity_threshold
        ):
            continue

        results.append(
            RetrievedHistoricalIncident(
                historical_incident_id=historical_incident.id,
                title=historical_incident.title,
                summary=historical_incident.summary,
                symptoms=historical_incident.symptoms,
                root_cause=historical_incident.root_cause,
                resolution=historical_incident.resolution,
                severity=historical_incident.severity,
                service_id=historical_incident.service_id,
                occurred_at=historical_incident.occurred_at,
                similarity_score=similarity_score,
            )
        )

    results.sort(
        key=lambda result: result.similarity_score,
        reverse=True,
    )

    return results[:top_k]