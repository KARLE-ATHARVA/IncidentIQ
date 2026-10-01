import { useEffect, useState } from "react";
import {
  useNavigate,
  useParams,
} from "react-router-dom";

import { getIncidents } from "../api";
import type { IncidentSummary } from "../types/incident";

function severityClass(severity: string) {
  return `badge badge-${severity.toLowerCase()}`;
}

function statusClass(status: string) {
  return `badge badge-${status.toLowerCase()}`;
}

function formatDate(value: string | null | undefined) {
  if (!value) {
    return "—";
  }

  return new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function IncidentsPage() {
  const { projectId } = useParams<{
    projectId: string;
  }>();

  const navigate = useNavigate();

  const [incidents, setIncidents] = useState<
    IncidentSummary[]
  >([]);

  const [loading, setLoading] = useState(
    Boolean(projectId),
  );

  const [error, setError] = useState("");

  useEffect(() => {
    if (!projectId) {
      return;
    }

    async function loadIncidents(
      currentProjectId: string,
    ) {
      try {
        setLoading(true);
        setError("");

        const response =
          await getIncidents(currentProjectId);

        setIncidents(response.items);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load incidents.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadIncidents(projectId);
  }, [projectId]);

  if (!projectId) {
    return (
      <div className="page">
        <div className="page-header">
          <div>
            <p className="section-eyebrow">
              PROJECT
            </p>

            <h1 className="page-title">
              Incident Inbox
            </h1>
          </div>
        </div>

        <div className="state-card error-state">
          <div className="state-title">
            Project could not be identified
          </div>

          <div className="state-description">
            Return to Projects and select a project
            before opening its incident inbox.
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="page">
        <div className="page-header">
          <div>
            <p className="section-eyebrow">
              PROJECT
            </p>

            <h1 className="page-title">
              Incident Inbox
            </h1>
          </div>
        </div>

        <div className="state-card">
          <div className="state-title">
            Loading incidents
          </div>

          <div className="state-description">
            Retrieving the latest incident activity.
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="page-header">
          <div>
            <p className="section-eyebrow">
              PROJECT
            </p>

            <h1 className="page-title">
              Incident Inbox
            </h1>
          </div>
        </div>

        <div className="state-card error-state">
          <div className="state-title">
            Unable to load incidents
          </div>

          <div className="state-description">
            {error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header incident-inbox-header">
        <div>
          <p className="section-eyebrow">
            PROJECT INCIDENTS
          </p>

          <h1 className="page-title">
            Incident Inbox
          </h1>

          <p className="page-description">
            Review detected incidents and open an
            investigation workspace to understand
            what happened.
          </p>
        </div>

        <div className="incident-inbox-count">
          <strong>{incidents.length}</strong>

          <span>
            {incidents.length === 1
              ? "incident"
              : "incidents"}
          </span>
        </div>
      </div>

      {incidents.length === 0 ? (
        <div className="state-card incident-empty-state">
          <div className="incident-empty-icon">
            ✓
          </div>

          <div className="state-title">
            No incidents detected
          </div>

          <div className="state-description">
            IncidentIQ will surface incidents here
            when abnormal behavior is detected from
            project telemetry.
          </div>
        </div>
      ) : (
        <div className="incident-list">
          {incidents.map((incident) => (
            <button
              key={incident.id}
              type="button"
              className="incident-card"
              onClick={() =>
                navigate(
                  `/projects/${projectId}/incidents/${incident.id}`,
                )
              }
            >
              <div className="incident-card-main">
                <div className="incident-card-topline">
                  <div className="incident-card-badges">
                    <span
                      className={severityClass(
                        incident.severity,
                      )}
                    >
                      {incident.severity}
                    </span>

                    <span
                      className={statusClass(
                        incident.status,
                      )}
                    >
                      {incident.status}
                    </span>
                  </div>

                  <span className="incident-card-open">
                    Investigate →
                  </span>
                </div>

                <h2>{incident.title}</h2>

                <div className="incident-card-meta">
                  <div>
                    <span className="incident-meta-label">
                      Detected
                    </span>

                    <span>
                      {formatDate(
                        incident.detected_at,
                      )}
                    </span>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default IncidentsPage;