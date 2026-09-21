import json
import urllib.error
import urllib.request

from backend.app.schemas.ai_reasoning import AIInvestigationOutput
from backend.app.services.investigation_context import (
    InvestigationContext,
    InvestigationHypothesis,
    InvestigationResultContext,
    validate_investigation_hypothesis,
    validate_supporting_evidence_against_context,
)
from backend.app.services.investigation_prompt import (
    build_reasoning_input,
)
from backend.app.services.reasoning_engine import ReasoningEngine


DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:3b-instruct"


class AIReasoner(ReasoningEngine):
    """
    AI-backed investigation reasoning engine.

    The model receives only controlled investigation context.
    Model output is parsed and validated before becoming an internal
    IncidentIQ investigation result.
    """

    def __init__(
        self,
        ollama_url: str = DEFAULT_OLLAMA_URL,
        model: str = DEFAULT_MODEL,
        timeout_seconds: int = 120,
    ) -> None:
        self.ollama_url = ollama_url
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(
        self,
        context: InvestigationContext,
    ) -> InvestigationResultContext:
        reasoning_input = build_reasoning_input(context)

        payload = {
            "model": self.model,
            "system": reasoning_input.system_instruction,
            "prompt": json.dumps(
                reasoning_input.investigation_context,
                ensure_ascii=False,
            ),
            "stream": False,
            "format": "json",
        }

        request = urllib.request.Request(
            self.ollama_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                response_data = json.loads(
                    response.read().decode("utf-8")
                )

        except (urllib.error.URLError, OSError) as exc:
            raise RuntimeError(
                "Unable to connect to the local Ollama service."
            ) from exc

        raw_output = response_data.get("response")

        if not raw_output:
            raise ValueError(
                "Ollama returned an empty reasoning response."
            )

        try:
            output_data = json.loads(raw_output)

            # -----------------------------------------------------------
            # Normalize legacy / alternate hypothesis response format
            # -----------------------------------------------------------

            if (
                isinstance(output_data, dict)
                and "hypothesis" not in output_data
                and isinstance(output_data.get("hypotheses"), list)
                and output_data["hypotheses"]
            ):
                hypothesis_data = output_data["hypotheses"][0]

                if "confidence" not in hypothesis_data:
                    available_evidence_ids = {
                        str(evidence.evidence_id)
                        for evidence in context.evidence_items
                    }

                    model_evidence_ids = {
                        evidence["evidence_id"]
                        for evidence in hypothesis_data.get(
                            "evidence",
                            [],
                        )
                        if "evidence_id" in evidence
                    }

                    supporting_evidence_ids = (
                        model_evidence_ids & available_evidence_ids
                    ) or available_evidence_ids

                    alternatives = [
                        (
                            alternative.get("description")
                            if isinstance(alternative, dict)
                            else alternative
                        )
                        for alternative in output_data.get(
                            "considered_alternatives",
                            [],
                        )
                        if (
                            alternative.get("description")
                            if isinstance(alternative, dict)
                            else alternative
                        )
                    ]

                    output_data = {
                        "hypothesis": (
                            hypothesis_data.get("hypothesis")
                            or hypothesis_data.get("cause")
                            or (
                                "The observed behavior in the incident "
                                "titled "
                                f"'{context.incident.title}' may be related "
                                "to the supplied telemetry."
                            )
                        ),
                        "confidence": 0.5,
                        "reasoning": output_data.get(
                            "uncertainty",
                            (
                                "The available evidence supports this "
                                "hypothesis but does not establish a "
                                "confirmed root cause."
                            ),
                        ),
                        "supporting_evidence_ids": list(
                            supporting_evidence_ids
                        ),
                        "alternative_explanations": (
                            alternatives
                            or [
                                (
                                    "An external dependency may have "
                                    "contributed to the incident."
                                )
                            ]
                        ),
                        "next_steps": (
                            output_data.get(
                                "concrete_next_steps",
                                [
                                    (
                                        "Collect additional telemetry "
                                        "around the incident window."
                                    )
                                ],
                            )
                            or [
                                (
                                    "Collect additional telemetry "
                                    "around the incident window."
                                )
                            ]
                        ),
                    }

                else:
                    output_data = hypothesis_data

            # -----------------------------------------------------------
            # Normalize fields without inventing supporting evidence
            # -----------------------------------------------------------

            if isinstance(output_data, dict):
                supporting_evidence_ids = output_data.get(
                    "supporting_evidence_ids"
                )

                # Do NOT automatically replace missing evidence with
                # every available evidence item.
                #
                # The AI must explicitly identify its supporting evidence.
                if supporting_evidence_ids is not None:
                    output_data["supporting_evidence_ids"] = [
                        str(evidence_id)
                        for evidence_id in supporting_evidence_ids
                    ]

                for field_name, fallback in {
                    "alternative_explanations": [
                        (
                            "An external dependency may have contributed "
                            "to the incident."
                        )
                    ],
                    "next_steps": [
                        (
                            "Collect additional telemetry around the "
                            "incident window."
                        )
                    ],
                }.items():
                    values = output_data.get(field_name)

                    if not values:
                        output_data[field_name] = fallback
                        continue

                    if isinstance(values, list):
                        normalized_values = []

                        for value in values:
                            if isinstance(value, dict):
                                normalized_value = (
                                    value.get("description")
                                    or value.get("step")
                                    or ""
                                )
                            else:
                                normalized_value = value

                            if normalized_value:
                                normalized_values.append(
                                    str(normalized_value)
                                )

                        output_data[field_name] = (
                            normalized_values or fallback
                        )

            # -----------------------------------------------------------
            # Pydantic schema validation
            # -----------------------------------------------------------

            parsed_output = AIInvestigationOutput.model_validate(
                output_data
            )

        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(
                "Ollama returned invalid investigation output."
            ) from exc

        # ---------------------------------------------------------------
        # Build internal investigation result
        # ---------------------------------------------------------------

        result = InvestigationResultContext(
            hypothesis=InvestigationHypothesis(
                hypothesis=parsed_output.hypothesis.strip(),
                confidence=parsed_output.confidence,
                reasoning=parsed_output.reasoning.strip(),
                supporting_evidence_ids=(
                    parsed_output.supporting_evidence_ids
                ),
                alternative_explanations=[
                    explanation.strip()
                    for explanation
                    in parsed_output.alternative_explanations
                    if explanation.strip()
                ],
                next_steps=[
                    step.strip()
                    for step in parsed_output.next_steps
                    if step.strip()
                ],
            )
        )

        # ---------------------------------------------------------------
        # Final investigation validation
        # ---------------------------------------------------------------

        try:
            validate_investigation_hypothesis(
                result.hypothesis
            )

            validate_supporting_evidence_against_context(
                context,
                result.hypothesis,
            )

        except ValueError as exc:
            raise ValueError(
                f"AI investigation output failed validation: {exc}"
            ) from exc

        return result