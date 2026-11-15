import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    Index
)
from sqlalchemy.orm import declarative_base, relationship

from app.models.enums import TicketStatusEnum, AIReviewStatusEnum, PriorityEnum

Base = declarative_base()


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Status & Priority Fields
    ticket_status = Column(
        Enum(TicketStatusEnum),
        default=TicketStatusEnum.OPEN,
        nullable=False,
        index=True
    )
    ai_review_status = Column(
        Enum(AIReviewStatusEnum),
        default=AIReviewStatusEnum.NOT_REQUIRED,
        nullable=False,
        index=True
    )
    priority = Column(
        Enum(PriorityEnum),
        default=PriorityEnum.MEDIUM,
        nullable=False,
        index=True
    )

    # AI Triage & RAG Fields
    ai_triage_category = Column(String(100), nullable=True, index=True)
    ai_drafted_response = Column(Text, nullable=True)
    ai_citations = Column(JSON, nullable=True, default=list)

    # Audit Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    history_entries = relationship(
        "TicketHistory",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketHistory.timestamp.desc()"
    )

    __table_args__ = (
        Index("ix_tickets_status_priority", "ticket_status", "priority"),
    )


class TicketHistory(Base):
    __tablename__ = "ticket_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_state = Column(JSON, nullable=False)
    new_state = Column(JSON, nullable=False)
    changed_by = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    ticket = relationship("Ticket", back_populates="history_entries")
