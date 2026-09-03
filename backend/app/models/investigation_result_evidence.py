import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class InvestigationResultEvidence(Base):
    __tablename__ = "investigation_result_evidence"

    investigation_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigation_results.id"),
        primary_key=True,
    )

    evidence_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_items.id"),
        primary_key=True,
    )

    investigation_result = relationship(
        "InvestigationResult",
        back_populates="evidence_links",
    )

    evidence_item = relationship(
        "EvidenceItem",
        back_populates="evidence_links",
    )