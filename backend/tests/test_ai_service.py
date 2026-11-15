from unittest.mock import MagicMock
import pytest

from app.models.models import (
    Ticket,
    TicketStatusEnum,
    AIReviewStatusEnum,
    PriorityEnum
)
from app.services.ai_service import AIService


@pytest.fixture
def mock_chroma():
    client = MagicMock()
    collection = MagicMock()
    collection.count.return_value = 1
    collection.query.return_value = {
        "documents": [["To reset LDAP password, execute vault-cli rotate."]],
        "metadatas": [[{"title": "Access & Identity Guide", "url": "https://kb.corp/iam"}]]
    }
    client.get_or_create_collection.return_value = collection
    return client


@pytest.fixture
def mock_mistral():
    client = MagicMock()
    return client


def test_fallback_on_llm_failure(in_memory_db, mock_chroma, mock_mistral):
    """Verifies that an LLM timeout/failure defaults review status to Failed gracefully without crash."""
    mock_mistral.chat.complete.side_effect = TimeoutError("Mistral API Unreachable")

    service = AIService(chroma_client=mock_chroma, mistral_client=mock_mistral)
    ticket = Ticket(
        title="Laptop display flickering",
        description="Hardware problem with screen",
        priority=PriorityEnum.LOW
    )
    in_memory_db.add(ticket)
    in_memory_db.commit()

    processed_ticket = service.triage_and_process_ticket(ticket, in_memory_db)

    assert processed_ticket.ai_review_status == AIReviewStatusEnum.FAILED
    assert "Route manually" in processed_ticket.ai_drafted_response
    assert len(processed_ticket.history_entries) == 1
    assert processed_ticket.history_entries[0].changed_by == "SYSTEM_AI"


def test_deterministic_guardrail_forces_pending_for_high_priority(in_memory_db, mock_chroma, mock_mistral):
    """
    Business Guardrail: Even if LLM suggests can_auto_resolve=True,
    a High-Priority ticket MUST be forced to Pending human review.
    """
    mock_choice = MagicMock()
    mock_choice.message.content = """{
        "ai_triage_category": "Hardware",
        "suggested_priority": "High",
        "confidence": 0.99,
        "draft_response": "Deploying hot-swap machine.",
        "can_auto_resolve": true
    }"""
    mock_mistral.chat.complete.return_value = MagicMock(choices=[mock_choice])

    service = AIService(chroma_client=mock_chroma, mistral_client=mock_mistral)
    ticket = Ticket(
        title="Core Database SAN Offline",
        description="SAN disk array failure",
        priority=PriorityEnum.HIGH
    )
    in_memory_db.add(ticket)
    in_memory_db.commit()

    processed_ticket = service.triage_and_process_ticket(ticket, in_memory_db)

    assert processed_ticket.ai_review_status == AIReviewStatusEnum.PENDING
    assert processed_ticket.ticket_status == TicketStatusEnum.IN_PROGRESS
    assert len(processed_ticket.ai_citations) == 1
    assert processed_ticket.ai_citations[0]["title"] == "Access & Identity Guide"


def test_deterministic_guardrail_forces_pending_for_access_category(in_memory_db, mock_chroma, mock_mistral):
    """
    Business Guardrail: Any ticket categorized as 'Access' must ALWAYS be forced
    to Pending for security policy compliance.
    """
    mock_choice = MagicMock()
    mock_choice.message.content = """{
        "ai_triage_category": "Access",
        "suggested_priority": "Low",
        "confidence": 0.95,
        "draft_response": "Follow standard approval chain.",
        "can_auto_resolve": true
    }"""
    mock_mistral.chat.complete.return_value = MagicMock(choices=[mock_choice])

    service = AIService(chroma_client=mock_chroma, mistral_client=mock_mistral)
    ticket = Ticket(
        title="Grant access to AWS S3",
        description="Need read access to analytics logs",
        priority=PriorityEnum.LOW
    )
    in_memory_db.add(ticket)
    in_memory_db.commit()

    processed_ticket = service.triage_and_process_ticket(ticket, in_memory_db)

    assert processed_ticket.ai_review_status == AIReviewStatusEnum.PENDING
    assert processed_ticket.ai_triage_category == "Access"


def test_standard_ticket_auto_resolves_when_eligible(in_memory_db, mock_chroma, mock_mistral):
    """Standard low-risk ticket with high confidence can be automatically marked Resolved/Approved."""
    mock_choice = MagicMock()
    mock_choice.message.content = """{
        "ai_triage_category": "Software",
        "suggested_priority": "Low",
        "confidence": 0.92,
        "draft_response": "You can install Slack from the Self Service portal.",
        "can_auto_resolve": true
    }"""
    mock_mistral.chat.complete.return_value = MagicMock(choices=[mock_choice])

    service = AIService(chroma_client=mock_chroma, mistral_client=mock_mistral)
    ticket = Ticket(
        title="Install Slack desktop application",
        description="Need Slack for team communications",
        priority=PriorityEnum.LOW
    )
    in_memory_db.add(ticket)
    in_memory_db.commit()

    processed_ticket = service.triage_and_process_ticket(ticket, in_memory_db)

    assert processed_ticket.ai_review_status == AIReviewStatusEnum.APPROVED
    assert processed_ticket.ticket_status == TicketStatusEnum.RESOLVED
