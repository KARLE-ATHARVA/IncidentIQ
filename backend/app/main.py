import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.app.core.redis import QUEUE_NAME, redis_client
from backend.app.db.database import engine
from backend.app.api.auth import router as auth_router
from backend.app.api.project import router as project_router
from backend.app.api.service import router as service_router
from backend.app.api.telemetry import router as telemetry_router

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

app.include_router(auth_router)
app.include_router(project_router)
app.include_router(service_router)
app.include_router(telemetry_router)

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
