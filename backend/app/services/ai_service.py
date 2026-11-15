import json
import urllib.error
import urllib.request
from typing import List, Optional
import chromadb
try:
    import httpx
    _http_client = httpx.Client(
        timeout=httpx.Timeout(10.0, connect=3.0),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=50, keepalive_expiry=60.0)
    )
except ImportError:
    httpx = None
    _http_client = None

try:
    from mistralai import Mistral
except ImportError:
    Mistral = None

from app.core.config import settings
from app.core.observability import logger, trace_latency
from app.models.models import (
    Ticket,
    TicketHistory,
    TicketStatusEnum,
    AIReviewStatusEnum,
    PriorityEnum
)
from app.schemas.schemas import LLMTriageOutput


DEFAULT_KB_DOCS = [
    {
        "id": "doc-iam-01",
        "text": (
            "For Access and IAM requests, AWS IAM and Production Database privileges require approval "
            "from Security and Manager. Multi-factor authentication must be re-verified via Okta."
        ),
        "metadata": {
            "title": "Production Access & Identity Policy",
            "url": "https://kb.enterprise.internal/iam/production-access"
        }
    },
    {
        "id": "doc-vpn-02",
        "text": (
            "Network and VPN connection drops are commonly resolved by cycling WireGuard tunnel configs "
            "and verifying internal DNS 10.0.0.2."
        ),
        "metadata": {
            "title": "Corporate VPN & Network Troubleshooting",
            "url": "https://kb.enterprise.internal/network/vpn-troubleshooting"
        }
    },
    {
        "id": "doc-hw-03",
        "text": (
            "Hardware issues including laptop screen flickering, battery health below 80%, or keyboard failure "
            "qualify for immediate on-site hardware swap at the IT Kiosk."
        ),
        "metadata": {
            "title": "Employee Hardware Replacement Lifecycle",
            "url": "https://kb.enterprise.internal/hardware/lifecycle-and-swaps"
        }
    },
    {
        "id": "doc-soft-04",
        "text": (
            "Standard software applications (Slack, Zoom, IDEs, Docker Desktop) can be self-installed from "
            "Enterprise Self Service Portal without admin credentials."
        ),
        "metadata": {
            "title": "Self-Service Software Catalog",
            "url": "https://kb.enterprise.internal/software/self-service-catalog"
        }
    }
]


