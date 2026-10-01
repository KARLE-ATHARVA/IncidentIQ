import type { SimilarHistoricalIncident } from "../types/historicalRetrieval";

interface SimilarHistoricalIncidentsProps {
  incidents: SimilarHistoricalIncident[];
}

function formatSimilarity(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function SimilarHistoricalIncidents({
  incidents,
}: SimilarHistoricalIncidentsProps) {
  return (
    <section className="historical-intelligence">
      <header className="historical-intelligence-header">
        <div>
          <div className="historical-intelligence-eyebrow">
            HISTORICAL INTELLIGENCE
          </div>

          <h2>Similar Historical Incidents</h2>

          <p>
            Previously resolved incidents that may
            provide useful investigation context.
          </p>
        </div>

        <div className="historical-match-count">
          <strong>{incidents.length}</strong>

          <span>
            {incidents.length === 1
              ? "similar incident"
              : "similar incidents"}
          </span>
        </div>
      </header>

      {incidents.length === 0 ? (
        <div className="state-card historical-empty">
          <div className="historical-empty-icon">
            ∅
          </div>

          <p className="state-title">
            No similar incidents found
          </p>

          <p className="state-description">
            No historical incidents met the current
            similarity threshold.
          </p>
        </div>
      ) : (
        <div className="historical-incident-list">
          {incidents.map((incident, index) => (
            <article
              key={incident.historical_incident_id}
              className="historical-incident-card"
            >
              <div className="historical-incident-rank">
                <span>
                  {String(index + 1).padStart(2, "0")}
                </span>
              </div>

              <div className="historical-incident-content">
                <div className="historical-incident-heading">
                  <div>
                    <div className="historical-incident-title-row">
                      <h3>{incident.title}</h3>

                      <span className="badge badge-resolved">
                        {incident.severity}
                      </span>
                    </div>

                    <p>
                      {incident.summary}
                    </p>
                  </div>

                  <div className="historical-similarity">
                    <strong>
                      {formatSimilarity(
                        incident.similarity_score,
                      )}
                    </strong>

                    <span>similarity</span>
                  </div>
                </div>

                <div className="historical-incident-meta">
                  <span>
                    Occurred{" "}
                    <strong>
                      {formatDate(
                        incident.occurred_at,
                      )}
                    </strong>
                  </span>

                  {incident.resolution && (
                    <span className="historical-resolution">
                      <span className="historical-resolution-label">
                        Resolution
                      </span>

                      {incident.resolution}
                    </span>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {incidents.length > 0 && (
        <div className="historical-intelligence-note">
          <span className="historical-note-icon">
            i
          </span>

          <span>
            Historical matches provide context for the
            investigation; they are not proof of the
            current incident's root cause.
          </span>
        </div>
      )}
    </section>
  );
}

export default SimilarHistoricalIncidents;