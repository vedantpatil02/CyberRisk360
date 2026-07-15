import { Drawer, List, ListItemButton, ListItemIcon, ListItemText, Toolbar } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import BugReportIcon from '@mui/icons-material/BugReport';
import StorageIcon from '@mui/icons-material/Storage';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { hasRole } from '../api/types/auth';
import { VULNERABILITY_READ_ROLES } from '../api/endpoints/vulnerabilities';
import { RISK_READ_ROLES } from '../api/endpoints/risks';

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
