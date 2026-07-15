import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './layout/AppLayout';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { VulnerabilitiesListPage } from './pages/vulnerabilities/VulnerabilitiesListPage';
import { VulnerabilityDetailPage } from './pages/vulnerabilities/VulnerabilityDetailPage';
import { AssetsListPage } from './pages/assets/AssetsListPage';
import { AssetDetailPage } from './pages/assets/AssetDetailPage';
import { VULNERABILITY_READ_ROLES } from './api/endpoints/vulnerabilities';
import { ASSET_DETAIL_READ_ROLES } from './api/endpoints/assets';

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

        {/* GET /assets has no role check at all - any authenticated
            user - but its detail endpoints (summary/vulnerabilities)
            require ASSET_DETAIL_READ_ROLES, so only the detail route
            is role-gated here. */}
        <Route path="/assets" element={<AssetsListPage />} />
        <Route
          path="/assets/:id"
          element={
            <ProtectedRoute roles={ASSET_DETAIL_READ_ROLES}>
              <AssetDetailPage />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
