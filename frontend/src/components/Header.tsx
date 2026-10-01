import { useNavigate } from "react-router-dom";

function Header() {
  const navigate = useNavigate();

  function handleLogout() {
    localStorage.removeItem("access_token");
    navigate("/login");
  }

  return (
    <header className="app-header">
      <div className="app-header-brand">
        <div className="app-header-brand-mark">
          IQ
        </div>

        <div className="app-header-brand-copy">
          <span className="app-header-brand-name">IncidentIQ</span>
          <span className="app-header-brand-subtitle">
            Incident Intelligence
          </span>
        </div>
      </div>

      <div className="app-header-user">
        <div className="app-header-user-info">
          <div className="app-header-avatar">E</div>

          <div className="app-header-user-copy">
            <span className="app-header-user-name">Engineer</span>
            <span className="app-header-user-role">
              Investigation workspace
            </span>
          </div>
        </div>

        <button
          type="button"
          className="app-header-logout"
          onClick={handleLogout}
        >
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
}

export default Header;