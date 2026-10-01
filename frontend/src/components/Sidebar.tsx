import { NavLink } from "react-router-dom";

function Sidebar() {
  return (
    <aside className="app-sidebar">
      <div className="app-sidebar-header">
        <span className="app-sidebar-label">WORKSPACE</span>
        <span className="app-sidebar-status">
          <span className="app-sidebar-status-dot" />
          Operational
        </span>
      </div>

      <nav className="app-sidebar-nav" aria-label="Primary navigation">
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
      </nav>

      <div className="app-sidebar-footer">
        <div className="app-sidebar-footer-line" />

        <div className="app-sidebar-product">
          <span className="app-sidebar-product-mark">IQ</span>

          <div>
            <strong>IncidentIQ</strong>
            <span>Evidence before conclusion.</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;