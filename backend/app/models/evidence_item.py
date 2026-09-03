import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String,Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class EvidenceItem(Base):
    __tablename__ = "evidence_items"
    __table_args__ = (
        Index(
            "ix_evidence_items_incident_collected_at",
            "incident_id",
            "collected_at",
        ),
        Index(
            "ix_evidence_items_source",
            "source_type",
            "source_id",
        ),
    )


    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id"),
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    incident = relationship(
        "Incident",
        back_populates="evidence_items",
    )

    evidence_links = relationship(
        "InvestigationResultEvidence",
        back_populates="evidence_item",
    )