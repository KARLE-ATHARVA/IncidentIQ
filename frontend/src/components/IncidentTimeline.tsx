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

function getEventClass(
  eventType: TimelineEvent["event_type"],
): string {
  switch (eventType) {
    case "metric":
      return "incident-timeline-event-metric";
    case "log":
      return "incident-timeline-event-log";
    case "deployment":
      return "incident-timeline-event-deployment";
  }
}

export default function IncidentTimeline({
  events,
  startTime,
  endTime,
  detectedAt,
}: IncidentTimelineProps) {
  return (
    <section className="incident-timeline">
      <header className="incident-timeline-header">
        <div>
          <div className="incident-timeline-eyebrow">
            INCIDENT RECONSTRUCTION
          </div>

          <h2>Incident Timeline</h2>

          <p>
            Events surrounding the incident detection point,
            ordered by occurrence.
          </p>
        </div>

        <div className="incident-timeline-window">
          <span>INVESTIGATION WINDOW</span>
          <strong>
            {formatTimestamp(startTime)} →{" "}
            {formatTimestamp(endTime)}
          </strong>
        </div>
      </header>

      <div className="incident-timeline-summary">
        <div className="incident-timeline-summary-item">
          <strong>{events.length}</strong>
          <span>telemetry events</span>
        </div>

        <div className="incident-timeline-summary-divider" />

        <div className="incident-timeline-summary-item">
          <strong>
            {formatTime(detectedAt)}
          </strong>
          <span>incident detected</span>
        </div>

        <div className="incident-timeline-summary-divider" />

        <div className="incident-timeline-legend">
          <span>
            <i className="timeline-legend-dot metric" />
            Metric
          </span>

          <span>
            <i className="timeline-legend-dot log" />
            Log
          </span>

          <span>
            <i className="timeline-legend-dot deployment" />
            Deployment
          </span>
        </div>
      </div>

      {events.length === 0 ? (
        <div className="state-card incident-timeline-empty">
          <p className="state-title">
            No telemetry events
          </p>

          <p className="state-description">
            No metric, log, or deployment events were found
            in this investigation window.
          </p>
        </div>
      ) : (
        <div className="incident-timeline-list">
          {events.map((event, index) => {
            const isDetectionPoint =
              new Date(event.timestamp).getTime() ===
              new Date(detectedAt).getTime();

            const isLast = index === events.length - 1;
            const eventClass = getEventClass(
              event.event_type,
            );

            return (
              <article
                key={event.id}
                className={`incident-timeline-event ${eventClass}${
                  isDetectionPoint
                    ? " incident-timeline-event-detected"
                    : ""
                }`}
              >
                <div className="incident-timeline-time">
                  <strong>
                    {formatTime(event.timestamp)}
                  </strong>

                  {isDetectionPoint && (
                    <span>Detection point</span>
                  )}
                </div>

                <div className="incident-timeline-rail">
                  {!isLast && (
                    <div className="incident-timeline-line" />
                  )}

                  <div className="incident-timeline-marker">
                    {getEventSymbol(event.event_type)}
                  </div>
                </div>

                <div className="incident-timeline-card">
                  <div className="incident-timeline-card-top">
                    <div className="incident-timeline-card-labels">
                      <span className="incident-timeline-type">
                        {getEventLabel(event.event_type)}
                      </span>

                      {event.severity && (
                        <span className="badge badge-neutral">
                          {event.severity}
                        </span>
                      )}

                      {isDetectionPoint && (
                        <span className="badge badge-critical">
                          Incident detected
                        </span>
                      )}
                    </div>

                    <span className="incident-timeline-full-time">
                      {formatTimestamp(event.timestamp)}
                    </span>
                  </div>

                  <h3>{event.title}</h3>

                  {event.description && (
                    <p>{event.description}</p>
                  )}

                  <div className="incident-timeline-metadata">
                    <span>
                      Service{" "}
                      <code>{event.service_id}</code>
                    </span>

                    <span>
                      Source{" "}
                      <code>{event.source_id}</code>
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