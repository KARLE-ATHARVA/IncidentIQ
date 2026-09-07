import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getIncidents } from "../api";

import type { IncidentSummary } from "../types";


function IncidentsPage() {
  const { projectId } = useParams<{
    projectId: string;
  }>();

  const navigate = useNavigate();

  const [incidents, setIncidents] = useState<
    IncidentSummary[]
  >([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(
    null,
  );


  useEffect(() => {
    async function loadIncidents() {
      if (!projectId) {
        setError("Missing project ID.");
        setLoading(false);
        return;
      }

      try {
        const data = await getIncidents(projectId);

        setIncidents(data.items);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load incidents.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadIncidents();
  }, [projectId]);


  if (loading) {
    return (
      <div>
        <h1>Incidents</h1>
        <p>Loading incidents...</p>
      </div>
    );
  }


  if (error) {
    return (
      <div>
        <h1>Incidents</h1>
        <p>{error}</p>
      </div>
    );
  }


  return (
    <div>
      <h1>Incidents</h1>

      {incidents.length === 0 ? (
        <p>No incidents found.</p>
      ) : (
        <div>
          {incidents.map((incident) => (
            <div
              key={incident.id}
              onClick={() =>
                navigate(
                  `/projects/${projectId}/incidents/${incident.id}`,
                )
              }
              style={{
                cursor: "pointer",
                border: "1px solid #ddd",
                padding: "16px",
                marginBottom: "12px",
              }}
            >
              <h2>{incident.title}</h2>

              <p>
                <strong>Severity:</strong>{" "}
                {incident.severity}
              </p>

              <p>
                <strong>Status:</strong>{" "}
                {incident.status}
              </p>

              <p>
                <strong>Detected:</strong>{" "}
                {new Date(
                  incident.detected_at,
                ).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


export default IncidentsPage;