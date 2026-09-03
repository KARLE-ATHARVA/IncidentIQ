import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index,String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class MetricEvent(Base):
    __tablename__ = "metric_events"

    __table_args__ = (
        Index(
            "ix_metric_events_service_name_timestamp",
            "service_id",
            "name",
            "timestamp",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id"),
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    service = relationship(
        "Service",
        back_populates="metric_events",
    )