class AIService:
    def __init__(self, chroma_client: Optional[chromadb.Client] = None, mistral_client: Optional[object] = None):
        self._is_custom_mistral_injected = mistral_client is not None

        if chroma_client is not None:
            self.chroma = chroma_client
        else:
            self.chroma = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)

        self.collection = self.chroma.get_or_create_collection("enterprise_it_kb")
        self._seed_default_kb_if_empty()

        if mistral_client is not None:
            self.mistral = mistral_client
        elif Mistral is not None and settings.MISTRAL_API_KEY:
            self.mistral = Mistral(api_key=settings.MISTRAL_API_KEY)
        else:
            self.mistral = None

    def _seed_default_kb_if_empty(self):
        try:
            count = self.collection.count()
            if count == 0:
                self.collection.add(
                    ids=[d["id"] for d in DEFAULT_KB_DOCS],
                    documents=[d["text"] for d in DEFAULT_KB_DOCS],
                    metadatas=[d["metadata"] for d in DEFAULT_KB_DOCS]
                )
                logger.info("Initialized ChromaDB with standard Enterprise IT Knowledge Base documents.")
        except Exception as e:
            logger.warning(f"Could not seed default IT documentation: {e}")

    def retrieve_rag_context(self, query: str, top_k: int = 2) -> tuple[str, List[dict]]:
        """Retrieves verified context and extracts document title and URL citations."""
        with trace_latency("rag_latency"):
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )

        context_texts = []
        citations = []

        if results and results.get("documents") and results["documents"] and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") and results["metadatas"] else [{}] * len(docs)
            for doc, meta in zip(docs, metas):
                context_texts.append(doc)
                meta_dict = meta if isinstance(meta, dict) else {}
                citations.append({
                    "title": meta_dict.get("title", "Internal IT Document"),
                    "url": meta_dict.get("url", "https://kb.enterprise.internal/docs")
                })

        formatted_context = "\n---\n".join(context_texts) if context_texts else "No documentation found."
        return formatted_context, citations

    def _call_gemini_api(self, system_prompt: str, user_content: str) -> str:
        """Invokes Google AI Studio Gemini API with structured JSON output."""
        api_key = settings.GEMINI_API_KEY
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-flash-latest:generateContent?key={api_key}"
        )

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": f"{system_prompt}\n\nUser Ticket Inquiry:\n{user_content}"}
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
                "max_output_tokens": 500
            }
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            candidate = result["candidates"][0]["content"]["parts"][0]["text"]
            return candidate

    def _call_llm(self, system_prompt: str, user_content: str) -> str:
        """Routes triage call to injected mock, Google AI Studio, or Mistral."""
        # 1. If explicit client injected (e.g. in test suite), use it
        if self._is_custom_mistral_injected and self.mistral is not None:
            response = self.mistral.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                timeout_ms=10000
            )
            return response.choices[0].message.content

        # 2. If Google AI Studio Gemini API key is configured, use Gemini
        if settings.GEMINI_API_KEY:
            return self._call_gemini_api(system_prompt, user_content)

        # 3. Fallback to Mistral API
        if self.mistral is not None:
            response = self.mistral.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                timeout_ms=10000
            )
            return response.choices[0].message.content

        raise ValueError("No LLM provider configured. Please provide GEMINI_API_KEY or MISTRAL_API_KEY.")

    def triage_and_process_ticket(self, ticket: Ticket, session) -> Ticket:
        """
        Orchestrates RAG, LLM inference, schema validation, fallbacks,
        and deterministic business guardrails.
        """
        old_state = {
            "ticket_status": ticket.ticket_status.value,
            "ai_review_status": ticket.ai_review_status.value,
            "priority": ticket.priority.value
        }

        # Step 1: Query ChromaDB Vector Database
        rag_context, citations = self.retrieve_rag_context(f"{ticket.title} - {ticket.description}")
        ticket.ai_citations = citations

        # Step 2: System Prompt Construction with Schema Enforcement
        schema_json = json.dumps(LLMTriageOutput.model_json_schema())
        system_prompt = (
            "You are an Enterprise Tier-3 IT Helpdesk Automation Architect.\n"
            "Analyze the ticket and provided documentation context.\n"
            "Respond strictly with valid JSON conforming to this JSON Schema:\n"
            f"{schema_json}\n\n"
            "Context from Internal IT Knowledge Base:\n"
            f"{rag_context}"
        )

        user_content = f"Title: {ticket.title}\nDescription: {ticket.description}"

        # Step 3: Call LLM API with Robust Fallback Handling
        try:
            with trace_latency("llm_latency"):
                raw_json = self._call_llm(system_prompt, user_content)

            # Strip markdown code blocks if present
            raw_text = raw_json.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            parsed_output = LLMTriageOutput.model_validate_json(raw_text)

            # Apply Parsed LLM Metadata
            ticket.ai_triage_category = parsed_output.ai_triage_category
            ticket.ai_drafted_response = parsed_output.draft_response
            ticket.priority = parsed_output.suggested_priority

            # Step 4: Apply Deterministic Safety Guardrails
            # Rule 1: High/Critical priority or 'Access' requests must NEVER auto-resolve
            # and MUST require human-in-the-loop review.
            is_access_category = ticket.ai_triage_category.strip().lower() == "access"
            is_high_or_crit = ticket.priority in [PriorityEnum.HIGH, PriorityEnum.CRITICAL]

            if is_access_category or is_high_or_crit:
                ticket.ai_review_status = AIReviewStatusEnum.PENDING
                ticket.ticket_status = TicketStatusEnum.IN_PROGRESS
            elif parsed_output.can_auto_resolve and parsed_output.confidence >= 0.85:
                ticket.ai_review_status = AIReviewStatusEnum.APPROVED
                ticket.ticket_status = TicketStatusEnum.RESOLVED
            else:
                ticket.ai_review_status = AIReviewStatusEnum.PENDING
                ticket.ticket_status = TicketStatusEnum.OPEN

        except Exception as exc:
            # Fallback Pattern: Ensure no downtime or state failure when LLM is unavailable
            logger.error(
                f"LLM Triage execution failed: {str(exc)}",
                extra={"extra_fields": {"ticket_id": ticket.id, "error": str(exc)}}
            )
            ticket.ai_review_status = AIReviewStatusEnum.FAILED
            ticket.ai_drafted_response = "AI triage unavailable. Route manually to IT Operations."

        # Step 5: Save State and Create Audit Trail
        with trace_latency("db_latency"):
            new_state = {
                "ticket_status": ticket.ticket_status.value,
                "ai_review_status": ticket.ai_review_status.value,
                "priority": ticket.priority.value
            }
            audit_log = TicketHistory(
                ticket_id=ticket.id,
                previous_state=old_state,
                new_state=new_state,
                changed_by="SYSTEM_AI",
            )
            session.add(audit_log)
            session.commit()
            session.refresh(ticket)

        return ticket
