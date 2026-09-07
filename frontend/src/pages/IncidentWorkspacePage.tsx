import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  createInvestigation,
  getIncident,
  startInvestigation,
} from "../api";

import type {
  Incident,
  Investigation,
} from "../types";


function IncidentWorkspacePage() {
  const { projectId, incidentId } = useParams<{
    projectId: string;
    incidentId: string;
  }>();

  const navigate = useNavigate();

  const [incident, setIncident] = useState<Incident | null>(null);
  const [investigation, setInvestigation] =
    useState<Investigation | null>(null);

  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);


  useEffect(() => {
    async function loadIncident() {
      if (!projectId || !incidentId) {
        setError("Missing project or incident ID.");
        setLoading(false);
        return;
      }

      try {
        const data = await getIncident(
          projectId,
          incidentId,
        );

        setIncident(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load incident.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadIncident();
  }, [projectId, incidentId]);


  async function handleCreateInvestigation() {
    if (!projectId || !incidentId) {
      return;
    }

    setCreating(true);
    setError(null);

    try {
      const data = await createInvestigation(
        projectId,
        incidentId,
      );

      setInvestigation(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create investigation.",
      );
    } finally {
      setCreating(false);
    }
  }


  async function handleStartInvestigation() {
    if (
      !projectId ||
      !incidentId ||
      !investigation
    ) {
      return;
    }

    setStarting(true);
    setError(null);

    try {
      const data = await startInvestigation(
        projectId,
        incidentId,
        investigation.id,
      );

      setInvestigation(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to start investigation.",
      );
    } finally {
      setStarting(false);
    }
  }


  if (loading) {
    return (
      <div>
        <p>Loading incident...</p>
      </div>
    );
  }


  if (!incident) {
    return (
      <div>
        <p>
          {error ?? "Incident not found."}
        </p>

        <button onClick={() => navigate("/incidents")}>
          Back to Incidents
        </button>
      </div>
    );
  }


  return (
    <div>
      <button
        onClick={() => navigate("/incidents")}
      >
        ← Back to Incidents
      </button>

      <h1>{incident.title}</h1>

      <p>{incident.description}</p>

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

      {incident.resolved_at && (
        <p>
          <strong>Resolved:</strong>{" "}
          {new Date(
            incident.resolved_at,
          ).toLocaleString()}
        </p>
      )}

      <hr />

      <h2>Investigation</h2>

      {!investigation && (
        <button
          onClick={handleCreateInvestigation}
          disabled={creating}
        >
          {creating
            ? "Creating..."
            : "Create Investigation"}
        </button>
      )}

      {investigation && (
        <div>
          <p>
            <strong>Status:</strong>{" "}
            {investigation.status}
          </p>

          {investigation.started_at && (
            <p>
              <strong>Started:</strong>{" "}
              {new Date(
                investigation.started_at,
              ).toLocaleString()}
            </p>
          )}

          {investigation.completed_at && (
            <p>
              <strong>Completed:</strong>{" "}
              {new Date(
                investigation.completed_at,
              ).toLocaleString()}
            </p>
          )}

          {investigation.status === "pending" && (
            <button
              onClick={handleStartInvestigation}
              disabled={starting}
            >
              {starting
                ? "Starting..."
                : "Start Investigation"}
            </button>
          )}
        </div>
      )}

      {error && (
        <p>
          {error}
        </p>
      )}
    </div>
  );
}


export default IncidentWorkspacePage;