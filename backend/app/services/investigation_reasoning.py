from backend.app.services.investigation_context import (
    InvestigationContext,
    InvestigationHypothesis,
    InvestigationResultContext,
)
from backend.app.services.reasoning_engine import ReasoningEngine


class DeterministicReasoner(ReasoningEngine):
    """
    Deterministic investigation reasoning engine.

    This implementation uses explicit rules over the supplied
    investigation context. It serves as the baseline reasoning
    implementation before introducing an AI-based reasoner.

    It does not claim a confirmed root cause.
    """

    def generate(
        self,
        context: InvestigationContext,
    ) -> InvestigationResultContext:
        """
        Generate an evidence-backed investigation result.
        """

        if not context.evidence_items:
            raise ValueError(
                "Cannot generate an investigation result without evidence."
            )

        evidence_ids = [
            evidence.evidence_id
            for evidence in context.evidence_items
        ]

        deployment_events = [
            event
            for event in context.timeline_events
            if event["event_type"] == "deployment"
        ]

        error_events = [
            event
            for event in context.timeline_events
            if event["event_type"] == "log"
            and event.get("severity", "").lower()
            in {"error", "critical"}
        ]

        metric_events = [
            event
            for event in context.timeline_events
            if event["event_type"] == "metric"
        ]

        if deployment_events and error_events and metric_events:
            hypothesis = (
                "A recent deployment may have contributed to the "
                "observed incident behavior."
            )

            reasoning = (
                "The investigation context contains a metric signal "
                "associated with the incident, a deployment within the "
                "incident timeline, and an error-level log event. "
                "These signals are temporally related, but the available "
                "evidence does not establish the deployment as a confirmed "
                "root cause."
            )

            confidence = 0.70

            alternative_explanations = [
                "External dependency or payment-provider degradation.",
                "Database or infrastructure contention.",
            ]

            next_steps = [
                "Compare application behavior before and after the deployment.",
                "Inspect the deployment changes associated with the affected service.",
                "Inspect external dependency latency and error rates.",
            ]

        elif error_events and metric_events:
            hypothesis = (
                "The observed metric anomaly may be associated with "
                "the recorded application errors."
            )

            reasoning = (
                "The timeline contains both an anomalous metric signal "
                "and error-level log events within the investigation window. "
                "The available evidence establishes temporal association "
                "but does not establish causality."
            )

            confidence = 0.60

            alternative_explanations = [
                "External dependency degradation.",
                "Infrastructure or database contention.",
            ]

            next_steps = [
                "Inspect the affected application logs in greater detail.",
                "Compare the metric against its historical baseline.",
                "Inspect dependent service health.",
            ]

        else:
            hypothesis = (
                "The available evidence indicates anomalous application "
                "behavior, but the current context is insufficient to "
                "identify a likely contributing cause."
            )

            reasoning = (
                "The investigation context contains incident and telemetry "
                "information, but it does not contain enough correlated "
                "signals to establish a strong causal hypothesis."
            )

            confidence = 0.35

            alternative_explanations = [
                "Insufficient telemetry.",
                "An unobserved external dependency issue.",
            ]

            next_steps = [
                "Collect additional application logs.",
                "Inspect service metrics around the incident window.",
                "Review recent operational changes.",
            ]

        return InvestigationResultContext(
            hypothesis=InvestigationHypothesis(
                hypothesis=hypothesis,
                confidence=confidence,
                reasoning=reasoning,
                supporting_evidence_ids=evidence_ids,
                alternative_explanations=alternative_explanations,
                next_steps=next_steps,
            )
        )


def generate_deterministic_investigation(
    context: InvestigationContext,
) -> InvestigationResultContext:
    """
    Backward-compatible helper for existing callers/tests.

    The actual implementation now lives behind the ReasoningEngine
    abstraction.
    """

    return DeterministicReasoner().generate(context)
