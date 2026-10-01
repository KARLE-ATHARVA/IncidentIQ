import { Outlet } from "react-router-dom";

import Header from "../components/Header";
import Sidebar from "../components/Sidebar";

function AppLayout() {
  return (
    <>
      <Header />

      <div className="app-shell">
        <Sidebar />

        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </>
  );
}

export default AppLayout;