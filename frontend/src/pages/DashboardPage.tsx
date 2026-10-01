import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import type { Project } from "../types";

import { getProjects } from "../api";

function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  useEffect(() => {
    async function loadProjects() {
      try {
        const data = await getProjects();
        setProjects(data);
      } catch {
        setError("Failed to load projects.");
      } finally {
        setLoading(false);
      }
    }

    loadProjects();
  }, []);

  if (loading) {
    return (
      <div className="page">
        <div className="page-header">
          <div>
            <h1 className="page-title">
              IncidentIQ
            </h1>

            <p className="page-description">
              Engineering incident investigation workspace.
            </p>
          </div>
        </div>

        <div className="card">
          <div className="state-card">
            <p className="state-title">
              Loading workspace
            </p>

            <p className="state-description">
              Loading your projects...
            </p>
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
            <h1 className="page-title">
              IncidentIQ
            </h1>

            <p className="page-description">
              Engineering incident investigation workspace.
            </p>
          </div>
        </div>

        <div className="card error-state">
          <div className="state-card">
            <p className="state-title">
              Workspace unavailable
            </p>

            <p className="state-description">
              {error}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      {/* Hero */}
      <section
        className="card"
        style={{
          marginBottom: "24px",
          background:
            "linear-gradient(135deg, #ffffff 0%, #f8faff 100%)",
        }}
      >
        <div
          className="card-body"
          style={{
            padding: "32px",
          }}
        >
          <div
            style={{
              maxWidth: "720px",
            }}
          >
            <span
              className="badge badge-investigating"
              style={{
                marginBottom: "12px",
              }}
            >
              Engineering Investigation
            </span>

            <h1
              style={{
                margin: "0 0 10px",
                fontSize: "30px",
                lineHeight: 1.2,
              }}
            >
              Investigate incidents with evidence.
            </h1>

            <p
              style={{
                margin: 0,
                color: "#4b5563",
                fontSize: "15px",
                lineHeight: 1.7,
              }}
            >
              IncidentIQ connects telemetry, incident
              timelines, historical incidents, and
              AI-assisted reasoning into a structured
              investigation workflow.
            </p>
          </div>
        </div>
      </section>

      {/* Workflow */}
      <section
        style={{
          marginBottom: "28px",
        }}
      >
        <div
          style={{
            marginBottom: "14px",
          }}
        >
          <h2
            style={{
              margin: 0,
              fontSize: "18px",
            }}
          >
            Investigation workflow
          </h2>

          <p
            style={{
              margin: "5px 0 0",
              color: "#6b7280",
              fontSize: "13px",
            }}
          >
            Follow the evidence from detection to
            investigation.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "10px",
          }}
        >
          {[
            {
              number: "01",
              title: "Detect",
              description:
                "Identify abnormal application behavior.",
            },
            {
              number: "02",
              title: "Correlate",
              description:
                "Connect related telemetry and changes.",
            },
            {
              number: "03",
              title: "Investigate",
              description:
                "Build a structured incident context.",
            },
            {
              number: "04",
              title: "Reason",
              description:
                "Generate an evidence-backed hypothesis.",
            },
          ].map((step) => (
            <div
              key={step.number}
              className="card"
            >
              <div
                className="card-body"
                style={{
                  minHeight: "145px",
                }}
              >
                <span
                  style={{
                    color: "#6366f1",
                    fontSize: "11px",
                    fontWeight: 700,
                    letterSpacing: "0.06em",
                  }}
                >
                  {step.number}
                </span>

                <h3
                  style={{
                    margin: "10px 0 6px",
                    fontSize: "15px",
                  }}
                >
                  {step.title}
                </h3>

                <p
                  style={{
                    margin: 0,
                    color: "#6b7280",
                    fontSize: "13px",
                    lineHeight: 1.5,
                  }}
                >
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Projects */}
      <section>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "baseline",
            gap: "16px",
            marginBottom: "14px",
          }}
        >
          <div>
            <h2
              style={{
                margin: 0,
                fontSize: "18px",
              }}
            >
              Your projects
            </h2>

            <p
              style={{
                margin: "5px 0 0",
                color: "#6b7280",
                fontSize: "13px",
              }}
            >
              Select a project to open its incident inbox.
            </p>
          </div>

          <button
            type="button"
            className="button button-secondary"
            onClick={() => navigate("/projects")}
          >
            View all projects
          </button>
        </div>

        {projects.length === 0 ? (
          <div className="card">
            <div className="state-card">
              <p className="state-title">
                No projects available
              </p>

              <p className="state-description">
                Projects available to your account will
                appear here.
              </p>
            </div>
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fill, minmax(260px, 1fr))",
              gap: "12px",
            }}
          >
            {projects.map((project) => (
              <div
                className="card"
                key={project.id}
              >
                <div className="card-body">
                  <h3
                    style={{
                      margin: "0 0 7px",
                      fontSize: "16px",
                    }}
                  >
                    {project.name}
                  </h3>

                  <p
                    style={{
                      margin: "0 0 18px",
                      color: "#6b7280",
                      fontSize: "12px",
                    }}
                  >
                    Project incident workspace
                  </p>

                  <button
                    type="button"
                    className="button button-primary"
                    onClick={() =>
                      navigate(
                        `/projects/${project.id}/incidents`,
                      )
                    }
                  >
                    Open incident inbox
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default DashboardPage;