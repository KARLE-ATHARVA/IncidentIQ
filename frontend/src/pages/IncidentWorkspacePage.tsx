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

function getSeverityClass(severity: string): string {
  switch (severity.toLowerCase()) {
    case "critical":
      return "badge badge-critical";

    case "high":
      return "badge badge-high";

    case "medium":
      return "badge badge-medium";

    case "low":
      return "badge badge-low";

    default:
      return "badge";
  }
}

function getStatusClass(status: string): string {
  switch (status.toLowerCase()) {
    case "open":
      return "badge badge-open";

    case "investigating":
      return "badge badge-investigating";

    case "resolved":
      return "badge badge-resolved";

    default:
      return "badge";
  }
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",

    timeStyle: "short",
  });
}

function getDisplayIncidentTitle(title: string): string {
  const normalizedTitle = title.trim();

  const match = normalizedTitle.match(
    /^Potential incident:\s*(.+?)\s+anomaly on service\s+[0-9a-f-]{36}$/i,
  );

  if (!match) {
    return normalizedTitle;
  }

  const metricName = match[1]

    .replace(/[_-]+/g, " ")

    .replace(/\s+/g, " ")

    .trim();

  const formattedMetricName = metricName.replace(/\b\w/g, (character) =>
    character.toUpperCase(),
  );

  return `${formattedMetricName} anomaly detected`;
}

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
      const data = await createInvestigation(
        projectId,

        incidentId,
      );

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
        const investigations = await getInvestigations(
          projectId,

          incidentId,
        );

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
      <div className="page">
        <div className="workspace-loading">
          <div className="workspace-loading-mark">IQ</div>

          <div>
            <div className="state-title">Loading incident workspace</div>

            <div className="state-description">
              Gathering incident telemetry and investigation context...
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="page">
        <div className="state-card error-state workspace-not-found">
          <div className="state-title">Incident not found</div>

          <div className="state-description">
            {error ?? "The requested incident could not be loaded."}
          </div>

          <button
            type="button"
            className="button button-secondary"
            onClick={() => navigate(`/projects/${projectId}/incidents`)}
          >
            ← Back to Incidents
          </button>
        </div>
      </div>
    );
  }

  const investigationComplete = investigation?.status === "completed";

  return (
    <div className="page incident-workspace">
      <div className="workspace-breadcrumb">
        <button
          type="button"
          onClick={() => navigate(`/projects/${projectId}/incidents`)}
        >
          ← Incident Inbox
        </button>

        <span>/</span>

        <span>Investigation Workspace</span>
      </div>

      <section className="workspace-hero">
        <div className="workspace-hero-main">
          <div className="workspace-eyebrow">INCIDENT INVESTIGATION</div>

          <div className="workspace-badges">
            <span className={getSeverityClass(incident.severity)}>
              {incident.severity}
            </span>

            <span className={getStatusClass(incident.status)}>
              {incident.status}
            </span>
          </div>

          <h1>{getDisplayIncidentTitle(incident.title)}</h1>

          <p>{incident.description}</p>
        </div>

        <div className="workspace-hero-meta">
          <div>
            <span>Detected</span>

            <strong>{formatDate(incident.detected_at)}</strong>
          </div>

          {incident.resolved_at && (
            <div>
              <span>Resolved</span>

              <strong>{formatDate(incident.resolved_at)}</strong>
            </div>
          )}
        </div>
      </section>

      <div className="workspace-section-heading">
        <div>
          <span className="section-eyebrow">INVESTIGATION</span>

          <h2>Understand what happened</h2>

          <p>Move from detected anomaly to evidence-backed reasoning.</p>
        </div>
      </div>

      <section className="workspace-investigation-card">
        <div className="workspace-investigation-header">
          <div>
            <div className="workspace-card-kicker">INVESTIGATION RUN</div>

            <h2>
              {investigation
                ? "Investigation in progress"
                : "Start an investigation"}
            </h2>

            <p>
              Build context from the incident timeline, telemetry, deployments,
              and historical incidents.
            </p>
          </div>

          {investigation && (
            <span className={getStatusClass(investigation.status)}>
              {investigation.status}
            </span>
          )}
        </div>

        {!investigation && (
          <div className="workspace-action-row">
            <button
              type="button"
              className="button button-primary"
              onClick={handleCreateInvestigation}
              disabled={creating}
            >
              {creating ? "Creating..." : "Create Investigation"}
            </button>
          </div>
        )}

        {investigation && (
          <>
            <div className="workspace-investigation-meta">
              {investigation.started_at && (
                <div>
                  <span>Started</span>

                  <strong>{formatDate(investigation.started_at)}</strong>
                </div>
              )}

              {investigation.completed_at && (
                <div>
                  <span>Completed</span>

                  <strong>{formatDate(investigation.completed_at)}</strong>
                </div>
              )}
            </div>

            <div className="workspace-action-row">
              {investigation.status === "pending" && (
                <button
                  type="button"
                  className="button button-secondary"
                  onClick={handleStartInvestigation}
                  disabled={starting}
                >
                  {starting ? "Starting..." : "Start Investigation"}
                </button>
              )}

              <button
                type="button"
                className="button button-primary"
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
              <div className="workspace-inline-error">
                <strong>Investigation error</strong>

                <span>{resultError}</span>
              </div>
            )}
          </>
        )}
      </section>

      {investigationResult && (
        <section className="workspace-result-section">
          <div className="workspace-section-heading compact">
            <div>
              <span className="section-eyebrow">REASONING</span>

              <h2>Evidence-backed hypothesis</h2>

              <p>
                Review the reasoning, supporting evidence, alternatives, and
                next steps.
              </p>
            </div>

            <span className="workspace-evidence-principle">
              Evidence before conclusion
            </span>
          </div>

          <div className="workspace-result-card">
            <InvestigationResultPanel
              result={investigationResult}
              onInspectEvidence={handleInspectEvidence}
            />
          </div>
        </section>
      )}

      {(loadingEvidence || evidenceError || selectedEvidence) && (
        <section className="workspace-support-section">
          <div className="workspace-section-heading compact">
            <div>
              <span className="section-eyebrow">PROVENANCE</span>

              <h2>Evidence inspection</h2>

              <p>Inspect the source behind an investigation result.</p>
            </div>
          </div>

          <div className="workspace-support-card">
            {loadingEvidence && (
              <div className="workspace-inline-loading">
                Loading evidence...
              </div>
            )}

            {evidenceError && (
              <div className="workspace-inline-error">
                <strong>Evidence inspection failed</strong>

                <span>{evidenceError}</span>
              </div>
            )}

            {selectedEvidence && (
              <InvestigationEvidencePanel
                evidence={selectedEvidence}
                onClose={handleCloseEvidence}
              />
            )}
          </div>
        </section>
      )}

      {timeline && (
        <section className="workspace-support-section workspace-timeline-section">
          <IncidentTimeline
            events={timeline.events}
            startTime={timeline.start_time}
            endTime={timeline.end_time}
            detectedAt={incident.detected_at}
          />
        </section>
      )}

      <section className="workspace-support-section workspace-history-section">
        <SimilarHistoricalIncidents incidents={similarHistoricalIncidents} />
      </section>

      {investigationComplete && (
        <div className="workspace-completion-note">
          <span className="workspace-completion-icon">✓</span>

          <div>
            <strong>Investigation completed</strong>

            <span>
              The investigation result and its supporting evidence are persisted
              for future review.
            </span>
          </div>
        </div>
      )}

      {error && (
        <div className="workspace-inline-error workspace-global-error">
          <strong>Workspace error</strong>

          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

export default IncidentWorkspacePage;
