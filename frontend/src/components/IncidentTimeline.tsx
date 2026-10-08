import type { TimelineEvent } from "../types/timeline";

interface IncidentTimelineProps {
  events: TimelineEvent[];
  startTime: string;
  endTime: string;
  detectedAt: string;
}

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatDate(timestamp: string): string {
  return new Date(timestamp).toLocaleDateString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function getEventLabel(
  eventType: TimelineEvent["event_type"],
): string {
  switch (eventType) {
    case "metric":
      return "Metric";
    case "log":
      return "Log";
    case "deployment":
      return "Deployment";
  }
}

function getEventSymbol(
  eventType: TimelineEvent["event_type"],
): string {
  switch (eventType) {
    case "metric":
      return "M";
    case "log":
      return "L";
    case "deployment":
      return "D";
  }
}

function getEventAccent(
  eventType: TimelineEvent["event_type"],
): {
  color: string;
  background: string;
  border: string;
} {
  switch (eventType) {
    case "metric":
      return {
        color: "#2563eb",
        background: "#eff6ff",
        border: "#bfdbfe",
      };

    case "log":
      return {
        color: "#dc2626",
        background: "#fef2f2",
        border: "#fecaca",
      };

    case "deployment":
      return {
        color: "#7c3aed",
        background: "#f5f3ff",
        border: "#ddd6fe",
      };
  }
}

function getEventValue(event: TimelineEvent): string | null {
  if (
    event.event_type === "metric" &&
    event.metadata &&
    typeof event.metadata.value !== "undefined"
  ) {
    return String(event.metadata.value);
  }

  return null;
}

function getSourceLabel(event: TimelineEvent): string {
  const sourceId = String(event.source_id);

  if (sourceId.length <= 13) {
    return sourceId;
  }

  return `${sourceId.slice(0, 8)}…${sourceId.slice(-4)}`;
}

function getServiceLabel(event: TimelineEvent): string {
  const serviceId = String(event.service_id);

  if (serviceId.length <= 13) {
    return serviceId;
  }

  return `${serviceId.slice(0, 8)}…${serviceId.slice(-4)}`;
}

export default function IncidentTimeline({
  events,
  startTime,
  endTime,
  detectedAt,
}: IncidentTimelineProps) {
  const detectionTimestamp = new Date(detectedAt).getTime();

  const detectionIndex = events.findIndex(
    (event) =>
      new Date(event.timestamp).getTime() ===
      detectionTimestamp,
  );

  return (
    <section className="incident-timeline">
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "24px",
          marginBottom: "20px",
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
            Incident reconstruction
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
            Incident timeline
          </h2>

          <p
            style={{
              margin: "5px 0 0",
              color: "#64748b",
              fontSize: "13px",
              lineHeight: 1.5,
            }}
          >
            Events surrounding the detection point, ordered by
            occurrence.
          </p>
        </div>

        <div
          style={{
            padding: "9px 12px",
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            background: "#f8fafc",
            color: "#64748b",
            fontSize: "11px",
            lineHeight: 1.4,
            whiteSpace: "nowrap",
          }}
        >
          <div
            style={{
              fontSize: "9px",
              fontWeight: 700,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "#94a3b8",
              marginBottom: "2px",
            }}
          >
            Investigation window
          </div>

          {formatDate(startTime)} · {formatTime(startTime)}
          {" → "}
          {formatTime(endTime)}
        </div>
      </div>

      {events.length === 0 ? (
        <div
          style={{
            padding: "24px",
            border: "1px dashed #cbd5e1",
            borderRadius: "10px",
            background: "#f8fafc",
            textAlign: "center",
          }}
        >
          <div
            style={{
              color: "#475569",
              fontSize: "14px",
              fontWeight: 650,
            }}
          >
            No telemetry events found
          </div>

          <div
            style={{
              marginTop: "5px",
              color: "#94a3b8",
              fontSize: "12px",
            }}
          >
            No metric, log, or deployment events were recorded
            in this investigation window.
          </div>
        </div>
      ) : (
        <>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0",
              marginBottom: "20px",
              padding: "10px 12px",
              border: "1px solid #e2e8f0",
              borderRadius: "9px",
              background: "#f8fafc",
              flexWrap: "wrap",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: "6px",
                paddingRight: "18px",
              }}
            >
              <strong
                style={{
                  color: "#0f172a",
                  fontSize: "15px",
                }}
              >
                {events.length}
              </strong>

              <span
                style={{
                  color: "#64748b",
                  fontSize: "11px",
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                }}
              >
                telemetry events
              </span>
            </div>

            <div
              style={{
                width: "1px",
                height: "22px",
                background: "#e2e8f0",
                marginRight: "18px",
              }}
            />

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                paddingRight: "18px",
              }}
            >
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  background: "#dc2626",
                }}
              />

              <span
                style={{
                  color: "#475569",
                  fontSize: "11px",
                }}
              >
                Detection point
              </span>
            </div>

            <div
              style={{
                marginLeft: "auto",
                display: "flex",
                alignItems: "center",
                gap: "14px",
              }}
            >
              {[
                ["metric", "#2563eb"],
                ["log", "#dc2626"],
                ["deployment", "#7c3aed"],
              ].map(([label, color]) => (
                <div
                  key={label}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "5px",
                    color: "#64748b",
                    fontSize: "10px",
                  }}
                >
                  <span
                    style={{
                      width: "6px",
                      height: "6px",
                      borderRadius: "50%",
                      background: color,
                    }}
                  />

                  {label}
                </div>
              ))}
            </div>
          </div>

          <div
            style={{
              position: "relative",
            }}
          >
            {events.map((event, index) => {
              const accent = getEventAccent(
                event.event_type,
              );

              const isDetectionPoint =
                index === detectionIndex;

              const isLast =
                index === events.length - 1;

              const metricValue = getEventValue(event);

              return (
                <article
                  key={event.id}
                  style={{
                    display: "grid",
                    gridTemplateColumns:
                      "76px 28px minmax(0, 1fr)",
                    gap: "12px",
                    alignItems: "stretch",
                  }}
                >
                  <div
                    style={{
                      paddingTop: "13px",
                      textAlign: "right",
                      color: isDetectionPoint
                        ? "#dc2626"
                        : "#64748b",
                      fontSize: "11px",
                      fontWeight: isDetectionPoint
                        ? 700
                        : 500,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {formatTime(event.timestamp)}
                  </div>

                  <div
                    style={{
                      position: "relative",
                      display: "flex",
                      justifyContent: "center",
                    }}
                  >
                    {!isLast && (
                      <div
                        style={{
                          position: "absolute",
                          top: "28px",
                          bottom: "-1px",
                          width: "1px",
                          background: "#dbe3ed",
                        }}
                      />
                    )}

                    <div
                      style={{
                        position: "relative",
                        zIndex: 1,
                        width: "27px",
                        height: "27px",
                        borderRadius: "50%",
                        border: `2px solid ${
                          isDetectionPoint
                            ? "#dc2626"
                            : accent.color
                        }`,
                        background: isDetectionPoint
                          ? "#fff1f2"
                          : "#ffffff",
                        color: isDetectionPoint
                          ? "#dc2626"
                          : accent.color,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "9px",
                        fontWeight: 750,
                        boxShadow: isDetectionPoint
                          ? "0 0 0 4px #fee2e2"
                          : "none",
                      }}
                    >
                      {getEventSymbol(
                        event.event_type,
                      )}
                    </div>
                  </div>

                  <div
                    style={{
                      position: "relative",
                      marginBottom: isLast
                        ? "0"
                        : "10px",
                      padding: "12px 14px",
                      border: `1px solid ${
                        isDetectionPoint
                          ? "#fecaca"
                          : "#e2e8f0"
                      }`,
                      borderLeft: `3px solid ${
                        isDetectionPoint
                          ? "#dc2626"
                          : accent.color
                      }`,
                      borderRadius: "8px",
                      background: isDetectionPoint
                        ? "#fffafa"
                        : "#ffffff",
                      boxShadow:
                        "0 1px 2px rgba(15, 23, 42, 0.03)",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "7px",
                        marginBottom: "5px",
                        flexWrap: "wrap",
                      }}
                    >
                      <span
                        style={{
                          color: accent.color,
                          fontSize: "9px",
                          fontWeight: 750,
                          letterSpacing: "0.1em",
                          textTransform: "uppercase",
                        }}
                      >
                        {getEventLabel(
                          event.event_type,
                        )}
                      </span>

                      {event.severity && (
                        <span
                          style={{
                            padding: "2px 6px",
                            borderRadius: "999px",
                            background: "#f1f5f9",
                            color: "#64748b",
                            fontSize: "9px",
                            fontWeight: 650,
                            textTransform:
                              "uppercase",
                          }}
                        >
                          {event.severity}
                        </span>
                      )}

                      {isDetectionPoint && (
                        <span
                          style={{
                            padding: "2px 7px",
                            borderRadius: "999px",
                            background: "#fef2f2",
                            color: "#dc2626",
                            fontSize: "9px",
                            fontWeight: 700,
                            letterSpacing: "0.03em",
                          }}
                        >
                          Detection point
                        </span>
                      )}
                    </div>

                    <div
                      style={{
                        display: "flex",
                        alignItems: "baseline",
                        justifyContent:
                          "space-between",
                        gap: "16px",
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
                        {event.title}
                      </h3>

                      {metricValue && (
                        <span
                          style={{
                            flexShrink: 0,
                            color: "#0f172a",
                            fontSize: "12px",
                            fontWeight: 650,
                          }}
                        >
                          {metricValue}
                        </span>
                      )}
                    </div>

                    {event.description && (
                      <p
                        style={{
                          margin: "5px 0 8px",
                          color: "#64748b",
                          fontSize: "12px",
                          lineHeight: 1.5,
                        }}
                      >
                        {event.description}
                      </p>
                    )}

                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "14px",
                        color: "#94a3b8",
                        fontSize: "10px",
                        flexWrap: "wrap",
                      }}
                    >
                      <span>
                        Service {getServiceLabel(event)}
                      </span>

                      <span>
                        Source {getSourceLabel(event)}
                      </span>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}