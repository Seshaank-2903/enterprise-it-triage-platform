"""
Database Seed Script: Populates development/staging DB with initial tickets & history.
"""
import os
import sys
from datetime import datetime, timedelta

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend"))
sys.path.insert(0, backend_path)

from app.core.database import SessionLocal, engine
from app.models.models import Base, Ticket, TicketHistory, TicketStatusEnum, AIReviewStatusEnum, PriorityEnum

SAMPLE_TICKETS = [
    {
        "title": "AWS Production RDS Read-Only Access Request",
        "description": "Need access to analytics replica database in AWS us-east-1 for quarterly financial report reconciliation.",
        "ticket_status": TicketStatusEnum.IN_PROGRESS,
        "ai_review_status": AIReviewStatusEnum.PENDING,
        "priority": PriorityEnum.HIGH,
        "ai_triage_category": "Access",
        "ai_drafted_response": "Per policy KB-IAM-101, production database access requires dual approval from the Engineering Director and Data Security Officer. I have routed this request to SecOps.",
        "ai_citations": [{"title": "Enterprise Identity & Access Management (IAM) Policy", "url": "https://kb.enterprise.internal/iam/production-access"}],
        "created_at": datetime.utcnow() - timedelta(hours=2),
    },
    {
        "title": "Corporate VPN Connection Handshake Timeout",
        "description": "WireGuard client repeatedly drops connection on MacBook Pro when switching between home Wi-Fi and mobile hotspot.",
        "ticket_status": TicketStatusEnum.OPEN,
        "ai_review_status": AIReviewStatusEnum.PENDING,
        "priority": PriorityEnum.MEDIUM,
        "ai_triage_category": "Network",
        "ai_drafted_response": "Please flush the DNS cache and cycle the tunnel interface via 'sudo ifconfig utun3 down && sudo ifconfig utun3 up'. Ensure corporate DNS is set to 10.0.0.2.",
        "ai_citations": [{"title": "Corporate VPN & Network Troubleshooting Guide", "url": "https://kb.enterprise.internal/network/vpn-troubleshooting"}],
        "created_at": datetime.utcnow() - timedelta(hours=5),
    },
    {
        "title": "Laptop Screen Flickering and Green Tint",
        "description": "Dell XPS 15 display flickers intermittently when connected to external Thunderbolt dock.",
        "ticket_status": TicketStatusEnum.RESOLVED,
        "ai_review_status": AIReviewStatusEnum.APPROVED,
        "priority": PriorityEnum.MEDIUM,
        "ai_triage_category": "Hardware",
        "ai_drafted_response": "Hardware qualification confirmed. Please visit the Building C IT Kiosk between 09:00 - 17:00 for an immediate loaner swap.",
        "ai_citations": [{"title": "Hardware Replacement & Warranty Lifecycle SOP", "url": "https://kb.enterprise.internal/hardware/lifecycle-and-swaps"}],
        "created_at": datetime.utcnow() - timedelta(days=1),
        "resolved_at": datetime.utcnow() - timedelta(hours=22),
    },
    {
        "title": "Docker Desktop Enterprise License Renewal",
        "description": "Docker Desktop prompted that company subscription expires in 3 days. Need team license key applied.",
        "ticket_status": TicketStatusEnum.RESOLVED,
        "ai_review_status": AIReviewStatusEnum.APPROVED,
        "priority": PriorityEnum.LOW,
        "ai_triage_category": "Software",
        "ai_drafted_response": "Enterprise license key has been renewed automatically via Okta SSO. Please sign out and sign in back with corporate credentials.",
        "ai_citations": [{"title": "Self-Service Software Catalog", "url": "https://kb.enterprise.internal/software/self-service-catalog"}],
        "created_at": datetime.utcnow() - timedelta(days=2),
        "resolved_at": datetime.utcnow() - timedelta(days=1, hours=20),
    }
]


def seed_database():
    print("Initializing tables if not already present...")
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        existing = session.query(Ticket).count()
        if existing > 0:
            print(f"Database already contains {existing} tickets. Skipping seed.")
            return

        for item in SAMPLE_TICKETS:
            ticket = Ticket(**item)
            session.add(ticket)
            session.flush()

            history = TicketHistory(
                ticket_id=ticket.id,
                previous_state={"ticket_status": "Open", "ai_review_status": "Not Required"},
                new_state={"ticket_status": ticket.ticket_status.value, "ai_review_status": ticket.ai_review_status.value},
                changed_by="SEED_SYSTEM",
                timestamp=ticket.created_at
            )
            session.add(history)

        session.commit()
        print(f"Successfully seeded {len(SAMPLE_TICKETS)} tickets with audit trails!")
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
