import json
from urllib.error import URLError

import pytest
from pydantic import ValidationError

from backend.app.services.ai_reasoner import AIReasoner


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_ai_reasoner_rejects_malformed_json(monkeypatch):
    def fake_urlopen(request, timeout):
        return FakeResponse(
            {
                "response": "{this is not valid JSON",
            }
        )

    monkeypatch.setattr(
        "backend.app.services.ai_reasoner.urlopen",
        fake_urlopen,
    )

    reasoner = AIReasoner()

    with pytest.raises(json.JSONDecodeError):
        reasoner.generate(None)


def test_ai_reasoner_rejects_empty_response(monkeypatch):
    def fake_urlopen(request, timeout):
        return FakeResponse(
            {
                "response": "",
            }
        )

    monkeypatch.setattr(
        "backend.app.services.ai_reasoner.urlopen",
        fake_urlopen,
    )

    reasoner = AIReasoner()

    with pytest.raises(
        ValueError,
        match="Ollama returned an empty reasoning response",
    ):
        reasoner.generate(None)


def test_ai_reasoner_rejects_invalid_confidence(monkeypatch):
    invalid_output = {
        "hypothesis": "The deployment may have contributed to the incident.",
        "confidence": 1.7,
        "reasoning": "The model returned an invalid confidence value.",
        "supporting_evidence_ids": [],
        "alternative_explanations": [
            "The issue may have originated elsewhere."
        ],
        "next_steps": [
            "Inspect the deployment and surrounding telemetry."
        ],
    }

    def fake_urlopen(request, timeout):
        return FakeResponse(
            {
                "response": json.dumps(invalid_output),
            }
        )

    monkeypatch.setattr(
        "backend.app.services.ai_reasoner.urlopen",
        fake_urlopen,
    )

    reasoner = AIReasoner()

    with pytest.raises(ValidationError):
        reasoner.generate(None)


def test_ai_reasoner_handles_ollama_connection_failure(monkeypatch):
    def fake_urlopen(request, timeout):
        raise URLError("Connection refused")

    monkeypatch.setattr(
        "backend.app.services.ai_reasoner.urlopen",
        fake_urlopen,
    )

    reasoner = AIReasoner()

    with pytest.raises(
        RuntimeError,
        match="Unable to connect to the local Ollama service",
    ):
        reasoner.generate(None)