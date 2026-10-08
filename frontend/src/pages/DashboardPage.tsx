import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getProjects } from "../api";
import type { Project } from "../types";

function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    async function loadProjects() {
      try {
        setProjects(await getProjects());
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load the operational workspace. Try again.",
        );
      } finally {
        setLoading(false);
      }
    }

    void loadProjects();
  }, []);

  return (
    <div className="page dashboard-page">
      <header className="page-header page-enter">
        <div>
          <p className="section-eyebrow">OPERATIONAL OVERVIEW</p>
          <h1 className="page-title">Incident intelligence</h1>
          <p className="page-description">
            Select a project to review detected incidents, investigate
            evidence, or run the controlled simulator scenario.
          </p>
        </div>
        <button
          type="button"
          className="button button-secondary"
          onClick={() => navigate("/home")}
        >
          Product overview
        </button>
      </header>

      <section className="dashboard-summary page-enter">
        <div className="dashboard-summary-main">
          <span className="section-eyebrow">YOUR WORKSPACE</span>
          <strong>{loading ? "—" : projects.length}</strong>
          <span>
            {projects.length === 1
              ? "project available"
              : "projects available"}
          </span>
        </div>
        <div className="dashboard-summary-copy">
          <strong>Start where the evidence lives.</strong>
          <p>
            Projects keep incident activity and the Production Simulator
            scoped to the engineering context you select.
          </p>
        </div>
      </section>

      <section className="dashboard-section page-enter">
        <div className="section-heading">
          <div>
            <p className="section-eyebrow">PROJECTS</p>
            <h2>Investigation surfaces</h2>
          </div>
          <button
            type="button"
            className="text-action"
            onClick={() => navigate("/projects")}
          >
            View all projects →
          </button>
        </div>

        {loading && (
          <div className="loading-grid" aria-label="Loading projects">
            <div /><div /><div />
          </div>
        )}

        {!loading && error && (
          <div className="state-card error-state">
            <div className="state-title">Unable to load projects</div>
            <div className="state-description">{error}</div>
          </div>
        )}

        {!loading && !error && projects.length === 0 && (
          <div className="state-card dashboard-empty-state">
            <div className="state-title">No projects available</div>
            <div className="state-description">
              Projects available to your account will appear here.
            </div>
          </div>
        )}

        {!loading && !error && projects.length > 0 && (
          <div className="dashboard-project-grid">
            {projects.map((project) => (
              <article key={project.id} className="project-surface">
                <div>
                  <span className="project-surface-label">PROJECT</span>
                  <h3>{project.name}</h3>
                  <p>
                    Review incident activity or demonstrate the
                    evidence-first workflow.
                  </p>
                </div>
                <div className="project-surface-actions">
                  <button
                    type="button"
                    className="button button-primary"
                    onClick={() =>
                      navigate(`/projects/${project.id}/incidents`)
                    }
                  >
                    Open incidents
                  </button>
                  <button
                    type="button"
                    className="button button-tertiary"
                    onClick={() =>
                      navigate(`/projects/${project.id}/simulator`)
                    }
                  >
                    Run simulator
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default DashboardPage;
