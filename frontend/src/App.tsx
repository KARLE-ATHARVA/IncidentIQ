import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./layouts/AppLayout";

import ProtectedRoute from "./components/ProtectedRoute";

import LoginPage from "./pages/LoginPage";

import HomePage from "./pages/HomePage";

import DashboardPage from "./pages/DashboardPage";

import ProjectsPage from "./pages/ProjectsPage";

import IncidentsPage from "./pages/IncidentsPage";

import IncidentWorkspacePage from "./pages/IncidentWorkspacePage";

import ProductionSimulatorPage from "./pages/ProductionSimulatorPage";


function RootRedirect() {
  const token = localStorage.getItem("access_token");

  return (
    <Navigate
      to={token ? "/home" : "/login"}
      replace
    />
  );
}


function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route
          path="/"
          element={<RootRedirect />}
        />

        <Route
          path="/login"
          element={<LoginPage />}
        />

        <Route element={<ProtectedRoute />}>

          <Route element={<AppLayout />}>

            <Route
              path="/home"
              element={<HomePage />}
            />

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

            <Route
              path="/projects/:projectId/simulator"
              element={<ProductionSimulatorPage />}
            />

          </Route>

        </Route>

        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />

      </Routes>
    </BrowserRouter>
  );
}


export default App;
