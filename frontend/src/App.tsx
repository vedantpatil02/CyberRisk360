import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './layout/AppLayout';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { AccountPage } from './pages/AccountPage';
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
import { ReportsLandingPage } from './pages/reports/ReportsLandingPage';
import { ExecutiveReportPage } from './pages/reports/ExecutiveReportPage';
import { TechnicalReportPage } from './pages/reports/TechnicalReportPage';
import { ComplianceReportPage } from './pages/reports/ComplianceReportPage';
import { AuditsListPage } from './pages/audits/AuditsListPage';
import { AuditDetailPage } from './pages/audits/AuditDetailPage';
import { UsersListPage } from './pages/users/UsersListPage';
import { ExecutiveDashboardPage } from './pages/dashboards/ExecutiveDashboardPage';
import { GrcDashboardLandingPage } from './pages/dashboards/GrcDashboardLandingPage';
import { GrcDashboardPage } from './pages/dashboards/GrcDashboardPage';
import { OrganizationsListPage } from './pages/organizations/OrganizationsListPage';
import { MappingReviewPage } from './pages/mappings/MappingReviewPage';
import { ImportReportPage } from './pages/imports/ImportReportPage';
import { VULNERABILITY_READ_ROLES } from './api/endpoints/vulnerabilities';
import { ASSET_DETAIL_READ_ROLES } from './api/endpoints/assets';
import { RISK_READ_ROLES } from './api/endpoints/risks';
import { FRAMEWORK_READ_ROLES } from './api/endpoints/frameworks';
import { USER_MANAGEMENT_ROLES } from './api/endpoints/users';
import { ORGANIZATION_MANAGEMENT_ROLES } from './api/endpoints/organizations';
import { MAPPING_READ_ROLES } from './api/endpoints/mappings';
import { IMPORT_WRITE_ROLES } from './api/endpoints/imports';

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/account" element={<AccountPage />} />

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

        {/* GET /reports/* all use require_role(*READ_ROLES) where
            READ_ROLES = ALL_ROLES - no restriction beyond being
            authenticated, same tier as /assets and /dashboard, so no
            `roles` prop here either. */}
        <Route path="/reports" element={<ReportsLandingPage />} />
        <Route path="/reports/executive" element={<ExecutiveReportPage />} />
        <Route path="/reports/technical" element={<TechnicalReportPage />} />
        <Route path="/reports/compliance/:shortName" element={<ComplianceReportPage />} />

        {/* GET /audits and GET /audits/{id} both use require_role(*READ_ROLES)
            where READ_ROLES = ALL_ROLES - no restriction beyond being
            authenticated, same tier as /assets and /dashboard, so no
            `roles` prop here either. */}
        <Route path="/audits" element={<AuditsListPage />} />
        <Route path="/audits/:id" element={<AuditDetailPage />} />

        {/* GET /dashboard/executive and GET /dashboard/grc/{framework}
            both use require_role(*READ_ROLES) where READ_ROLES =
            ALL_ROLES - no restriction beyond authentication, same tier
            as /reports and /audits, so no `roles` prop here either. */}
        <Route path="/executive-dashboard" element={<ExecutiveDashboardPage />} />
        <Route path="/grc-dashboard" element={<GrcDashboardLandingPage />} />
        <Route path="/grc-dashboard/:shortName" element={<GrcDashboardPage />} />

        <Route
          path="/users"
          element={
            <ProtectedRoute roles={USER_MANAGEMENT_ROLES}>
              <UsersListPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/organizations"
          element={
            <ProtectedRoute roles={ORGANIZATION_MANAGEMENT_ROLES}>
              <OrganizationsListPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/mappings/review"
          element={
            <ProtectedRoute roles={MAPPING_READ_ROLES}>
              <MappingReviewPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/imports"
          element={
            <ProtectedRoute roles={IMPORT_WRITE_ROLES}>
              <ImportReportPage />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
