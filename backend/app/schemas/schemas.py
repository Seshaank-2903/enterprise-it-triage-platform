from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import TicketStatusEnum, AIReviewStatusEnum, PriorityEnum


class CitationItem(BaseModel):
    title: str = Field(description="Title of IT doc source")
    url: str = Field(description="Canonical documentation URL")


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=5)
    priority: Optional[PriorityEnum] = Field(default=PriorityEnum.MEDIUM)


class TicketReviewAction(BaseModel):
    action: str = Field(description="'Approved' or 'Rejected'")
    edited_response: Optional[str] = None
    agent_id: Optional[str] = "agent_human_in_loop"


class TicketHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    previous_state: dict
    new_state: dict
    changed_by: str
    timestamp: datetime


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    ticket_status: TicketStatusEnum
    ai_review_status: AIReviewStatusEnum
    priority: PriorityEnum
    ai_triage_category: Optional[str] = None
    ai_drafted_response: Optional[str] = None
    ai_citations: List[CitationItem] = []
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None


class LLMTriageOutput(BaseModel):
    ai_triage_category: str = Field(description="Target category: Access, Hardware, Software, Network, or Other")
    suggested_priority: PriorityEnum = Field(description="Inferred severity level")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    draft_response: str = Field(description="Empathetic, actionable drafted resolution for the user")
    can_auto_resolve: bool = Field(description="Whether issue is standard enough to resolve without approval")


class ReportCategoryMetric(BaseModel):
    category: str
    total: int
    avg_hours: float
    pending_reviews: int
