import time
from datetime import datetime, timezone
from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.models.historical_incident import HistoricalIncident
from backend.app.models.historical_incident_embedding import (
    HistoricalIncidentEmbedding,
)
from backend.app.models.incident import Incident
from backend.app.models.project import Project
from backend.app.models.service import Service
from backend.app.models.user import User
from backend.app.services.historical_retrieval import (
    retrieve_similar_historical_incidents,
)


def make_embedding(index: int) -> list[float]:
    embedding = [0.0] * 384

    # Keep one dimension dominant while varying the candidates.
    embedding[0] = 1.0
    embedding[1] = (index % 10) / 10.0

    return embedding


def create_historical_incident(
    db,
    *,
    project_id,
    service_id,
    index,
):
    incident_id = uuid4()

    incident = Incident(
        id=incident_id,
        project_id=project_id,
        title=f"Retrieval Performance Incident {index}",
        description="Historical retrieval performance benchmark",
        severity="high",
        status="resolved",
        detected_at=datetime.now(timezone.utc),
        resolved_at=datetime.now(timezone.utc),
    )

    db.add(incident)
    db.flush()

    historical = HistoricalIncident(
        id=uuid4(),
        incident_id=incident_id,
        project_id=project_id,
        service_id=service_id,
        title=f"Historical checkout incident {index}",
        summary="Historical retrieval performance benchmark summary",
        symptoms="Checkout latency increased",
        root_cause="Database contention",
        resolution="Reduced database load",
        severity="high",
        occurred_at=datetime.now(timezone.utc),
        resolved_at=datetime.now(timezone.utc),
    )

    db.add(historical)
    db.flush()

    embedding = HistoricalIncidentEmbedding(
        historical_incident_id=historical.id,
        embedding=make_embedding(index),
        model_name="performance-benchmark",
        embedding_text=historical.title,
    )

    db.add(embedding)
    db.flush()

    return historical


def test_retrieval_performance():
    db = SessionLocal()

    try:
        user = User(
            email=f"retrieval-performance-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )
        db.add(user)
        db.flush()

        project = Project(
            name=f"Retrieval Performance Project {uuid4()}",
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

        candidate_count = 100

        for index in range(candidate_count):
            create_historical_incident(
                db,
                project_id=project.id,
                service_id=service.id,
                index=index,
            )

        db.commit()

        query_embedding = make_embedding(0)

        iteration_count = 100

        start_time = time.perf_counter()

        for _ in range(iteration_count):
            results = retrieve_similar_historical_incidents(
                db=db,
                project_id=project.id,
                query_embedding=query_embedding,
                top_k=5,
            )

        elapsed_seconds = time.perf_counter() - start_time

        average_latency_ms = (
            elapsed_seconds / iteration_count
        ) * 1000

        throughput = iteration_count / elapsed_seconds

        print("\n" + "=" * 60)
        print("INCIDENTIQ HISTORICAL RETRIEVAL PERFORMANCE")
        print("=" * 60)
        print(f"Historical incidents:   {candidate_count}")
        print(f"Retrieval iterations:   {iteration_count}")
        print(f"Total time:             {elapsed_seconds:.4f} s")
        print(
            f"Average latency:        "
            f"{average_latency_ms:.2f} ms"
        )
        print(
            f"Throughput:             "
            f"{throughput:.2f} retrievals/s"
        )
        print(f"Results returned:       {len(results)}")
        print("=" * 60)

        assert len(results) == 5
        assert results[0].similarity_score >= results[-1].similarity_score
        assert elapsed_seconds > 0
        assert average_latency_ms > 0
        assert throughput > 0

    finally:
        db.rollback()
        db.close()
