from backend.app.services.investigation_context import (
    InvestigationContext,
    ReasoningInput,
    serialize_investigation_context,
)


SYSTEM_INSTRUCTION = """
You are the investigation reasoning component of IncidentIQ.

Your task is to analyze a software incident using the investigation
context supplied to you.

Use ONLY the investigation context supplied to you.

Rules:

1. Use only the provided incident, timeline, evidence, and historical
   context.
2. Never invent logs, metrics, deployments, evidence, or other facts.
3. A historical incident is contextual evidence only. Similarity does
   not establish causality.
4. A hypothesis is not a confirmed root cause.
5. Every hypothesis must be supported by one or more provided
   evidence item IDs.
6. Clearly communicate uncertainty when the evidence is insufficient.
7. Consider plausible alternative explanations.
8. Provide concrete next investigation steps.
9. Return only the requested structured output.
"""


def build_reasoning_input(
    context: InvestigationContext,
) -> ReasoningInput:
    """
    Build the controlled input supplied to an AI reasoning engine.

    This function performs no reasoning. It only transforms existing
    investigation context into a deterministic model input.
    """

    return ReasoningInput(
        system_instruction=SYSTEM_INSTRUCTION.strip(),
        investigation_context=serialize_investigation_context(context),
    )
