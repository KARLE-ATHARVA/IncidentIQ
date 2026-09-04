import { NavLink } from "react-router-dom";

function Sidebar() {
  return (
    <aside>
      <h2>IncidentIQ</h2>

      <nav>
        <NavLink to="/dashboard">Dashboard</NavLink>
        <NavLink to="/projects">Projects</NavLink>
        <NavLink to="/incidents">Incidents</NavLink>
      </nav>
    </aside>
  );
}

export default Sidebar;
