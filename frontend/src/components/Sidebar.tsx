import { NavLink, useLocation } from "react-router-dom";

function Sidebar() {
  const { pathname } = useLocation();
  const projectMatch = pathname.match(/^\/projects\/([^/]+)/);
  const projectId = projectMatch?.[1];

  return (
    <aside className="app-sidebar">
      <div className="app-sidebar-brand">
        <span className="app-sidebar-product-mark">IQ</span>
        <div>
          <strong>IncidentIQ</strong>
          <span>Evidence-first investigation</span>
        </div>
      </div>

      <nav className="app-sidebar-nav" aria-label="Primary navigation">
        <p className="app-sidebar-label">WORKSPACE</p>
        <NavLink
          to="/home"
          className={({ isActive }) =>
            `app-sidebar-link${isActive ? " active" : ""}`
          }
        >
          <span className="app-sidebar-icon">⌂</span>
          <span>Home</span>
        </NavLink>
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            `app-sidebar-link${isActive ? " active" : ""}`
          }
        >
          <span className="app-sidebar-icon">⌂</span>
          <span>Dashboard</span>
        </NavLink>

        <NavLink
          to="/projects"
          className={({ isActive }) =>
            `app-sidebar-link${isActive ? " active" : ""}`
          }
        >
          <span className="app-sidebar-icon">▦</span>
          <span>Projects</span>
        </NavLink>

        {projectId && (
          <>
            <p className="app-sidebar-label app-sidebar-section-label">
              INVESTIGATE
            </p>
            <NavLink
              to={`/projects/${projectId}/incidents`}
              className={({ isActive }) =>
                `app-sidebar-link${isActive ? " active" : ""}`
              }
            >
              <span className="app-sidebar-icon">◌</span>
              <span>Active Incidents</span>
            </NavLink>
            <NavLink
              to={`/projects/${projectId}/simulator`}
              className={({ isActive }) =>
                `app-sidebar-link${isActive ? " active" : ""}`
              }
            >
              <span className="app-sidebar-icon">↯</span>
              <span>Production Simulator</span>
            </NavLink>
          </>
        )}
      </nav>

      <div className="app-sidebar-footer">
        <div className="app-sidebar-footer-line" />
        <div className="app-sidebar-status">
          <span className="app-sidebar-status-dot" />
          Investigation workspace
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
