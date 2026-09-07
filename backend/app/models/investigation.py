import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey,Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Investigation(Base):
    __tablename__ = "investigations"


    __table_args__ = (
        Index(
            "ix_investigations_incident_status",
            "incident_id",
            "status",
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

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    incident = relationship(
        "Incident",
        back_populates="investigations",
    )

    results = relationship(
        "InvestigationResult",
        back_populates="investigation",
    )
