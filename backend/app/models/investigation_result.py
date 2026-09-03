import uuid

from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, ForeignKey, Table,Index, Text
from backend.app.db.base import Base


class InvestigationResult(Base):
    __tablename__ = "investigation_results"

    __table_args__ = (
        Index(
            "ix_investigation_results_investigation",
            "investigation_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id"),
        nullable=False,
    )

    hypothesis: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    reasoning: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    next_steps: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    investigation = relationship(
        "Investigation",
        back_populates="results",
    )

    evidence_links = relationship(
        "InvestigationResultEvidence",
        back_populates="investigation_result",
    )