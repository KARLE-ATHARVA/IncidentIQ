import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getSimulationState,
  resetSimulation,
  runBadDeploymentSimulation,
} from "../api/simulation";

import { useNotifications } from "../components/useNotifications";

function ProductionSimulatorPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { notify } = useNotifications();

  const [running, setRunning] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [loadingState, setLoadingState] = useState(true);
  const [simulationActive, setSimulationActive] = useState(false);

  const [lastResult, setLastResult] = useState<{
    incidentId: string;
    severity: string;
    title: string;
  } | null>(null);

  useEffect(() => {
    if (!projectId) {
      return;
    }

    const currentProjectId = projectId;

    async function loadSimulationState() {
      try {
        const state = await getSimulationState(currentProjectId);

        setSimulationActive(state.active);

        if (state.active && state.incident_id) {
          setLastResult({
            incidentId: state.incident_id,
            severity: state.severity ?? "unknown",
            title: state.title ?? "Incident detected",
          });
        } else {
          setLastResult(null);
        }
      } catch (err) {
        notify.error(
          err instanceof Error
            ? err.message
            : "Unable to load simulation state.",
        );
      } finally {
        setLoadingState(false);
      }
    }

    void loadSimulationState();
  }, [notify, projectId]);

  async function handleResetSimulation() {
    if (!projectId || resetting) {
      return;
    }

    setResetting(true);

    try {
      await resetSimulation(projectId);

      setSimulationActive(false);
      setLastResult(null);

      notify.success("Simulation reset. The environment is healthy again.");
    } catch (err) {
      notify.error(
        err instanceof Error
          ? err.message
          : "Unable to reset the production simulation.",
      );
    } finally {
      setResetting(false);
    }
  }

  async function handleBadDeployment() {
    if (!projectId) {
      notify.error("Project ID is missing.");
      return;
    }

    if (simulationActive) {
      notify.warning(
        "A simulation is already active. Reset it before starting another one.",
      );
      return;
    }

    setRunning(true);
    setLastResult(null);

    try {
      const result = await runBadDeploymentSimulation(projectId);

      if (result.status === "incident_detected" && result.incident_id) {
        const incidentId = result.incident_id;

        setLastResult({
          incidentId,
          severity: result.severity ?? "unknown",
          title: result.title ?? "Incident detected",
        });

        setSimulationActive(true);

        notify.success(
          "Production failure simulated. IncidentIQ detected an incident.",
        );
      } else {
        setSimulationActive(false);

        notify.error("The simulation completed, but no incident was detected.");
      }
    } catch (err) {
      notify.error(
        err instanceof Error
          ? err.message
          : "Unable to run the production simulation.",
      );
    } finally {
      setRunning(false);
    }
  }

  function openIncident() {
    if (!projectId || !lastResult) {
      return;
    }

    navigate(`/projects/${projectId}/incidents/${lastResult.incidentId}`);
  }

  function getDisplayIncidentTitle(title: string) {
    if (title.toLowerCase().includes("checkout_latency")) {
      return "Checkout latency degradation";
    }

    return title;
  }

  function getSeverityBadgeClass(severity: string) {
    switch (severity.toLowerCase()) {
      case "critical":
        return "badge-critical";

      case "high":
        return "badge-high";

      case "medium":
        return "badge-medium";

      case "low":
        return "badge-low";

      default:
        return "badge-neutral";
    }
  }

  return (
    <div className="page simulator-page">
      <div className="page-header">
        <div>
          <p className="eyebrow">PRODUCTION ENVIRONMENT</p>

          <h1>Production Simulator</h1>

          <p className="page-subtitle">
            Simulate a realistic application failure and watch IncidentIQ
            detect, correlate, and investigate it.
          </p>
        </div>

        <span className="badge badge-resolved">SIMULATION MODE</span>
      </div>

      {/* HEALTHY ENVIRONMENT */}

      <section className="card">
        <div className="card-body">
          <div className="section-heading">
            <div>
              <p className="eyebrow">CHECKOUT SERVICE</p>

              <h2>Healthy production environment</h2>

              <p>
                This environment generates realistic telemetry that flows
                through the same IncidentIQ detection and investigation
                pipeline.
              </p>
            </div>

            <span className="badge badge-resolved">● Healthy</span>
          </div>

          <div
            className="stats-grid"
            style={{
              marginTop: "24px",
              gap: "14px",
            }}
          >
            <div
              className="stat-card"
              style={{
                minHeight: "112px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <span className="stat-label">Checkout latency</span>

              <strong
                className="stat-value"
                style={{
                  marginTop: "8px",
                }}
              >
                101 ms
              </strong>

              <span
                className="stat-meta"
                style={{
                  marginTop: "6px",
                }}
              >
                Normal baseline
              </span>
            </div>

            <div
              className="stat-card"
              style={{
                minHeight: "112px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <span className="stat-label">Error rate</span>

              <strong
                className="stat-value"
                style={{
                  marginTop: "8px",
                }}
              >
                0.2%
              </strong>

              <span
                className="stat-meta"
                style={{
                  marginTop: "6px",
                }}
              >
                Within normal range
              </span>
            </div>

            <div
              className="stat-card"
              style={{
                minHeight: "112px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <span className="stat-label">Deployment</span>

              <strong
                className="stat-value"
                style={{
                  marginTop: "8px",
                }}
              >
                v2.3.9
              </strong>

              <span
                className="stat-meta"
                style={{
                  marginTop: "6px",
                }}
              >
                Stable release
              </span>
            </div>

            <div
              className="stat-card"
              style={{
                minHeight: "112px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <span className="stat-label">Environment</span>

              <strong
                className="stat-value"
                style={{
                  marginTop: "8px",
                }}
              >
                Production
              </strong>

              <span
                className="stat-meta"
                style={{
                  marginTop: "6px",
                }}
              >
                Checkout service
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* FAILURE INJECTION */}

      <section
        className="card"
        style={{
          marginTop: "20px",
        }}
      >
        <div className="card-body">
          <div className="section-heading">
            <div>
              <p className="eyebrow">FAILURE INJECTION</p>

              <h2>Simulate a bad deployment</h2>

              <p>
                Introduce a degraded deployment that increases checkout latency
                and produces payment timeout errors. IncidentIQ will receive the
                resulting telemetry and determine whether it constitutes an
                incident.
              </p>
            </div>
          </div>

          <div
            style={{
              marginTop: "24px",
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "14px",
            }}
          >
            <div
              style={{
                padding: "18px",
                border: "1px solid var(--border-color)",
                borderRadius: "12px",
                background: "var(--surface-subtle)",
              }}
            >
              <span className="stat-label">SCENARIO</span>

              <strong
                style={{
                  display: "block",
                  marginTop: "8px",
                  fontSize: "15px",
                }}
              >
                Bad deployment
              </strong>

              <p
                style={{
                  margin: "6px 0 0",
                  fontSize: "13px",
                }}
              >
                Release v2.4.0 introduces degraded checkout behavior.
              </p>
            </div>

            <div
              style={{
                padding: "18px",
                border: "1px solid var(--border-color)",
                borderRadius: "12px",
                background: "var(--surface-subtle)",
              }}
            >
              <span className="stat-label">EXPECTED SIGNALS</span>

              <strong
                style={{
                  display: "block",
                  marginTop: "8px",
                  fontSize: "15px",
                }}
              >
                Multi-signal degradation
              </strong>

              <p
                style={{
                  margin: "6px 0 0",
                  fontSize: "13px",
                }}
              >
                Elevated latency, payment timeout errors, and deployment
                activity.
              </p>
            </div>

            <div
              style={{
                padding: "18px",
                border: "1px solid var(--border-color)",
                borderRadius: "12px",
                background: "var(--surface-subtle)",
              }}
            >
              <span className="stat-label">INCIDENTIQ RESPONSE</span>

              <strong
                style={{
                  display: "block",
                  marginTop: "8px",
                  fontSize: "15px",
                }}
              >
                Evidence-first investigation
              </strong>

              <p
                style={{
                  margin: "6px 0 0",
                  fontSize: "13px",
                }}
              >
                Detect → Correlate → Investigate → Reason with evidence.
              </p>
            </div>
          </div>

          <div
            style={{
              marginTop: "24px",
              display: "flex",
              alignItems: "center",
              gap: "12px",
              flexWrap: "wrap",
            }}
          >
            <button
              className="button button-primary"
              type="button"
              onClick={handleBadDeployment}
              disabled={
                running || resetting || loadingState || simulationActive
              }
            >
              {running
                ? "Simulating production failure..."
                : simulationActive
                  ? "Simulation Active"
                  : "Deploy Bad Version"}
            </button>

            <button
              className="button button-secondary"
              type="button"
              onClick={handleResetSimulation}
              disabled={
                running || resetting || loadingState || !simulationActive
              }
            >
              {resetting ? "Resetting..." : "Reset Simulation"}
            </button>

            <span
              style={{
                fontSize: "12px",
                color: "#6b7280",
              }}
            >
              {simulationActive
                ? "Reset the environment before running another scenario."
                : "Generates telemetry through the real IncidentIQ pipeline."}
            </span>
          </div>
        </div>
      </section>

      {/* INCIDENT RESULT */}

      {lastResult && (
        <section
          className="card"
          style={{
            marginTop: "20px",
          }}
        >
          <div className="card-body">
            <div className="section-heading">
              <div>
                <p className="eyebrow">INCIDENT DETECTED</p>

                <h2>IncidentIQ detected a production incident</h2>

                <p>
                  The simulated failure successfully passed through the existing
                  detection and correlation pipeline.
                </p>
              </div>

              <span
                className={`badge ${getSeverityBadgeClass(
                  lastResult.severity,
                )}`}
              >
                {lastResult.severity.toUpperCase()}
              </span>
            </div>

            <div
              style={{
                marginTop: "22px",
                padding: "20px",
                border: "1px solid var(--border-color)",
                borderRadius: "14px",
                background: "var(--surface-subtle)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  justifyContent: "space-between",
                  gap: "20px",
                  flexWrap: "wrap",
                }}
              >
                <div>
                  <span
                    className="stat-label"
                    style={{
                      display: "block",
                      marginBottom: "7px",
                    }}
                  >
                    INCIDENT
                  </span>

                  <strong
                    style={{
                      display: "block",
                      fontSize: "20px",
                      lineHeight: 1.3,
                    }}
                  >
                    {getDisplayIncidentTitle(lastResult.title)}
                  </strong>

                  <p
                    style={{
                      margin: "8px 0 0",
                      color: "#6b7280",
                      fontSize: "13px",
                    }}
                  >
                    Detected from correlated checkout telemetry.
                  </p>
                </div>

                <div
                  style={{
                    minWidth: "250px",
                  }}
                >
                  <span className="stat-label">INCIDENT ID</span>

                  <p
                    style={{
                      margin: "7px 0 0",
                      fontSize: "12px",
                      fontFamily:
                        "ui-monospace, SFMono-Regular, Menlo, monospace",
                      color: "#6b7280",
                      wordBreak: "break-all",
                    }}
                  >
                    {lastResult.incidentId}
                  </p>
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  gap: "10px",
                  flexWrap: "wrap",
                  marginTop: "20px",
                }}
              >
                <button
                  className="button button-primary"
                  type="button"
                  onClick={openIncident}
                >
                  Open Investigation
                </button>

                <button
                  className="button button-secondary"
                  type="button"
                  onClick={() => setLastResult(null)}
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* EVIDENCE-FIRST DESIGN */}

      <section
        className="card"
        style={{
          marginTop: "20px",
        }}
      >
        <div className="card-body">
          <p className="eyebrow">EVIDENCE-FIRST DESIGN</p>

          <h2>What this simulator demonstrates</h2>

          <p
            style={{
              maxWidth: "720px",
            }}
          >
            The simulator does not decide the root cause. It generates
            engineering evidence and lets IncidentIQ's existing detection,
            correlation, retrieval, and reasoning pipeline determine what the
            evidence supports.
          </p>

          <div
            style={{
              marginTop: "24px",
              display: "grid",
              gap: "10px",
            }}
          >
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "48px 150px 1fr",
                alignItems: "center",
                gap: "16px",
                padding: "16px 18px",
                border: "1px solid var(--border-color)",
                borderRadius: "12px",
                background: "var(--surface-subtle)",
              }}
            >
              <span
                style={{
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "#6366f1",
                }}
              >
                01
              </span>

              <strong>Telemetry</strong>

              <span
                style={{
                  fontSize: "13px",
                  color: "#6b7280",
                }}
              >
                Real metric, log, and deployment events
              </span>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "48px 150px 1fr",
                alignItems: "center",
                gap: "16px",
                padding: "16px 18px",
                border: "1px solid var(--border-color)",
                borderRadius: "12px",
                background: "var(--surface-subtle)",
              }}
            >
              <span
                style={{
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "#6366f1",
                }}
              >
                02
              </span>

              <strong>Detection</strong>

              <span
                style={{
                  fontSize: "13px",
                  color: "#6b7280",
                }}
              >
                Explainable anomaly detection on telemetry
              </span>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "48px 150px 1fr",
                alignItems: "center",
                gap: "16px",
                padding: "16px 18px",
                border: "1px solid var(--border-color)",
                borderRadius: "12px",
                background: "var(--surface-subtle)",
              }}
            >
              <span
                style={{
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "#6366f1",
                }}
              >
                03
              </span>

              <strong>Correlation</strong>

              <span
                style={{
                  fontSize: "13px",
                  color: "#6b7280",
                }}
              >
                Related signals are connected into an incident candidate
              </span>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "48px 150px 1fr",
                alignItems: "center",
                gap: "16px",
                padding: "16px 18px",
                border: "1px solid var(--border-color)",
                borderRadius: "12px",
                background: "var(--surface-subtle)",
              }}
            >
              <span
                style={{
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "#6366f1",
                }}
              >
                04
              </span>

              <strong>Investigation</strong>

              <span
                style={{
                  fontSize: "13px",
                  color: "#6b7280",
                }}
              >
                Historical context and evidence-backed reasoning
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default ProductionSimulatorPage;
