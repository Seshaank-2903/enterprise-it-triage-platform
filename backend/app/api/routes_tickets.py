from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.observability import trace_latency
from app.models.models import (
    Ticket,
    TicketHistory,
    TicketStatusEnum,
    AIReviewStatusEnum,
    PriorityEnum
)
from app.schemas.schemas import (
    TicketCreate,
    TicketResponse,
    TicketReviewAction,
    TicketHistoryResponse
)
from app.services.ai_service import AIService

router = APIRouter(prefix="/tickets", tags=["Tickets & Triage"])
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


@router.post("", response_model=TicketResponse, status_code=201)
def create_and_triage_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service)
):
    """Creates a new ticket and executes the guardrailed AI triage workflow."""
    with trace_latency("db_latency"):
        new_ticket = Ticket(
            title=payload.title,
            description=payload.description,
            priority=payload.priority or PriorityEnum.MEDIUM,
            ticket_status=TicketStatusEnum.OPEN,
            ai_review_status=AIReviewStatusEnum.NOT_REQUIRED
        )
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)

    # Run AI triage workflow
    processed_ticket = ai_service.triage_and_process_ticket(new_ticket, db)
    return processed_ticket


@router.get("", response_model=List[TicketResponse])
def list_tickets(
    ai_review_status: Optional[AIReviewStatusEnum] = Query(None),
    ticket_status: Optional[TicketStatusEnum] = Query(None),
    priority: Optional[PriorityEnum] = Query(None),
    db: Session = Depends(get_db)
):
    """Retrieves tickets with optional filtering by status and AI review state."""
    with trace_latency("db_latency"):
        query = db.query(Ticket)
        if ai_review_status:
            query = query.filter(Ticket.ai_review_status == ai_review_status)
        if ticket_status:
            query = query.filter(Ticket.ticket_status == ticket_status)
        if priority:
            query = query.filter(Ticket.priority == priority)
        return query.order_by(Ticket.created_at.desc()).all()


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    with trace_latency("db_latency"):
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("/{ticket_id}/history", response_model=List[TicketHistoryResponse])
def get_ticket_history(ticket_id: str, db: Session = Depends(get_db)):
    with trace_latency("db_latency"):
        history = (
            db.query(TicketHistory)
            .filter(TicketHistory.ticket_id == ticket_id)
            .order_by(TicketHistory.timestamp.desc())
            .all()
        )
    return history


@router.post("/{ticket_id}/review", response_model=TicketResponse)
def review_ai_ticket(
    ticket_id: str,
    action_payload: TicketReviewAction,
    db: Session = Depends(get_db)
):
    """Human-in-the-loop review endpoint for agents to Approve or Reject drafted AI responses."""
    with trace_latency("db_latency"):
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        old_state = {
            "ticket_status": ticket.ticket_status.value,
            "ai_review_status": ticket.ai_review_status.value,
            "ai_drafted_response": ticket.ai_drafted_response
        }

        action_norm = action_payload.action.strip().capitalize()
        if action_norm == "Approved":
            ticket.ai_review_status = AIReviewStatusEnum.APPROVED
            ticket.ticket_status = TicketStatusEnum.RESOLVED
            ticket.resolved_at = datetime.utcnow()
            if action_payload.edited_response:
                ticket.ai_drafted_response = action_payload.edited_response
        elif action_norm == "Rejected":
            ticket.ai_review_status = AIReviewStatusEnum.REJECTED
            ticket.ticket_status = TicketStatusEnum.IN_PROGRESS
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'Approved' or 'Rejected'")

        new_state = {
            "ticket_status": ticket.ticket_status.value,
            "ai_review_status": ticket.ai_review_status.value,
            "ai_drafted_response": ticket.ai_drafted_response
        }

        audit_entry = TicketHistory(
            ticket_id=ticket.id,
            previous_state=old_state,
            new_state=new_state,
            changed_by=action_payload.agent_id or "HUMAN_AGENT"
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(ticket)

    return ticket
