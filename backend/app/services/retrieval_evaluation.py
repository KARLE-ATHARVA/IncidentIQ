from dataclasses import dataclass
from uuid import UUID

from backend.app.services.historical_retrieval import (
    RetrievedHistoricalIncident,
)


@dataclass(frozen=True)
class RetrievalEvaluationCase:
    results: list[RetrievedHistoricalIncident]
    expected_historical_incident_id: UUID


@dataclass(frozen=True)
class RetrievalEvaluation:
    total_cases: int
    hits: int
    misses: int
    hit_rate: float
    mean_reciprocal_rank: float


def evaluate_retrieval_results(
    cases: list[RetrievalEvaluationCase],
) -> RetrievalEvaluation:
    """
    Evaluate whether the expected historical incident was retrieved.

    Hit rate measures whether the expected incident appears anywhere
    in the returned result set.

    Mean Reciprocal Rank measures how highly the expected incident
    was ranked.
    """

    hits = 0
    misses = 0
    reciprocal_ranks: list[float] = []

    for case in cases:
        expected_id = case.expected_historical_incident_id

        rank = None

        for index, result in enumerate(case.results, start=1):
            if result.historical_incident_id == expected_id:
                rank = index
                break

        if rank is None:
            misses += 1
        else:
            hits += 1
            reciprocal_ranks.append(1.0 / rank)

    total_cases = len(cases)

    hit_rate = (
        hits / total_cases
        if total_cases
        else 0.0
    )

    mean_reciprocal_rank = (
        sum(reciprocal_ranks) / hits
        if hits
        else 0.0
    )

    return RetrievalEvaluation(
        total_cases=total_cases,
        hits=hits,
        misses=misses,
        hit_rate=hit_rate,
        mean_reciprocal_rank=mean_reciprocal_rank,
    )
