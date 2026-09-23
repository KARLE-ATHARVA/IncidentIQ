import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  createInvestigation,
  generateInvestigationResult,
  getEvidenceInspection,
  getIncident,
  getIncidentTimeline,
  getInvestigations,
  getInvestigationResult,
  getSimilarHistoricalIncidents,
  startInvestigation,
} from "../api";

import IncidentTimeline from "../components/IncidentTimeline";
import InvestigationEvidencePanel from "../components/InvestigationEvidencePanel";
import InvestigationResultPanel from "../components/InvestigationResultPanel";
import SimilarHistoricalIncidents from "../components/SimilarHistoricalIncidents";

import type {
  Incident,
  Investigation,
  InvestigationEvidence,
  InvestigationResult,
} from "../types";

import type { TimelineResponse } from "../types/timeline";
import type { SimilarHistoricalIncident } from "../types/historicalRetrieval";

function IncidentWorkspacePage() {
  const { projectId, incidentId } = useParams<{
    projectId: string;
    incidentId: string;
  }>();

  const navigate = useNavigate();

  const [incident, setIncident] = useState<Incident | null>(null);

  const [investigation, setInvestigation] = useState<Investigation | null>(
    null,
  );

  const [investigationResult, setInvestigationResult] =
    useState<InvestigationResult | null>(null);

  const [selectedEvidence, setSelectedEvidence] =
    useState<InvestigationEvidence | null>(null);

  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);

  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);

  const [similarHistoricalIncidents, setSimilarHistoricalIncidents] = useState<
    SimilarHistoricalIncident[]
  >([]);

  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [starting, setStarting] = useState(false);
  const [generating, setGenerating] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [resultError, setResultError] = useState<string | null>(null);

  useEffect(() => {
    async function loadWorkspace() {
      if (!projectId || !incidentId) {
        setError("Missing project or incident ID.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        setResultError(null);
        setSelectedEvidence(null);
        setEvidenceError(null);

        const [incidentData, investigations, timelineData, historicalData] =
          await Promise.all([
            getIncident(projectId, incidentId),
            getInvestigations(projectId, incidentId),
            getIncidentTimeline(projectId, incidentId),
            getSimilarHistoricalIncidents(projectId, incidentId),
          ]);

        setIncident(incidentData);

        const currentInvestigation =
          investigations.length > 0 ? investigations[0] : null;

        setInvestigation(currentInvestigation);
        setTimeline(timelineData);
        setSimilarHistoricalIncidents(historicalData);

        if (currentInvestigation) {
          try {
            const existingResult = await getInvestigationResult(
              projectId,
              incidentId,
              currentInvestigation.id,
            );

            setInvestigationResult(existingResult);
          } catch {
            setInvestigationResult(null);
          }
        } else {
          setInvestigationResult(null);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load incident workspace.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadWorkspace();
  }, [projectId, incidentId]);

  async function handleCreateInvestigation() {
    if (!projectId || !incidentId) {
      return;
    }

    setCreating(true);
    setError(null);
    setResultError(null);

    try {
      const data = await createInvestigation(projectId, incidentId);

      setInvestigation(data);
      setInvestigationResult(null);
      setSelectedEvidence(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create investigation.",
      );
    } finally {
      setCreating(false);
    }
  }

  async function handleStartInvestigation() {
    if (!projectId || !incidentId || !investigation) {
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
        err instanceof Error ? err.message : "Failed to start investigation.",
      );
    } finally {
      setStarting(false);
    }
  }

  async function handleGenerateInvestigation() {
    if (!projectId || !incidentId || !investigation) {
      return;
    }

    setGenerating(true);
    setResultError(null);
    setSelectedEvidence(null);
    setEvidenceError(null);

    try {
      const result = await generateInvestigationResult(
        projectId,
        incidentId,
        investigation.id,
      );

      setInvestigationResult(result);

      try {
        const investigations = await getInvestigations(projectId, incidentId);

        if (investigations.length > 0) {
          setInvestigation(investigations[0]);
        }
      } catch {
        // Keep the generated result even if refresh fails.
      }
    } catch (err) {
      setResultError(
        err instanceof Error
          ? err.message
          : "Failed to generate investigation result.",
      );
    } finally {
      setGenerating(false);
    }
  }

  async function handleInspectEvidence(evidenceId: string) {
    if (!projectId || !incidentId) {
      return;
    }

    setLoadingEvidence(true);
    setEvidenceError(null);

    try {
      const evidence = await getEvidenceInspection(
        projectId,
        incidentId,
        evidenceId,
      );

      setSelectedEvidence(evidence);
    } catch (err) {
      setEvidenceError(
        err instanceof Error ? err.message : "Failed to inspect evidence.",
      );

      setSelectedEvidence(null);
    } finally {
      setLoadingEvidence(false);
    }
  }

  function handleCloseEvidence() {
    setSelectedEvidence(null);
    setEvidenceError(null);
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
        <p>{error ?? "Incident not found."}</p>

        <button onClick={() => navigate(`/projects/${projectId}/incidents`)}>
          Back to Incidents
        </button>
      </div>
    );
  }

  return (
    <div>
      <button onClick={() => navigate(`/projects/${projectId}/incidents`)}>
        ← Back to Incidents
      </button>

      <h1>{incident.title}</h1>

      <p>{incident.description}</p>

      <p>
        <strong>Severity:</strong> {incident.severity}
      </p>

      <p>
        <strong>Status:</strong> {incident.status}
      </p>

      <p>
        <strong>Detected:</strong>{" "}
        {new Date(incident.detected_at).toLocaleString()}
      </p>

      {incident.resolved_at && (
        <p>
          <strong>Resolved:</strong>{" "}
          {new Date(incident.resolved_at).toLocaleString()}
        </p>
      )}

      <hr />

      <h2>Investigation</h2>

      {!investigation && (
        <button onClick={handleCreateInvestigation} disabled={creating}>
          {creating ? "Creating..." : "Create Investigation"}
        </button>
      )}

      {investigation && (
        <div>
          <p>
            <strong>Status:</strong> {investigation.status}
          </p>

          <p>
            <strong>Investigation ID:</strong> {investigation.id}
          </p>

          {investigation.started_at && (
            <p>
              <strong>Started:</strong>{" "}
              {new Date(investigation.started_at).toLocaleString()}
            </p>
          )}

          {investigation.completed_at && (
            <p>
              <strong>Completed:</strong>{" "}
              {new Date(investigation.completed_at).toLocaleString()}
            </p>
          )}

          {investigation.status === "pending" && (
            <button onClick={handleStartInvestigation} disabled={starting}>
              {starting ? "Starting..." : "Start Investigation"}
            </button>
          )}

          <div>
            <br />

            <button
              onClick={handleGenerateInvestigation}
              disabled={generating || investigation.status === "pending"}
            >
              {generating
                ? "Generating Investigation..."
                : investigationResult
                  ? "Regenerate Investigation"
                  : "Generate Investigation"}
            </button>
          </div>

          {resultError && (
            <p>
              <strong>Investigation error:</strong> {resultError}
            </p>
          )}
        </div>
      )}

      <hr />

      {investigationResult && (
        <>
          <InvestigationResultPanel
            result={investigationResult}
            onInspectEvidence={handleInspectEvidence}
          />

          <hr />
        </>
      )}

      {loadingEvidence && (
        <section>
          <h3>Evidence Inspection</h3>
          <p>Loading evidence...</p>
        </section>
      )}

      {evidenceError && (
        <section>
          <h3>Evidence Inspection</h3>
          <p>{evidenceError}</p>
        </section>
      )}

      {selectedEvidence && (
        <>
          <InvestigationEvidencePanel
            evidence={selectedEvidence}
            onClose={handleCloseEvidence}
          />

          <hr />
        </>
      )}

      {timeline && (
        <>
          <IncidentTimeline
            events={timeline.events}
            startTime={timeline.start_time}
            endTime={timeline.end_time}
            detectedAt={incident.detected_at}
          />

          <hr />
        </>
      )}

      <SimilarHistoricalIncidents incidents={similarHistoricalIncidents} />

      {error && <p>{error}</p>}
    </div>
  );
}

export default IncidentWorkspacePage;
