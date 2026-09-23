from datetime import datetime, timezone
from uuid import uuid4

import pytest

from backend.app.services.historical_retrieval import (
    RetrievedHistoricalIncident,
)
from backend.app.services.retrieval_evaluation import (
    RetrievalEvaluationCase,
    evaluate_retrieval_results,
)


def make_result(
    historical_incident_id,
    similarity_score,
):
    return RetrievedHistoricalIncident(
        historical_incident_id=historical_incident_id,
        title="Test incident",
        summary="Test summary",
        symptoms="Test symptoms",
        root_cause="Test root cause",
        resolution="Test resolution",
        severity="high",
        service_id=uuid4(),
        occurred_at=datetime.now(timezone.utc),
        similarity_score=similarity_score,
    )


def test_perfect_retrieval():
    expected_id = uuid4()

    cases = [
        RetrievalEvaluationCase(
            results=[
                make_result(expected_id, 0.95),
            ],
            expected_historical_incident_id=expected_id,
        ),
    ]

    evaluation = evaluate_retrieval_results(cases)

    assert evaluation.total_cases == 1
    assert evaluation.hits == 1
    assert evaluation.misses == 0
    assert evaluation.hit_rate == pytest.approx(1.0)
    assert evaluation.mean_reciprocal_rank == pytest.approx(1.0)


def test_expected_incident_at_second_position():
    expected_id = uuid4()

    cases = [
        RetrievalEvaluationCase(
            results=[
                make_result(uuid4(), 0.95),
                make_result(expected_id, 0.90),
            ],
            expected_historical_incident_id=expected_id,
        ),
    ]

    evaluation = evaluate_retrieval_results(cases)

    assert evaluation.hits == 1
    assert evaluation.misses == 0
    assert evaluation.hit_rate == pytest.approx(1.0)
    assert evaluation.mean_reciprocal_rank == pytest.approx(0.5)


def test_expected_incident_at_third_position():
    expected_id = uuid4()

    cases = [
        RetrievalEvaluationCase(
            results=[
                make_result(uuid4(), 0.95),
                make_result(uuid4(), 0.92),
                make_result(expected_id, 0.85),
            ],
            expected_historical_incident_id=expected_id,
        ),
    ]

    evaluation = evaluate_retrieval_results(cases)

    assert evaluation.hits == 1
    assert evaluation.misses == 0
    assert evaluation.hit_rate == pytest.approx(1.0)
    assert evaluation.mean_reciprocal_rank == pytest.approx(1 / 3)


def test_expected_incident_missing():
    expected_id = uuid4()

    cases = [
        RetrievalEvaluationCase(
            results=[
                make_result(uuid4(), 0.95),
                make_result(uuid4(), 0.90),
            ],
            expected_historical_incident_id=expected_id,
        ),
    ]

    evaluation = evaluate_retrieval_results(cases)

    assert evaluation.hits == 0
    assert evaluation.misses == 1
    assert evaluation.hit_rate == pytest.approx(0.0)
    assert evaluation.mean_reciprocal_rank == pytest.approx(0.0)


def test_mixed_retrieval_results():
    expected_a = uuid4()
    expected_b = uuid4()
    expected_c = uuid4()

    cases = [
        RetrievalEvaluationCase(
            results=[
                make_result(expected_a, 0.95),
                make_result(uuid4(), 0.80),
            ],
            expected_historical_incident_id=expected_a,
        ),
        RetrievalEvaluationCase(
            results=[
                make_result(uuid4(), 0.95),
                make_result(expected_b, 0.90),
            ],
            expected_historical_incident_id=expected_b,
        ),
        RetrievalEvaluationCase(
            results=[
                make_result(uuid4(), 0.95),
                make_result(uuid4(), 0.90),
            ],
            expected_historical_incident_id=expected_c,
        ),
    ]

    evaluation = evaluate_retrieval_results(cases)

    assert evaluation.total_cases == 3
    assert evaluation.hits == 2
    assert evaluation.misses == 1

    assert evaluation.hit_rate == pytest.approx(2 / 3)
    assert evaluation.mean_reciprocal_rank == pytest.approx(0.75)


def test_empty_cases_are_safe():
    evaluation = evaluate_retrieval_results([])

    assert evaluation.total_cases == 0
    assert evaluation.hits == 0
    assert evaluation.misses == 0
    assert evaluation.hit_rate == 0.0
    assert evaluation.mean_reciprocal_rank == 0.0
