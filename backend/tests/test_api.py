from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.models import Ticket, TicketStatusEnum, AIReviewStatusEnum, PriorityEnum

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_export_csv_empty(in_memory_db):
    app.dependency_overrides[get_db] = lambda: in_memory_db
    response = client.get("/api/reports/metrics/export-csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "category,total_tickets" in response.text
    app.dependency_overrides.clear()


def test_export_csv_with_data(in_memory_db):
    app.dependency_overrides[get_db] = lambda: in_memory_db
    t = Ticket(
        title="Test Ticket",
        description="Test Description",
        ai_triage_category="Hardware",
        ticket_status=TicketStatusEnum.RESOLVED,
        ai_review_status=AIReviewStatusEnum.APPROVED,
        priority=PriorityEnum.MEDIUM
    )
    in_memory_db.add(t)
    in_memory_db.commit()

    response = client.get("/api/reports/metrics/export-csv")
    assert response.status_code == 200
    assert "Hardware" in response.text
    app.dependency_overrides.clear()


def test_list_tickets_and_filter(in_memory_db):
    app.dependency_overrides[get_db] = lambda: in_memory_db
    t = Ticket(
        title="VPN Issue",
        description="Cannot connect to VPN",
        ticket_status=TicketStatusEnum.OPEN,
        ai_review_status=AIReviewStatusEnum.PENDING,
        priority=PriorityEnum.HIGH
    )
    in_memory_db.add(t)
    in_memory_db.commit()

    res = client.get("/api/tickets?ai_review_status=Pending")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "VPN Issue"
    assert data[0]["ai_review_status"] == "Pending"
    app.dependency_overrides.clear()


def test_review_ticket_approval(in_memory_db):
    app.dependency_overrides[get_db] = lambda: in_memory_db
    t = Ticket(
        title="Screen replacement",
        description="Cracked glass",
        ticket_status=TicketStatusEnum.OPEN,
        ai_review_status=AIReviewStatusEnum.PENDING,
        priority=PriorityEnum.LOW,
        ai_drafted_response="Replace at kiosk"
    )
    in_memory_db.add(t)
    in_memory_db.commit()

    res = client.post(
        f"/api/tickets/{t.id}/review",
        json={"action": "Approved", "agent_id": "test_agent"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ai_review_status"] == "Approved"
    assert data["ticket_status"] == "Resolved"
    assert data["resolved_at"] is not None

    # Check history audit entry
    hist_res = client.get(f"/api/tickets/{t.id}/history")
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert len(hist) == 1
    assert hist[0]["changed_by"] == "test_agent"
    app.dependency_overrides.clear()
