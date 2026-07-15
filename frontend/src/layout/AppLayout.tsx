import { AppBar, Box, IconButton, Toolbar, Typography, Tooltip } from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';
import { Outlet } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { NavDrawer } from './NavDrawer';

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap sx={{ flexGrow: 1 }}>
            CyberRisk360
          </Typography>
          {user && (
            <>
              <Typography variant="body2" sx={{ mr: 2 }}>
                {user.email} ({user.role})
              </Typography>
              <Tooltip title="Log out">
                <IconButton color="inherit" onClick={logout}>
                  <LogoutIcon />
                </IconButton>
              </Tooltip>
            </>
          )}
        </Toolbar>
      </AppBar>
      <NavDrawer />
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
