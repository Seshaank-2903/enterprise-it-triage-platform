# Enterprise AI IT Helpdesk: API Keys & Secrets Guide

This guide details all API keys, database credentials, and service tokens required to run the platform in **Development**, **Staging**, and **Production**.

---

## 1. Primary AI Engine API Key

### Google AI Studio API Key (`GEMINI_API_KEY`)
* **Status:** Configured as Primary AI Engine (`gemini-1.5-flash`).
* **Purpose:** Drives autonomous ticket triage, category classification (`Access`, `Hardware`, `Software`, `Network`), confidence scoring, and resolution drafting with structured JSON schema validation.
* **Where to obtain / refresh:**
  1. Navigate to [Google AI Studio](https://aistudio.google.com/app/apikey).
  2. Click **Create API Key**.
* **Connected Locations:**
  - `backend/.env`
  - `env/.env.development`
  - `env/.env.production`
  - `backend/app/core/config.py`

---

## 2. Alternative LLM Engine Key (Optional)

### Mistral AI API Key (`MISTRAL_API_KEY`)
* **Status:** Available as secondary provider / unit-test fallback (`mistral-large-latest`).
* **Where to obtain:** [console.mistral.ai](https://console.mistral.ai/) $\to$ **API Keys**.
* **Configuration:** Leave empty to use Gemini, or populate in `.env` to route requests through Mistral.

---

## 3. Relational Database Credentials (`DATABASE_URL`)

* **Purpose:** Transactional storage for tickets, enum statuses, and the immutable `TicketHistory` audit ledger.
* **Format & Credentials:**
  - **Local Development (SQLite):**
    ```bash
    DATABASE_URL=sqlite:///./enterprise_helpdesk.db
    ```
  - **Production (PostgreSQL):**
    ```bash
    DATABASE_URL=postgresql+psycopg2://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>
    ```
    *Example:* `postgresql+psycopg2://helpdesk_admin:ChangeMeSecurePassword123!@localhost:5432/helpdesk_production`

---

## 4. Vector Database & RAG Citations (`CHROMA_PERSIST_DIR`)

* **Purpose:** Ground-truth semantic retrieval for IT policies and source citations attached to AI draft responses.
* **Configuration:**
  - **Local Path:** `./chroma_db` (automatically initialized with IT SOPs on first launch).
  - **Docker Volume:** `/chroma_data` mounted in `env/docker/docker-compose.yml`.

---

## 5. Configuration Matrix by Environment

| Key Name | Development (`env/.env.development`) | Staging (`env/.env.staging`) | Production (`env/.env.production`) |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | `staging` | `production` |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `INFO` |
| `DATABASE_URL` | `sqlite:///./enterprise_helpdesk.db` | `sqlite:///./staging_helpdesk.db` | `postgresql+psycopg2://...` |
| `GEMINI_API_KEY` | Connected | Connected | Connected |
| `MISTRAL_API_KEY` | Optional | Optional | Optional |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | `./staging_chroma_db` | `/chroma_data` |
