import os


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://incidentiq:incidentiq_dev@localhost:5432/incidentiq",
)