import json
from datetime import datetime, timezone
from unittest.mock import patch
from urllib.error import URLError
from uuid import uuid4

import pytest

from backend.app.services.ai_reasoner import AIReasoner
from backend.app.services.investigation_context import (
    EvidenceContext,
    IncidentContext,
    InvestigationContext,
)


def create_context() -> InvestigationContext:
    service_id = uuid4()

    return InvestigationContext(
        incident=IncidentContext(
            incident_id=uuid4(),
            title="Checkout latency incident",
            description="Checkout latency increased unexpectedly.",
            severity="high",
            status="open",
            detected_at=datetime.now(timezone.utc),
            resolved_at=None,
        ),
        timeline_events=[
            {
                "id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "metric",
                "service_id": str(service_id),
                "title": "Checkout latency anomaly",
                "description": "Latency exceeded the historical baseline.",
                "source_id": str(uuid4()),
                "severity": None,
                "metadata": {"value": 175},
            }
        ],
        evidence_items=[
            EvidenceContext(
                evidence_id=uuid4(),
                source_type="telemetry",
                source_id=uuid4(),
                title="Latency telemetry",
                description="Telemetry supporting the incident.",
                collected_at=datetime.now(timezone.utc),
            )
        ],
        historical_incidents=[],
    )


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_ai_reasoner_generates_structured_result():
    context = create_context()

    evidence_id = context.evidence_items[0].evidence_id

    fake_response = {
        "response": json.dumps(
            {
                "hypothesis": (
                    "The checkout latency anomaly may be associated "
                    "with the affected service behavior."
                ),
                "confidence": 0.72,
                "reasoning": (
                    "The supplied telemetry shows abnormal latency "
                    "during the incident window."
                ),
                "supporting_evidence_ids": [str(evidence_id)],
                "alternative_explanations": [
                    "Database contention.",
                    "External dependency degradation.",
                ],
                "next_steps": [
                    "Inspect database latency.",
                    "Inspect dependent service health.",
                ],
            }
        )
    }

    with patch(
        "backend.app.services.ai_reasoner.urllib.request.urlopen",
        return_value=FakeResponse(fake_response),
    ):
        reasoner = AIReasoner()
        result = reasoner.generate(context)

    assert result.hypothesis.hypothesis.startswith(
        "The checkout latency anomaly"
    )
    assert result.hypothesis.confidence == 0.72
    assert result.hypothesis.supporting_evidence_ids == [evidence_id]
    assert len(result.hypothesis.alternative_explanations) == 2
    assert len(result.hypothesis.next_steps) == 2


def test_ai_reasoner_rejects_invalid_json():
    context = create_context()

    fake_response = {
        "response": "this is not valid JSON"
    }

    with patch(
        "backend.app.services.ai_reasoner.urllib.request.urlopen",
        return_value=FakeResponse(fake_response),
    ):
        reasoner = AIReasoner()

        with pytest.raises(ValueError, match="invalid investigation output"):
            reasoner.generate(context)


def test_ai_reasoner_rejects_empty_response():
    context = create_context()

    fake_response = {
        "response": ""
    }

    with patch(
        "backend.app.services.ai_reasoner.urllib.request.urlopen",
        return_value=FakeResponse(fake_response),
    ):
        reasoner = AIReasoner()

        with pytest.raises(
            ValueError,
            match="empty reasoning response",
        ):
            reasoner.generate(context)


def test_ai_reasoner_handles_ollama_connection_failure():
    context = create_context()

    with patch(
        "backend.app.services.ai_reasoner.urllib.request.urlopen",
        side_effect=URLError("connection refused"),
    ):
        reasoner = AIReasoner()

        with pytest.raises(
            RuntimeError,
            match="Unable to connect to the local Ollama service",
        ):
            reasoner.generate(context)


def test_ai_reasoner_rejects_empty_hypothesis():
    context = create_context()

    evidence_id = context.evidence_items[0].evidence_id

    fake_response = {
        "response": json.dumps(
            {
                "hypothesis": "",
                "confidence": 0.7,
                "reasoning": "Some reasoning.",
                "supporting_evidence_ids": [str(evidence_id)],
                "alternative_explanations": ["Another possibility."],
                "next_steps": ["Inspect additional telemetry."],
            }
        )
    }

    with patch(
        "backend.app.services.ai_reasoner.urllib.request.urlopen",
        return_value=FakeResponse(fake_response),
    ):
        reasoner = AIReasoner()

        with pytest.raises(
            ValueError,
            match="invalid investigation output",
        ):
            reasoner.generate(context)


def test_ai_reasoner_rejects_confidence_above_one():
    context = create_context()

    evidence_id = context.evidence_items[0].evidence_id

    fake_response = {
        "response": json.dumps(
            {
                "hypothesis": "A possible contributing factor.",
                "confidence": 1.5,
                "reasoning": "Some reasoning.",
                "supporting_evidence_ids": [str(evidence_id)],
                "alternative_explanations": ["Another possibility."],
                "next_steps": ["Inspect additional telemetry."],
            }
        )
    }

    with patch(
        "backend.app.services.ai_reasoner.urllib.request.urlopen",
        return_value=FakeResponse(fake_response),
    ):
        reasoner = AIReasoner()

        with pytest.raises(
            ValueError,
            match="invalid investigation output",
        ):
            reasoner.generate(context)


def test_ai_reasoner_rejects_missing_supporting_evidence():
    context = create_context()

    fake_response = {
        "response": json.dumps(
            {
                "hypothesis": "A possible contributing factor.",
                "confidence": 0.7,
                "reasoning": "Some reasoning.",
                "supporting_evidence_ids": [],
                "alternative_explanations": ["Another possibility."],
                "next_steps": ["Inspect additional telemetry."],
            }
        )
    }

    with patch(
        "backend.app.services.ai_reasoner.urllib.request.urlopen",
        return_value=FakeResponse(fake_response),
    ):
        reasoner = AIReasoner()

        with pytest.raises(
            ValueError,
            match="invalid investigation output",
        ):
            reasoner.generate(context)
