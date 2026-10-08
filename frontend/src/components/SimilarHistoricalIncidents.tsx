import type { SimilarHistoricalIncident } from "../types/historicalRetrieval";

interface SimilarHistoricalIncidentsProps {
  incidents: SimilarHistoricalIncident[];
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatSimilarity(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function getSimilarityTone(value: number): {
  color: string;
  background: string;
  border: string;
} {
  if (value >= 0.8) {
    return {
      color: "#047857",
      background: "#ecfdf5",
      border: "#a7f3d0",
    };
  }

  if (value >= 0.7) {
    return {
      color: "#2563eb",
      background: "#eff6ff",
      border: "#bfdbfe",
    };
  }

  return {
    color: "#64748b",
    background: "#f8fafc",
    border: "#e2e8f0",
  };
}

function getSeverityTone(severity: string): {
  color: string;
  background: string;
} {
  switch (severity.toLowerCase()) {
    case "critical":
      return {
        color: "#b91c1c",
        background: "#fef2f2",
      };

    case "high":
      return {
        color: "#c2410c",
        background: "#fff7ed",
      };

    case "medium":
      return {
        color: "#a16207",
        background: "#fefce8",
      };

    case "low":
      return {
        color: "#475569",
        background: "#f1f5f9",
      };

    default:
      return {
        color: "#64748b",
        background: "#f8fafc",
      };
  }
}

function truncateId(value: string): string {
  if (value.length <= 13) {
    return value;
  }

  return `${value.slice(0, 8)}…${value.slice(-4)}`;
}

export default function SimilarHistoricalIncidents({
  incidents,
}: SimilarHistoricalIncidentsProps) {
  if (incidents.length === 0) {
    return (
      <section>
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: "20px",
            marginBottom: "16px",
            flexWrap: "wrap",
          }}
        >
          <div>
            <div
              style={{
                color: "#4f46e5",
                fontSize: "10px",
                fontWeight: 700,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                marginBottom: "5px",
              }}
            >
              Historical intelligence
            </div>

            <h2
              style={{
                margin: 0,
                color: "#0f172a",
                fontSize: "20px",
                lineHeight: 1.3,
                letterSpacing: "-0.02em",
              }}
            >
              Similar incidents
            </h2>

            <p
              style={{
                margin: "5px 0 0",
                color: "#64748b",
                fontSize: "13px",
                lineHeight: 1.5,
              }}
            >
              Previous incidents can provide useful context
              without determining the current root cause.
            </p>
          </div>

          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "7px",
              padding: "7px 10px",
              border: "1px solid #e2e8f0",
              borderRadius: "7px",
              background: "#f8fafc",
              color: "#64748b",
              fontSize: "10px",
              fontWeight: 600,
            }}
          >
            <span
              style={{
                color: "#94a3b8",
                fontSize: "14px",
                lineHeight: 1,
              }}
            >
              0
            </span>

