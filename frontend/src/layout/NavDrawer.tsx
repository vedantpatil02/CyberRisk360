import { Drawer, List, ListItemButton, ListItemIcon, ListItemText, Toolbar } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import BugReportIcon from '@mui/icons-material/BugReport';
import StorageIcon from '@mui/icons-material/Storage';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import RuleIcon from '@mui/icons-material/Rule';
import AssessmentIcon from '@mui/icons-material/Assessment';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import PeopleIcon from '@mui/icons-material/People';
import InsightsIcon from '@mui/icons-material/Insights';
import GppGoodIcon from '@mui/icons-material/GppGood';
import CorporateFareIcon from '@mui/icons-material/CorporateFare';
import FactCheckOutlinedIcon from '@mui/icons-material/FactCheckOutlined';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { hasRole } from '../api/types/auth';
import { VULNERABILITY_READ_ROLES } from '../api/endpoints/vulnerabilities';
import { RISK_READ_ROLES } from '../api/endpoints/risks';
import { FRAMEWORK_READ_ROLES } from '../api/endpoints/frameworks';
import { USER_MANAGEMENT_ROLES } from '../api/endpoints/users';
import { ORGANIZATION_MANAGEMENT_ROLES } from '../api/endpoints/organizations';
import { MAPPING_READ_ROLES } from '../api/endpoints/mappings';
import { IMPORT_WRITE_ROLES } from '../api/endpoints/imports';

const DRAWER_WIDTH = 240;

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  // Omit to show for any authenticated user.
  visible: boolean;
}

export function NavDrawer() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const items: NavItem[] = [
    {
      label: 'Dashboard',
      path: '/dashboard',
      icon: <DashboardIcon />,
      // GET /dashboard/overview has no role check at all - visible to
      // any authenticated user.
      visible: true,
    },
    {
      label: 'Vulnerabilities',
      path: '/vulnerabilities',
      icon: <BugReportIcon />,
      visible: user !== null && hasRole(user.role, VULNERABILITY_READ_ROLES),
    },
    {
      label: 'Assets',
      path: '/assets',
      icon: <StorageIcon />,
      // GET /assets has no role check at all - visible to any
      // authenticated user (its detail view is separately role-gated
      // in App.tsx via ASSET_DETAIL_READ_ROLES).
      visible: true,
    },
    {
      label: 'Risks',
      path: '/risks',
      icon: <WarningAmberIcon />,
      visible: user !== null && hasRole(user.role, RISK_READ_ROLES),
    },
    {
      label: 'Frameworks',
      path: '/frameworks',
      icon: <RuleIcon />,
      visible: user !== null && hasRole(user.role, FRAMEWORK_READ_ROLES),
    },
    {
      label: 'Reports',
      path: '/reports',
      icon: <AssessmentIcon />,
      // GET /reports/* has no role check beyond authentication (same
      // tier as Dashboard/Assets) - visible to any authenticated user.
      visible: true,
    },
    {
      label: 'Audits',
      path: '/audits',
      icon: <FactCheckIcon />,
      // GET /audits has no role check beyond authentication (same
      // tier as Dashboard/Assets/Reports) - visible to any
      // authenticated user (write actions are separately gated to
      // OVERSIGHT_ROLES on the page itself).
      visible: true,
    },
    {
      label: 'Executive Dashboard',
      path: '/executive-dashboard',
      icon: <InsightsIcon />,
      // GET /dashboard/executive has no role check beyond
      // authentication - visible to any authenticated user.
      visible: true,
    },
    {
      label: 'GRC Dashboard',
      path: '/grc-dashboard',
      icon: <GppGoodIcon />,
      // GET /dashboard/grc/{framework} has no role check beyond
      // authentication - visible to any authenticated user.
      visible: true,
    },
    {
      label: 'Mapping Review',
      path: '/mappings/review',
      icon: <FactCheckOutlinedIcon />,
      visible: user !== null && hasRole(user.role, MAPPING_READ_ROLES),
    },
    {
      label: 'Import Report',
      path: '/imports',
      icon: <UploadFileIcon />,
      visible: user !== null && hasRole(user.role, IMPORT_WRITE_ROLES),
    },
    {
      label: 'Users',
      path: '/users',
      icon: <PeopleIcon />,
      visible: user !== null && hasRole(user.role, USER_MANAGEMENT_ROLES),
    },
    {
      label: 'Organizations',
      path: '/organizations',
      icon: <CorporateFareIcon />,
      visible: user !== null && hasRole(user.role, ORGANIZATION_MANAGEMENT_ROLES),
    },
  ];

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: { width: DRAWER_WIDTH, boxSizing: 'border-box' },
      }}
    >
      <Toolbar />
      <List>
        {items
          .filter((item) => item.visible)
          .map((item) => (
            <ListItemButton
              key={item.path}
              selected={location.pathname.startsWith(item.path)}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
      </List>
    </Drawer>
  );
}
