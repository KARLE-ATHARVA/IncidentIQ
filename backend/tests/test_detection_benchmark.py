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
from backend.app.services.retrieval_evaluation import (
    RetrievalEvaluationCase,
    evaluate_retrieval_results,
)


def create_historical_incident(
    db,
    *,
    project_id,
    service_id,
    title,
    embedding,
):
    incident_id = uuid4()

    incident = Incident(
        id=incident_id,
        project_id=project_id,
        title=title,
        description="Retrieval benchmark incident",
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
        title=title,
        summary="Retrieval benchmark summary",
        symptoms="Retrieval benchmark symptoms",
        root_cause="Retrieval benchmark root cause",
        resolution="Retrieval benchmark resolution",
        severity="high",
        occurred_at=datetime.now(timezone.utc),
        resolved_at=datetime.now(timezone.utc),
    )

    db.add(historical)
    db.flush()

    embedding_record = HistoricalIncidentEmbedding(
        historical_incident_id=historical.id,
        embedding=embedding,
        model_name="benchmark",
        embedding_text=title,
    )

    db.add(embedding_record)
    db.flush()

    return historical


def make_embedding(*values):
    embedding = [0.0] * 384

    for index, value in enumerate(values):
        embedding[index] = value

    return embedding


def test_real_retrieval_benchmark():
    db = SessionLocal()

    try:
        # ---------------------------------------------------------
        # Create benchmark user
        # ---------------------------------------------------------
        user = User(
            email=f"retrieval-benchmark-{uuid4()}@example.com",
            password_hash="test-password-hash",
        )

        db.add(user)
        db.flush()

        # ---------------------------------------------------------
        # Create two projects
        # ---------------------------------------------------------
        project = Project(
            name=f"Retrieval Benchmark Project {uuid4()}",
            owner_id=user.id,
        )

        db.add(project)
        db.flush()

        other_project = Project(
            name=f"Other Retrieval Project {uuid4()}",
            owner_id=user.id,
        )

        db.add(other_project)
        db.flush()

        # ---------------------------------------------------------
        # Create services
        # ---------------------------------------------------------
        service = Service(
            name="checkout",
            project_id=project.id,
        )

        db.add(service)
        db.flush()

        other_service = Service(
            name="checkout",
            project_id=other_project.id,
        )

        db.add(other_service)
        db.flush()

        # ---------------------------------------------------------
        # Query embedding
        # ---------------------------------------------------------
        query_embedding = make_embedding(
            1.0,
            0.0,
            0.0,
        )

        # ---------------------------------------------------------
        # Exact semantic match
        # ---------------------------------------------------------
        exact_match = create_historical_incident(
            db,
            project_id=project.id,
            service_id=service.id,
            title="Checkout latency incident",
            embedding=make_embedding(
                1.0,
                0.0,
                0.0,
            ),
        )

        # ---------------------------------------------------------
        # Related but different incident
        # ---------------------------------------------------------
        related_incident = create_historical_incident(
            db,
            project_id=project.id,
            service_id=service.id,
            title="Checkout timeout incident",
            embedding=make_embedding(
                0.8,
                0.6,
                0.0,
            ),
        )

        # ---------------------------------------------------------
        # Unrelated incident
        # ---------------------------------------------------------
        unrelated_incident = create_historical_incident(
            db,
            project_id=project.id,
            service_id=service.id,
            title="Authentication failure incident",
            embedding=make_embedding(
                0.0,
                0.0,
                1.0,
            ),
        )

        # ---------------------------------------------------------
        # Same embedding as query, but DIFFERENT project.
        #
        # This verifies that project scoping prevents this
        # incident from entering the result set.
        # ---------------------------------------------------------
        other_project_incident = create_historical_incident(
            db,
            project_id=other_project.id,
            service_id=other_service.id,
            title="Other project checkout incident",
            embedding=make_embedding(
                1.0,
                0.0,
                0.0,
            ),
        )

        db.commit()

        # ---------------------------------------------------------
        # Execute the REAL retrieval implementation
        # ---------------------------------------------------------
        results = retrieve_similar_historical_incidents(
            db=db,
            project_id=project.id,
            query_embedding=query_embedding,
            top_k=3,
        )

        # ---------------------------------------------------------
        # Evaluate retrieval
        # ---------------------------------------------------------
        evaluation = evaluate_retrieval_results(
            [
                RetrievalEvaluationCase(
                    results=results,
                    expected_historical_incident_id=exact_match.id,
                )
            ]
        )

        # ---------------------------------------------------------
        # Print benchmark report
        # ---------------------------------------------------------
        print("\n" + "=" * 60)
        print("INCIDENTIQ RETRIEVAL BENCHMARK")
        print("=" * 60)

        print(f"Returned results:  {len(results)}")

        for rank, result in enumerate(results, start=1):
            print(
                f"{rank}. {result.title} "
                f"(similarity={result.similarity_score:.3f})"
            )

        print("-" * 60)

        print(
            f"Expected match:    "
            f"{exact_match.title}"
        )

        print(
            f"Hits:              "
            f"{evaluation.hits}"
        )

        print(
            f"Misses:            "
            f"{evaluation.misses}"
        )

        print(
            f"Hit rate:          "
            f"{evaluation.hit_rate:.3f}"
        )

        print(
            f"MRR:               "
            f"{evaluation.mean_reciprocal_rank:.3f}"
        )

        print("=" * 60)

        # ---------------------------------------------------------
        # Core retrieval assertions
        # ---------------------------------------------------------

        # top_k=3 should return exactly three incidents
        # from the requested project.
        assert len(results) == 3

        # The exact semantic match should rank first.
        assert (
            results[0].historical_incident_id
            == exact_match.id
        )

        # Similarity should decrease as ranking progresses.
        assert (
            results[0].similarity_score
            > results[1].similarity_score
        )

        assert (
            results[1].similarity_score
            > results[2].similarity_score
        )

        # ---------------------------------------------------------
        # Retrieval evaluation assertions
        # ---------------------------------------------------------

        assert evaluation.total_cases == 1

        assert evaluation.hits == 1

        assert evaluation.misses == 0

        assert evaluation.hit_rate == 1.0

        assert evaluation.mean_reciprocal_rank == 1.0

        # ---------------------------------------------------------
        # Project isolation assertion
        # ---------------------------------------------------------

        returned_ids = {
            result.historical_incident_id
            for result in results
        }

        assert other_project_incident.id not in returned_ids

        # These should be present in the current project's results.
        assert related_incident.id in returned_ids
        assert unrelated_incident.id in returned_ids

    finally:
        db.rollback()
        db.close()