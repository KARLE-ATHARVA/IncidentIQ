import pytest
from pydantic import ValidationError
from uuid import uuid4

from backend.app.schemas.ai_reasoning import AIInvestigationOutput


def valid_output() -> dict:
    return {
        "hypothesis": "Database connection pool exhaustion may have contributed to the incident.",
        "confidence": 0.82,
        "reasoning": (
            "The provided evidence shows increased checkout latency "
            "and timeout errors during the incident window."
        ),
        "supporting_evidence_ids": [uuid4()],
        "alternative_explanations": [
            "An external payment dependency may have contributed."
        ],
        "next_steps": [
            "Inspect database connection pool utilization during the incident."
        ],
    }


def test_valid_ai_investigation_output_is_accepted():
    output = AIInvestigationOutput.model_validate(valid_output())

    assert output.hypothesis
    assert output.confidence == 0.82
    assert len(output.supporting_evidence_ids) == 1
    assert len(output.alternative_explanations) == 1
    assert len(output.next_steps) == 1


def test_confidence_below_zero_is_rejected():
    data = valid_output()
    data["confidence"] = -0.1

    with pytest.raises(ValidationError):
        AIInvestigationOutput.model_validate(data)


def test_confidence_above_one_is_rejected():
    data = valid_output()
    data["confidence"] = 1.1

    with pytest.raises(ValidationError):
        AIInvestigationOutput.model_validate(data)


def test_missing_supporting_evidence_is_rejected():
    data = valid_output()
    data["supporting_evidence_ids"] = []

    with pytest.raises(ValidationError):
        AIInvestigationOutput.model_validate(data)


def test_missing_alternative_explanation_is_rejected():
    data = valid_output()
    data["alternative_explanations"] = []

    with pytest.raises(ValidationError):
        AIInvestigationOutput.model_validate(data)


def test_missing_next_step_is_rejected():
    data = valid_output()
    data["next_steps"] = []

    with pytest.raises(ValidationError):
        AIInvestigationOutput.model_validate(data)


def test_empty_hypothesis_is_rejected():
    data = valid_output()
    data["hypothesis"] = ""

    with pytest.raises(ValidationError):
        AIInvestigationOutput.model_validate(data)


def test_empty_reasoning_is_rejected():
    data = valid_output()
    data["reasoning"] = ""

    with pytest.raises(ValidationError):
        AIInvestigationOutput.model_validate(data)