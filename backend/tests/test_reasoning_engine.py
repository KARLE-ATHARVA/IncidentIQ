from uuid import uuid4

from backend.app.services.investigation_context import (
    IncidentContext,
    InvestigationContext,
    InvestigationHypothesis,
    InvestigationResultContext,
)
from backend.app.services.reasoning_engine import ReasoningEngine


class StubReasoningEngine(ReasoningEngine):
    def generate(
        self,
        context: InvestigationContext,
    ) -> InvestigationResultContext:
        evidence_id = uuid4()

        hypothesis = InvestigationHypothesis(
            hypothesis="The incident may be related to the observed service degradation.",
            confidence=0.5,
            reasoning="This is a controlled test implementation.",
            supporting_evidence_ids=[evidence_id],
            alternative_explanations=[
                "The degradation may have another underlying cause."
            ],
            next_steps=[
                "Inspect the available telemetry for additional evidence."
            ],
        )

        return InvestigationResultContext(
            investigation_id=uuid4(),
            incident_id=context.incident.incident_id,
            hypothesis=hypothesis,
        )


def build_context() -> InvestigationContext:
    incident_id = uuid4()

    incident = IncidentContext(
        incident_id=incident_id,
        title="Test incident",
        description="Controlled test incident.",
        severity="high",
        status="investigating",
        detected_at=None,
        resolved_at=None,
    )

    return InvestigationContext(
        incident=incident,
        timeline_events=[],
        evidence_items=[],
        historical_incidents=[],
    )


def test_reasoning_engine_can_be_implemented():
    engine = StubReasoningEngine()
    context = build_context()

    result = engine.generate(context)

    assert isinstance(result, InvestigationResultContext)
    assert result.incident_id == context.incident.incident_id
    assert result.hypothesis.hypothesis
    assert 0.0 <= result.hypothesis.confidence <= 1.0


def test_reasoning_engine_is_an_abstract_contract():
    assert ReasoningEngine.__abstractmethods__ == {"generate"}