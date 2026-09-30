import json
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.app.core.logging import configure_logging
from backend.app.core.metrics import metrics
from backend.app.core.redis import QUEUE_NAME, redis_client
from backend.app.db.database import engine
from backend.app.api.auth import router as auth_router
from backend.app.api.project import router as project_router
from backend.app.api.service import router as service_router
from backend.app.api.telemetry import router as telemetry_router
from backend.app.api.incidents import router as incidents_router
from backend.app.api import investigations
from backend.app.api.timeline import router as timeline_router
from backend.app.api.historical_incidents import (
    router as historical_incidents_router,
)
from backend.app.api.historical_retrieval import (
    router as historical_retrieval_router,
)


configure_logging()

logger = logging.getLogger("incidentiq.api")


app = FastAPI(
    title="IncidentIQ API",
    description="Incident investigation and intelligence platform",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        metrics.record_request(
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        logger.info(
            "HTTP request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response

    except Exception:
        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        metrics.record_request(
            path=request.url.path,
            status_code=500,
            duration_ms=duration_ms,
        )

        logger.exception(
            "HTTP request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "duration_ms": duration_ms,
            },
        )

        raise


app.include_router(auth_router)
app.include_router(project_router)
app.include_router(service_router)
app.include_router(telemetry_router)
app.include_router(incidents_router)
app.include_router(investigations.router)
app.include_router(timeline_router)
app.include_router(historical_incidents_router)
app.include_router(historical_retrieval_router)


@app.get("/")
def root():
    return {"message": "IncidentIQ API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/database")
def database_health_check():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database": result.scalar_one()}


@app.get("/health/redis")
def redis_health_check():
    return {"redis": redis_client.ping()}


@app.get("/metrics")
def application_metrics():
    return metrics.snapshot()


@app.post("/jobs/test")
def create_test_job():
    job = {
        "type": "test",
        "message": "Hello from FastAPI",
    }

    redis_client.rpush(
        QUEUE_NAME,
        json.dumps(job),
    )

    return {
        "queued": True,
        "job": job,
    }