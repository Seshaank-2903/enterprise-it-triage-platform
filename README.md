# Enterprise AI IT Helpdesk & Triage Platform

An enterprise-ready IT service management and automated triage system powered by **FastAPI**, **React (Vite)**, **SQLAlchemy & Alembic**, **ChromaDB (RAG)**, and **Mistral AI**.

---

## 🏛️ Architecture Overview

```
                                      +------------------------+
                                      |     React Frontend     |
                                      | (Vite + Tailwind CSS)  |
                                      +-----------+------------+
                                                  |
                                             REST / JSON
                                                  |
                                                  v
+-------------------------------------------------+---------------------------------------------------+
| FastAPI Backend                                                                                     |
|                                                                                                     |
|  [Granular Observability Middleware]                                                                |
|  Logs X-Request-ID, api_latency, db_latency, rag_latency, llm_latency                               |
|                                                                                                     |
|  +--------------------+        +-------------------------+        +-------------------------------+ |
|  | Ticket Routes      |        | AI Triage Engine        |        | Analytics & Reports           | |
|  | - Create & List    |------->| - ChromaDB Vector RAG   |        | - SQLAlchemy Group Aggregates | |
|  | - Human Review     |        | - Mistral JSON Schema   |        | - Pandas Metrics Processing   | |
|  | - Audit History    |        | - Deterministic Rules   |        | - Streaming CSV Export        | |
|  +---------+----------+        +------------+------------+        +---------------+---------------+ |
+------------|--------------------------------|-------------------------------------|-----------------+
             |                                |                                     |
             v                                v                                     v
+------------------------+       +------------------------+             +-----------------------+
| Relational DB          |       | ChromaDB Vector Store  |             | Mistral AI API        |
| (SQLite / PostgreSQL)  |       | (IT Knowledge Base)    |             | (Structured Output)   |
+------------------------+       +------------------------+             +-----------------------+
```

---

## 🚀 Features

1. **Strict Database Modeling & Audit Logging**:
   - `Ticket` model with separated state fields: `ticket_status`, `ai_review_status`, `priority`, and `ai_triage_category`.
   - `TicketHistory` audit ledger tracking previous and new states, timestamp, and actor (`SYSTEM_AI` vs. human agent).
   - Dynamic Alembic migration configuration supporting SQLite (batch mode) and PostgreSQL.

2. **Granular Observability**:
   - Automatic `X-Request-ID` generation and context-variable propagation.
   - Structured JSON logs independently reporting `api_latency`, `db_latency`, `rag_latency`, and `llm_latency`.

3. **Deterministic Guardrails & Fallbacks**:
   - Mistral API output enforced via strict **Pydantic schema**.
   - **Deterministic Security Rule**: If `priority == High` or `category == Access`, auto-resolution is strictly blocked and forced to `ai_review_status = Pending` for human approval.
   - **Fault-Tolerant Fallback**: If LLM times out or produces invalid JSON, the ticket is saved, flagged as `Failed`, and never crashes the application.

4. **Code-Split Frontend Performance**:
   - Fast React + Vite + Tailwind CSS agent workspace.
   - Heavy Recharts analytics dashboard split using `React.lazy` and wrapped in `<Suspense>`.
   - Inspection modal displaying AI suggested solution alongside verified RAG source citations.

5. **Streaming Analytics with Pandas**:
   - FastAPI endpoint running SQLAlchemy `GROUP BY` aggregations into a Pandas DataFrame.
   - Computes resolution durations and streams downloadable CSV reports in real-time.

---

## 📁 Project Structure

```text
enterprise-ai-helpdesk/
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/
│       └── main.yml
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 001_initial_schema.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes_tickets.py
│   │   │   └── routes_reports.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── observability.py
│   │   ├── models/
│   │   │   ├── enums.py
│   │   │   └── models.py
│   │   ├── schemas/
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   └── ai_service.py
│   │   └── main.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_ai_service.py
│   │   └── test_api.py
│   ├── alembic.ini
│   ├── requirements.txt
│   └── setup.cfg
├── env/
│   ├── .env.development
│   ├── .env.production
│   ├── .env.staging
│   ├── API_KEYS_AND_SECRETS_GUIDE.md
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.frontend
│   │   └── nginx.conf
│   ├── knowledge_base/
│   │   ├── iam_access_policy.md
│   │   ├── vpn_network_troubleshooting.md
│   │   ├── hardware_replacement_sop.md
│   │   └── ingest_knowledge_base.py
│   └── seeds/
│       └── seed_data.py
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── components/
│   │   │   ├── AgentDashboard.tsx
│   │   │   ├── AnalyticsDashboard.tsx   # Lazy-loaded
│   │   │   ├── ReviewTicketModal.tsx
│   │   │   └── SubmitTicketForm.tsx
│   │   ├── test/
│   │   │   ├── setup.ts
│   │   │   └── AgentDashboard.test.tsx
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── vitest.config.ts
└── README.md
```

---

## 🛠️ Quick Start

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API docs will be available at: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```

The frontend will be available at: `http://localhost:5173`

---

## 🧪 Testing & CI

### Backend Tests (Isolated Unit Tests with Mocks)
```bash
cd backend
pytest --cov=app tests/
```

### Frontend Tests (Vitest + React Testing Library)
```bash
cd frontend
npm run test:run
```