            historical matches
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "14px",
            padding: "15px 16px",
            border: "1px dashed #cbd5e1",
            borderRadius: "9px",
            background: "#f8fafc",
          }}
        >
          <div
            style={{
              width: "30px",
              height: "30px",
              flexShrink: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              borderRadius: "7px",
              background: "#eef2ff",
              color: "#4f46e5",
              fontSize: "14px",
              fontWeight: 700,
            }}
          >
            ∅
          </div>

          <div>
            <div
              style={{
                color: "#334155",
                fontSize: "13px",
                fontWeight: 650,
              }}
            >
              No strong historical matches
            </div>

            <div
              style={{
                marginTop: "3px",
                color: "#94a3b8",
                fontSize: "11px",
                lineHeight: 1.45,
              }}
            >
              No resolved incidents currently meet the
              similarity threshold for this investigation.
            </div>
          </div>
        </div>

        <div
          style={{
            marginTop: "9px",
            color: "#94a3b8",
            fontSize: "10px",
          }}
        >
          Historical matches provide context, not proof of
          root cause.
        </div>
      </section>
    );
  }

  return (
    <section>
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "20px",
          marginBottom: "16px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <div
            style={{
              color: "#4f46e5",
              fontSize: "10px",
              fontWeight: 700,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              marginBottom: "5px",
            }}
          >
            Historical intelligence
          </div>

          <h2
            style={{
              margin: 0,
              color: "#0f172a",
              fontSize: "20px",
              lineHeight: 1.3,
              letterSpacing: "-0.02em",
            }}
          >
            Similar incidents
          </h2>

          <p
            style={{
              margin: "5px 0 0",
              color: "#64748b",
              fontSize: "13px",
              lineHeight: 1.5,
            }}
          >
            Resolved incidents ranked by contextual
            similarity.
          </p>
        </div>

        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "7px",
            padding: "7px 10px",
            border: "1px solid #e2e8f0",
            borderRadius: "7px",
            background: "#f8fafc",
            color: "#64748b",
            fontSize: "10px",
            fontWeight: 600,
          }}
        >
          <span
            style={{
              color: "#4f46e5",
              fontSize: "14px",
              lineHeight: 1,
            }}
          >
            {incidents.length}
          </span>

          {incidents.length === 1
            ? "historical match"
            : "historical matches"}
        </div>
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "8px",
        }}
      >
        {incidents.map((incident, index) => {
          const similarity = getSimilarityTone(
            incident.similarity_score,
          );

          const severity = getSeverityTone(
            incident.severity,
          );

          return (
            <article
              key={incident.historical_incident_id}
              style={{
                display: "grid",
                gridTemplateColumns:
                  "34px minmax(0, 1fr) auto",
                gap: "13px",
                alignItems: "start",
                padding: "14px",
                border: "1px solid #e2e8f0",
                borderRadius: "9px",
                background: "#ffffff",
                boxShadow:
                  "0 1px 2px rgba(15, 23, 42, 0.03)",
                transition:
                  "border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease",
              }}
              onMouseEnter={(event) => {
                event.currentTarget.style.borderColor =
                  "#c7d2fe";
                event.currentTarget.style.boxShadow =
                  "0 4px 12px rgba(79, 70, 229, 0.07)";
                event.currentTarget.style.transform =
                  "translateY(-1px)";
              }}
              onMouseLeave={(event) => {
                event.currentTarget.style.borderColor =
                  "#e2e8f0";
                event.currentTarget.style.boxShadow =
                  "0 1px 2px rgba(15, 23, 42, 0.03)";
                event.currentTarget.style.transform =
                  "translateY(0)";
              }}
            >
              <div
                style={{
                  width: "34px",
                  height: "34px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  borderRadius: "8px",
                  background:
                    index === 0
                      ? "#eef2ff"
                      : "#f8fafc",
                  border: "1px solid #e2e8f0",
                  color:
                    index === 0
                      ? "#4f46e5"
                      : "#64748b",
                  fontSize: "11px",
                  fontWeight: 750,
                }}
              >
                {String(index + 1).padStart(2, "0")}
              </div>

              <div
                style={{
                  minWidth: 0,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "7px",
                    flexWrap: "wrap",
                    marginBottom: "4px",
                  }}
                >
                  <h3
                    style={{
                      margin: 0,
                      color: "#0f172a",
                      fontSize: "14px",
                      fontWeight: 650,
                      lineHeight: 1.35,
                    }}
                  >
                    {incident.title}
                  </h3>

                  <span
                    style={{
                      padding: "2px 6px",
                      borderRadius: "999px",
                      background: severity.background,
                      color: severity.color,
                      fontSize: "9px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.04em",
                    }}
                  >
                    {incident.severity}
                  </span>
                </div>

                <p
                  style={{
                    margin: "0 0 8px",
                    color: "#64748b",
                    fontSize: "11px",
                    lineHeight: 1.5,
                  }}
                >
                  {incident.summary}
                </p>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    flexWrap: "wrap",
                    color: "#94a3b8",
                    fontSize: "10px",
                  }}
                >
                  <span>
                    Occurred {formatDate(incident.occurred_at)}
                  </span>

                  {incident.resolved_at && (
                    <span>
                      Resolved{" "}
                      {formatDate(incident.resolved_at)}
                    </span>
                  )}

                  <span>
                    ID{" "}
                    {truncateId(
                      incident.historical_incident_id,
                    )}
                  </span>
                </div>

                {(incident.root_cause ||
                  incident.resolution) && (
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns:
                        "repeat(auto-fit, minmax(180px, 1fr))",
                      gap: "8px",
                      marginTop: "10px",
                      paddingTop: "9px",
                      borderTop: "1px solid #f1f5f9",
                    }}
                  >
                    {incident.root_cause && (
                      <div>
                        <div
                          style={{
                            color: "#94a3b8",
                            fontSize: "9px",
                            fontWeight: 700,
                            letterSpacing: "0.08em",
                            textTransform:
                              "uppercase",
                            marginBottom: "3px",
                          }}
                        >
                          Previous root cause
                        </div>

                        <div
                          style={{
                            color: "#475569",
                            fontSize: "10px",
                            lineHeight: 1.45,
                          }}
                        >
                          {incident.root_cause}
                        </div>
                      </div>
                    )}

                    {incident.resolution && (
                      <div>
                        <div
                          style={{
                            color: "#94a3b8",
                            fontSize: "9px",
                            fontWeight: 700,
                            letterSpacing: "0.08em",
                            textTransform:
                              "uppercase",
                            marginBottom: "3px",
                          }}
                        >
                          Previous resolution
                        </div>

                        <div
                          style={{
                            color: "#475569",
                            fontSize: "10px",
                            lineHeight: 1.45,
                          }}
                        >
                          {incident.resolution}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div
                style={{
                  minWidth: "72px",
                  padding: "7px 9px",
                  border: `1px solid ${similarity.border}`,
                  borderRadius: "7px",
                  background: similarity.background,
                  textAlign: "right",
                }}
              >
                <div
                  style={{
                    color: similarity.color,
                    fontSize: "16px",
                    lineHeight: 1,
                    fontWeight: 750,
                    letterSpacing: "-0.03em",
                  }}
                >
                  {formatSimilarity(
                    incident.similarity_score,
                  )}
                </div>

                <div
                  style={{
                    marginTop: "3px",
                    color: similarity.color,
                    opacity: 0.8,
                    fontSize: "8px",
                    fontWeight: 700,
                    letterSpacing: "0.07em",
                    textTransform: "uppercase",
                  }}
                >
                  similarity
                </div>
              </div>
            </article>
          );
        })}
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "7px",
          marginTop: "10px",
          padding: "8px 10px",
          borderRadius: "7px",
          background: "#f8fafc",
          color: "#94a3b8",
          fontSize: "10px",
          lineHeight: 1.45,
        }}
      >
        <span
          style={{
            color: "#4f46e5",
            fontWeight: 750,
          }}
        >
          i
        </span>

        Similarity indicates contextual relatedness, not
        causality. Historical incidents should be treated as
        supporting context rather than proof of root cause.
      </div>
    </section>
  );
}