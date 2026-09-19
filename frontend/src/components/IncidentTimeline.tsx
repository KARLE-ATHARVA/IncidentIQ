import type { TimelineEvent } from "../types/timeline";

interface IncidentTimelineProps {
  events: TimelineEvent[];
  startTime: string;
  endTime: string;
  detectedAt: string;
}

function formatTimestamp(timestamp: string): string {
  return new Date(timestamp).toLocaleString();
}

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
}

function getEventLabel(
  eventType: TimelineEvent["event_type"],
): string {
  switch (eventType) {
    case "metric":
      return "METRIC";
    case "log":
      return "LOG";
    case "deployment":
      return "DEPLOYMENT";
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

function getEventBorder(
  eventType: TimelineEvent["event_type"],
): string {
  switch (eventType) {
    case "metric":
      return "#2563eb";
    case "log":
      return "#dc2626";
    case "deployment":
      return "#7c3aed";
  }
}

export default function IncidentTimeline({
  events,
  startTime,
  endTime,
  detectedAt,
}: IncidentTimelineProps) {
  return (
    <section
      style={{
        marginTop: "32px",
        paddingBottom: "24px",
      }}
    >
      <div
        style={{
          marginBottom: "24px",
        }}
      >
        <h2
          style={{
            marginBottom: "8px",
          }}
        >
          Incident Timeline
        </h2>

        <p
          style={{
            margin: 0,
            color: "#64748b",
            fontSize: "14px",
          }}
        >
          Investigation window:{" "}
          {formatTimestamp(startTime)} →{" "}
          {formatTimestamp(endTime)}
        </p>
      </div>

      {events.length === 0 ? (
        <div
          style={{
            padding: "20px",
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            background: "#f8fafc",
          }}
        >
          <p
            style={{
              margin: 0,
              color: "#64748b",
            }}
          >
            No telemetry events found in this
            investigation window.
          </p>
        </div>
      ) : (
        <div
          style={{
            position: "relative",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
          }}
        >
          {events.map((event) => {
            const borderColor = getEventBorder(
              event.event_type,
            );

            const isDetectionPoint =
              new Date(event.timestamp).getTime() ===
              new Date(detectedAt).getTime();

            return (
              <article
                key={event.id}
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "90px 36px 1fr",
                  gap: "16px",
                  alignItems: "start",
                }}
              >
                {/* Timestamp */}
                <div
                  style={{
                    paddingTop: "10px",
                    textAlign: "right",
                    color: isDetectionPoint
                      ? "#dc2626"
                      : "#64748b",
                    fontSize: "13px",
                    fontWeight: 600,
                  }}
                >
                  {formatTime(event.timestamp)}
                </div>

                {/* Timeline marker */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "center",
                    position: "relative",
                  }}
                >
                  <div
                    style={{
                      width: "32px",
                      height: "32px",
                      borderRadius: "50%",
                      border: `2px solid ${isDetectionPoint ? "#dc2626" : borderColor}`,
                      background: "#ffffff",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: isDetectionPoint
                        ? "#dc2626"
                        : borderColor,
                      fontSize: "12px",
                      fontWeight: 700,
                      zIndex: 1,
                    }}
                  >
                    {getEventSymbol(
                      event.event_type,
                    )}
                  </div>
                </div>

                {/* Event content */}
                <div
                  style={{
                    border: "1px solid #e2e8f0",
                    borderLeft: `4px solid ${isDetectionPoint ? "#dc2626" : borderColor}`,
                    borderRadius: "8px",
                    padding: "14px 16px",
                    background: isDetectionPoint
                      ? "#fff7f7"
                      : "#ffffff",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      marginBottom: "8px",
                      flexWrap: "wrap",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: 700,
                        letterSpacing: "0.05em",
                        color: borderColor,
                      }}
                    >
                      {getEventLabel(
                        event.event_type,
                      )}
                    </span>

                    {event.severity && (
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 700,
                          color: "#dc2626",
                        }}
                      >
                        {event.severity}
                      </span>
                    )}

                    {isDetectionPoint && (
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 700,
                          letterSpacing: "0.05em",
                          color: "#dc2626",
                        }}
                      >
                        INCIDENT DETECTED
                      </span>
                    )}
                  </div>

                  <h3
                    style={{
                      margin: "0 0 6px",
                      fontSize: "16px",
                    }}
                  >
                    {event.title}
                  </h3>

                  {event.description && (
                    <p
                      style={{
                        margin: "0 0 10px",
                        color: "#475569",
                        fontSize: "14px",
                        lineHeight: 1.5,
                      }}
                    >
                      {event.description}
                    </p>
                  )}

                  <div
                    style={{
                      display: "flex",
                      flexWrap: "wrap",
                      gap: "16px",
                      color: "#64748b",
                      fontSize: "12px",
                    }}
                  >
                    <span>
                      Service: {event.service_id}
                    </span>

                    <span>
                      Source: {event.source_id}
                    </span>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}