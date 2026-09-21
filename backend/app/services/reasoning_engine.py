from abc import ABC, abstractmethod

from backend.app.services.investigation_context import (
    InvestigationContext,
    InvestigationResultContext,
)


class ReasoningEngine(ABC):
    """
    Contract for IncidentIQ investigation reasoning engines.

    A reasoning engine receives structured investigation context
    and produces a validated investigation result context.

    Implementations must reason only from the supplied context.
    """

    @abstractmethod
    def generate(
        self,
        context: InvestigationContext,
    ) -> InvestigationResultContext:
        """
        Generate an evidence-backed investigation result.
        """
        raise NotImplementedError