import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './layout/AppLayout';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { VulnerabilitiesListPage } from './pages/vulnerabilities/VulnerabilitiesListPage';
import { VulnerabilityDetailPage } from './pages/vulnerabilities/VulnerabilityDetailPage';
import { VULNERABILITY_READ_ROLES } from './api/endpoints/vulnerabilities';

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />

        <Route
          path="/vulnerabilities"
          element={
            <ProtectedRoute roles={VULNERABILITY_READ_ROLES}>
              <VulnerabilitiesListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vulnerabilities/:id"
          element={
            <ProtectedRoute roles={VULNERABILITY_READ_ROLES}>
              <VulnerabilityDetailPage />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
