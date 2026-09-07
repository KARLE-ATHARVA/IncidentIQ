import { BrowserRouter, Route, Routes } from "react-router-dom";

import AppLayout from "./layouts/AppLayout";

import ProtectedRoute from "./components/ProtectedRoute";

import LoginPage from "./pages/LoginPage";

import DashboardPage from "./pages/DashboardPage";

import ProjectsPage from "./pages/ProjectsPage";

import IncidentsPage from "./pages/IncidentsPage";

import IncidentWorkspacePage from "./pages/IncidentWorkspacePage";


function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route
          path="/login"
          element={<LoginPage />}
        />

        <Route element={<ProtectedRoute />}>

          <Route element={<AppLayout />}>

            <Route
              path="/dashboard"
              element={<DashboardPage />}
            />

            <Route
              path="/projects"
              element={<ProjectsPage />}
            />

            <Route
              path="/projects/:projectId/incidents"
              element={<IncidentsPage />}
            />

            <Route
              path="/projects/:projectId/incidents/:incidentId"
              element={<IncidentWorkspacePage />}
            />

          </Route>

        </Route>

      </Routes>
    </BrowserRouter>
  );
}


export default App;