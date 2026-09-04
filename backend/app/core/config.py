import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://incidentiq:incidentiq_dev@localhost:5432/incidentiq",
)

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "incidentiq-dev-secret-change-me",
)

JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30