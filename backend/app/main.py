from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from backend.app.db.database import engine
from backend.app.core.redis import redis_client

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


@app.get("/")
def root():
    return {"message": "IncidentIQ API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/health/database")
def database_health_check():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database": result.scalar_one()}
    
@app.get("/health/redis")
def redis_health_check():
    return {"redis": redis_client.ping()}