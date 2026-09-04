import { useNavigate } from "react-router-dom";

function Header() {
  const navigate = useNavigate();

  function handleLogout() {
    localStorage.removeItem("access_token");
    navigate("/login");
  }

  return (
    <header>
      <div>
        <strong>IncidentIQ</strong>
      </div>

      <div>
        <span>Engineer</span>

        <button onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}

export default Header;