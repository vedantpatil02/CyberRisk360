import { useState } from 'react';
import { Badge, Box, Divider, IconButton, Menu, MenuItem, Tooltip, Typography } from '@mui/material';
import NotificationsIcon from '@mui/icons-material/Notifications';
import { useNavigate } from 'react-router-dom';
import { useNotifications } from '../hooks/useNotifications';
import type { Notification } from '../api/types/notification';

// entity_type -> route segment (plain pluralization would turn
// "vulnerability" into "vulnerabilitys").
const ENTITY_ROUTES: Record<Notification['entity_type'], string> = {
  vulnerability: 'vulnerabilities',
  risk: 'risks',
};

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString();
}

export function NotificationBell() {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();
  const { data: notifications } = useNotifications();
  const count = notifications?.length ?? 0;

  return (
    <>
      <Tooltip title="Notifications">
        <IconButton color="inherit" onClick={(e) => setAnchorEl(e.currentTarget)}>
          <Badge badgeContent={count} color="error">
            <NotificationsIcon />
          </Badge>
        </IconButton>
      </Tooltip>
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
        {count === 0 && (
          <MenuItem disabled>
            <Typography variant="body2" color="text.secondary">
              No notifications
            </Typography>
          </MenuItem>
        )}
        {notifications?.map((notification, index) => (
          <Box key={`${notification.entity_type}-${notification.entity_id}-${index}`}>
            {index > 0 && <Divider />}
            <MenuItem
              onClick={() => {
                setAnchorEl(null);
                navigate(`/${ENTITY_ROUTES[notification.entity_type]}/${notification.entity_id}`);
              }}
              sx={{ display: 'block', maxWidth: 320 }}
            >
              <Typography variant="body2">{notification.message}</Typography>
              <Typography variant="caption" color="text.secondary">
                {notification.type === 'evidence_expired' ? 'Expired' : 'Expires'}{' '}
                {formatDate(notification.expires_at)}
              </Typography>
            </MenuItem>
          </Box>
        ))}
      </Menu>
    </>
  );
}
