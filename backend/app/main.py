from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.routes_tickets import router as tickets_router
from app.api.routes_reports import router as reports_router
from app.core.config import settings
from app.core.database import engine
from app.core.observability import GranularObservabilityMiddleware, logger
from app.models.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Enterprise AI Helpdesk Platform database models...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down Enterprise AI Helpdesk Platform.")


app = FastAPI(
    title="Enterprise AI IT Helpdesk & Triage Platform",
    description="Scalable, guardrailed IT service automation with RAG, Mistral API, and granular observability.",
    version="1.0.0",
    lifespan=lifespan
)

# Granular Observability Middleware (Logs API, DB, RAG, and LLM Latencies + X-Request-ID)
app.add_middleware(GranularObservabilityMiddleware)

# High-speed payload compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registration
app.include_router(tickets_router, prefix="/api")
app.include_router(reports_router, prefix="/api")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
