import contextvars
import json
import logging
import sys
import time
import uuid
from contextlib import contextmanager
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variables for isolated per-request tracing
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
metrics_ctx: contextvars.ContextVar[dict] = contextvars.ContextVar("metrics_ctx", default={})


class JSONFormatter(logging.Formatter):
    """Outputs standardized, machine-readable JSON logs for SIEM / APM log aggregators."""
    def format(self, record: logging.LogRecord) -> str:
        log_payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "request_id": request_id_ctx.get(),
            **getattr(record, "extra_fields", {}),
        }
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_payload)


def setup_logger(name: str = "enterprise_platform") -> logging.Logger:
    app_logger = logging.getLogger(name)
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False

    if not app_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        app_logger.addHandler(handler)
    return app_logger


logger = setup_logger()


@contextmanager
def trace_latency(metric_name: str):
    """
    Context manager to track duration of specific execution blocks.
    Supported metric_names: db_latency, rag_latency, llm_latency.
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        metrics = metrics_ctx.get().copy()
        metrics[metric_name] = round(metrics.get(metric_name, 0.0) + duration_ms, 2)
        metrics_ctx.set(metrics)


class GranularObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token_req_id = request_id_ctx.set(req_id)
        token_metrics = metrics_ctx.set({
            "db_latency": 0.0,
            "rag_latency": 0.0,
            "llm_latency": 0.0
        })

        start_time = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            accumulated_metrics = metrics_ctx.get()

            logger.info(
                f"{request.method} {request.url.path} Completed",
                extra={
                    "extra_fields": {
                        "http": {
                            "method": request.method,
                            "path": request.url.path,
                            "status_code": status_code,
                        },
                        "telemetry": {
                            "api_latency": total_latency_ms,
                            "db_latency": accumulated_metrics.get("db_latency", 0.0),
                            "rag_latency": accumulated_metrics.get("rag_latency", 0.0),
                            "llm_latency": accumulated_metrics.get("llm_latency", 0.0),
                        }
                    }
                }
            )

            request_id_ctx.reset(token_req_id)
            metrics_ctx.reset(token_metrics)
