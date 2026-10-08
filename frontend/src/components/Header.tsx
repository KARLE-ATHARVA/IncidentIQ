import { useNavigate } from "react-router-dom";

function Header() {
  const navigate = useNavigate();

  function handleLogout() {
    localStorage.removeItem("access_token");
    navigate("/login");
  }

  return (
    <header className="app-header">
      <div className="app-header-context">
        <span className="app-header-context-dot" />
        <span>Engineering incident intelligence</span>
      </div>

      <div className="app-header-user">
        <div className="app-header-user-info">
          <div className="app-header-user-copy">
            <span className="app-header-user-name">Signed in</span>
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
