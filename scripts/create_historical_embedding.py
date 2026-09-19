import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.db.database import SessionLocal
from backend.app.models.historical_incident import HistoricalIncident
from backend.app.models.historical_incident_embedding import (
    HistoricalIncidentEmbedding,
)
from backend.app.services.historical_incident_embedding import (
    create_historical_incident_embedding,
)


HISTORICAL_INCIDENT_ID = UUID(
    "311b0f99-3937-46a8-9baf-44f7db65e643"
)


def main() -> None:
    db = SessionLocal()

    try:
        historical_incident = (
            db.query(HistoricalIncident)
            .filter(
                HistoricalIncident.id == HISTORICAL_INCIDENT_ID
            )
            .first()
        )

        if historical_incident is None:
            raise ValueError(
                "Historical incident not found."
            )

        existing_embedding = (
            db.query(HistoricalIncidentEmbedding)
            .filter(
                HistoricalIncidentEmbedding.historical_incident_id
                == historical_incident.id
            )
            .first()
        )

        if existing_embedding is not None:
            print("Embedding already exists.")
            print(f"Embedding ID: {existing_embedding.id}")
            print(
                f"Historical Incident ID: "
                f"{existing_embedding.historical_incident_id}"
            )
            print(f"Model: {existing_embedding.model_name}")
            print(f"Dimensions: {len(existing_embedding.embedding)}")
            return

        embedding = create_historical_incident_embedding(
            db=db,
            historical_incident=historical_incident,
        )

        print("Embedding created successfully.")
        print(f"Embedding ID: {embedding.id}")
        print(
            f"Historical Incident ID: "
            f"{embedding.historical_incident_id}"
        )
        print(f"Model: {embedding.model_name}")
        print(f"Dimensions: {len(embedding.embedding)}")

    finally:
        db.close()


if __name__ == "__main__":
    main()

