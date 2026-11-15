import io
from datetime import datetime
from typing import List
import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.observability import trace_latency
from app.models.models import Ticket, TicketStatusEnum
from app.schemas.schemas import ReportCategoryMetric

router = APIRouter(prefix="/reports", tags=["Analytics & Reports"])


@router.get("/summary", response_model=List[ReportCategoryMetric])
def get_reports_summary(db: Session = Depends(get_db)):
    """Provides categorized aggregate data for the frontend Recharts dashboard."""
    with trace_latency("db_latency"):
        tickets = db.query(
            Ticket.ai_triage_category,
            Ticket.ticket_status,
            Ticket.ai_review_status,
            Ticket.created_at,
            Ticket.resolved_at
        ).all()

    if not tickets:
        return [
            {"category": "Access", "total": 0, "avg_hours": 0.0, "pending_reviews": 0},
            {"category": "Hardware", "total": 0, "avg_hours": 0.0, "pending_reviews": 0},
            {"category": "Software", "total": 0, "avg_hours": 0.0, "pending_reviews": 0},
            {"category": "Network", "total": 0, "avg_hours": 0.0, "pending_reviews": 0},
        ]

    data = [
        {
            "category": t.ai_triage_category or "Other",
            "status": t.ticket_status.value,
            "ai_review_status": t.ai_review_status.value,
            "resolution_hours": (
                (t.resolved_at - t.created_at).total_seconds() / 3600.0
                if t.resolved_at and t.resolved_at > t.created_at
                else None
            ),
        }
        for t in tickets
    ]
    df = pd.DataFrame(data)

    metrics = []
    for cat, group in df.groupby("category"):
        avg_h = group["resolution_hours"].dropna().mean()
        metrics.append({
            "category": str(cat),
            "total": int(len(group)),
            "avg_hours": round(float(avg_h), 2) if pd.notnull(avg_h) else 0.0,
            "pending_reviews": int((group["ai_review_status"] == "Pending").sum())
        })

    return metrics


@router.get("/metrics/export-csv")
def export_ticket_metrics_csv(db: Session = Depends(get_db)):
    """
    Executes SQLAlchemy queries, performs advanced analytical aggregations in Pandas,
    and returns an in-memory streaming CSV download.
    """
    with trace_latency("db_latency"):
        tickets = db.query(
            Ticket.id,
            Ticket.ai_triage_category,
            Ticket.ticket_status,
            Ticket.ai_review_status,
            Ticket.priority,
            Ticket.created_at,
            Ticket.resolved_at
        ).all()

    if not tickets:
        header = "category,total_tickets,resolved_tickets,avg_resolution_hours,pending_ai_reviews,critical_tickets\n"
        return StreamingResponse(
            io.StringIO(header),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=ticket_metrics_report.csv"}
        )

    data = [
        {
            "id": t.id,
            "category": t.ai_triage_category or "Unassigned",
            "status": t.ticket_status.value,
            "ai_review_status": t.ai_review_status.value,
            "priority": t.priority.value,
            "created_at": t.created_at,
            "resolved_at": t.resolved_at,
            "resolution_hours": (
                (t.resolved_at - t.created_at).total_seconds() / 3600.0
                if t.resolved_at and t.resolved_at > t.created_at
                else None
            ),
        }
        for t in tickets
    ]
    df = pd.DataFrame(data)

    # Advanced Pandas KPI group computation
    agg_df = df.groupby("category").apply(
        lambda g: pd.Series({
            "total_tickets": int(len(g)),
            "resolved_tickets": int((g["status"] == TicketStatusEnum.RESOLVED.value).sum()),
            "avg_resolution_hours": (
                round(float(g["resolution_hours"].mean()), 2)
                if g["resolution_hours"].notnull().any()
                else 0.0
            ),
            "pending_ai_reviews": int((g["ai_review_status"] == "Pending").sum()),
            "critical_tickets": int((g["priority"] == "Critical").sum()),
        })
    ).reset_index()

    buffer = io.StringIO()
    agg_df.to_csv(buffer, index=False)
    buffer.seek(0)

    filename = f"ticket_metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
