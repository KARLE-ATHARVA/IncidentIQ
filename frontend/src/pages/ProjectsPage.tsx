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
    getProjects()
      .then((data) => {
        setProjects(data);
      })
      .catch(() => {
        setError("Failed to load projects");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <p>Loading projects...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <div>
      <h1>Projects</h1>

      {projects.length === 0 ? (
        <p>No projects found.</p>
      ) : (
        <ul>
          {projects.map((project) => (
            <li key={project.id}>
              <button
                onClick={() => navigate(`/projects/${project.id}/incidents`)}
              >
                {project.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default ProjectsPage;
