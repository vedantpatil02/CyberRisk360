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
import { RisksListPage } from './pages/risks/RisksListPage';
import { RiskDetailPage } from './pages/risks/RiskDetailPage';
import { FrameworksListPage } from './pages/frameworks/FrameworksListPage';
import { FrameworkDetailPage } from './pages/frameworks/FrameworkDetailPage';
import { VULNERABILITY_READ_ROLES } from './api/endpoints/vulnerabilities';
import { ASSET_DETAIL_READ_ROLES } from './api/endpoints/assets';
import { RISK_READ_ROLES } from './api/endpoints/risks';
import { FRAMEWORK_READ_ROLES } from './api/endpoints/frameworks';

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

        <Route
          path="/risks"
          element={
            <ProtectedRoute roles={RISK_READ_ROLES}>
              <RisksListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/risks/:id"
          element={
            <ProtectedRoute roles={RISK_READ_ROLES}>
              <RiskDetailPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/frameworks"
          element={
            <ProtectedRoute roles={FRAMEWORK_READ_ROLES}>
              <FrameworksListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/frameworks/:shortName"
          element={
            <ProtectedRoute roles={FRAMEWORK_READ_ROLES}>
              <FrameworkDetailPage />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
