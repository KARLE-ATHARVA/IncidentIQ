import type { SimilarHistoricalIncident } from "../types/historicalRetrieval";

interface SimilarHistoricalIncidentsProps {
  incidents: SimilarHistoricalIncident[];
}

function SimilarHistoricalIncidents({
  incidents,
}: SimilarHistoricalIncidentsProps) {
  return (
    <section>
      <h2>Similar Historical Incidents</h2>

      <p>
        Historical incidents with similar telemetry and incident context.
        Similarity indicates relatedness, not confirmed causality.
      </p>

      {incidents.length === 0 ? (
        <p>No sufficiently similar historical incidents found.</p>
      ) : (
        <div>
          {incidents.map((incident) => {
            const similarityPercentage = (
              incident.similarity_score * 100
            ).toFixed(1);

            return (
              <article key={incident.historical_incident_id}>
                <h3>{incident.title}</h3>

                <p>
                  <strong>Similarity:</strong>{" "}
                  {similarityPercentage}%
                </p>

                <p>
                  <strong>Severity:</strong>{" "}
                  {incident.severity}
                </p>

                <p>
                  <strong>Summary:</strong>{" "}
                  {incident.summary}
                </p>

                <p>
                  <strong>Symptoms:</strong>{" "}
                  {incident.symptoms}
                </p>

                {incident.root_cause && (
                  <p>
                    <strong>Recorded Root Cause:</strong>{" "}
                    {incident.root_cause}
                  </p>
                )}

                {incident.resolution && (
                  <p>
                    <strong>Recorded Resolution:</strong>{" "}
                    {incident.resolution}
                  </p>
                )}

                <p>
                  <strong>Occurred:</strong>{" "}
                  {new Date(
                    incident.occurred_at,
                  ).toLocaleString()}
                </p>

                <hr />
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default SimilarHistoricalIncidents;