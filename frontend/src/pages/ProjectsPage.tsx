import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import type { Project } from "../types";

import { getProjects } from "../api";

function ProjectsPage() {
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
            <h1 className="page-title">Projects</h1>
            <p className="page-description">
              Select a project to investigate its incidents.
            </p>
          </div>
        </div>

        <div className="card">
          <div className="state-card">
            <p className="state-title">Loading projects</p>
            <p className="state-description">Fetching your projects...</p>
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
            <h1 className="page-title">Projects</h1>
            <p className="page-description">
              Select a project to investigate its incidents.
            </p>
          </div>
        </div>

        <div className="card error-state">
          <div className="state-card">
            <p className="state-title">Unable to load projects</p>
            <p className="state-description">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Projects</h1>

          <p className="page-description">
            Select a project to investigate its incidents.
          </p>
        </div>
      </div>

      {projects.length === 0 ? (
        <div className="card">
          <div className="state-card">
            <p className="state-title">No projects found</p>

            <p className="state-description">
              There are currently no projects available for your account.
            </p>
          </div>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
            gap: "16px",
          }}
        >
          {projects.map((project) => (
            <div className="card" key={project.id}>
              <div className="card-body">
                <div
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    justifyContent: "space-between",
                    gap: "12px",
                    marginBottom: "8px",
                  }}
                >
                  <h2
                    style={{
                      margin: 0,
                      fontSize: "18px",
                      fontWeight: 650,
                    }}
                  >
                    {project.name}
                  </h2>

                  <span className="badge badge-neutral">Production</span>
                </div>

                <p
                  style={{
                    margin: "0 0 20px",
                    color: "#6b7280",
                    fontSize: "13px",
                  }}
                >
                  Investigate incidents and review engineering evidence.
                </p>

                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "10px",
                  }}
                >
                  <button
                    type="button"
                    className="button button-primary"
                    onClick={() =>
                      navigate(`/projects/${project.id}/incidents`)
                    }
                  >
                    View incidents
                  </button>

                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={() =>
                      navigate(`/projects/${project.id}/simulator`)
                    }
                  >
                    Production simulator
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ProjectsPage;
