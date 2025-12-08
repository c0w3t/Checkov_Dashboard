import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Badge,
  List,
  ListItem,
  ListItemText,
  Divider,
  Box,
} from '@mui/material';
import { Menu as MenuIcon, Notifications, AccountCircle, Logout, CheckCircle, Error } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';

interface HeaderProps {
  onMenuClick: () => void;
}

interface Notification {
  id: number;
  type: 'scan_completed' | 'scan_failed' | 'high_severity';
  message: string;
  scan_id?: number;
  project_id?: number;
  created_at: string;
  read: boolean;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notifAnchorEl, setNotifAnchorEl] = useState<null | HTMLElement>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    // Poll for notifications every 30 seconds
    const fetchNotifications = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/scans/?limit=10');
        const scans = response.data;
        
        // Generate notifications from recent scans
        const notifs: Notification[] = scans
          .filter((scan: any) => scan.status === 'completed' || scan.status === 'failed')
          .slice(0, 5)
          .map((scan: any, index: number) => ({
            id: index,
            type: scan.status === 'failed' ? 'scan_failed' : 
                  scan.failed_checks > 10 ? 'high_severity' : 'scan_completed',
            message: scan.status === 'failed' 
              ? `Scan #${scan.id} failed for Project ${scan.project_id}`
              : scan.failed_checks > 10
              ? `Scan #${scan.id} found ${scan.failed_checks} critical issues`
              : `Scan #${scan.id} completed - ${scan.failed_checks} issues found`,
            scan_id: scan.id,
            project_id: scan.project_id,
            created_at: scan.completed_at || scan.started_at,
            read: false,
          }));
        
        setNotifications(notifs);
      } catch (error) {
        console.error('Failed to fetch notifications:', error);
      }
    };

    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleNotifOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotifAnchorEl(event.currentTarget);
  };

  const handleNotifClose = () => {
    setNotifAnchorEl(null);
  };

  const handleNotificationClick = (notif: Notification) => {
    if (notif.scan_id) {
      navigate(`/scans/${notif.scan_id}`);
      handleNotifClose();
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    handleMenuClose();
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <AppBar 
      position="fixed" 
      sx={{ 
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: '#ffffff',
        color: '#2d3748',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      }}
    >
      <Toolbar>
        <IconButton
          color="inherit"
          edge="start"
          onClick={onMenuClick}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>
        
        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          Checkov Security Dashboard
        </Typography>

        <IconButton color="inherit" onClick={handleNotifOpen}>
          <Badge badgeContent={unreadCount} color="error">
            <Notifications />
          </Badge>
        </IconButton>

        <Menu
          anchorEl={notifAnchorEl}
          open={Boolean(notifAnchorEl)}
          onClose={handleNotifClose}
          PaperProps={{
            sx: { width: 400, maxHeight: 500 }
          }}
        >
          <Box sx={{ p: 2, pb: 1 }}>
            <Typography variant="h6">Notifications</Typography>
          </Box>
          <Divider />
          {notifications.length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                No notifications
              </Typography>
            </Box>
          ) : (
            <List sx={{ p: 0 }}>
              {notifications.map((notif) => (
                <ListItem
                  key={notif.id}
                  button
                  onClick={() => handleNotificationClick(notif)}
                  sx={{
                    '&:hover': { bgcolor: 'action.hover' },
                    borderLeft: notif.type === 'scan_failed' ? '4px solid #f44336' :
                                notif.type === 'high_severity' ? '4px solid #ff9800' :
                                '4px solid #4caf50',
                  }}
                >
                  <Box sx={{ mr: 2 }}>
                    {notif.type === 'scan_failed' ? (
                      <Error color="error" />
                    ) : (
                      <CheckCircle color="success" />
                    )}
                  </Box>
                  <ListItemText
                    primary={notif.message}
                    secondary={new Date(notif.created_at + 'Z').toLocaleString()}
                    primaryTypographyProps={{
                      fontSize: '0.875rem',
                      fontWeight: notif.read ? 'normal' : 'bold',
                    }}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Menu>
        
        <IconButton color="inherit" onClick={handleMenuOpen}>
          <AccountCircle />
        </IconButton>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
        >
          <MenuItem disabled>
            <Typography variant="body2">
              {user?.username} {user?.is_admin && '(Admin)'}
            </Typography>
          </MenuItem>
          <MenuItem onClick={handleLogout}>
            <Logout sx={{ mr: 1 }} fontSize="small" />
            Logout
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
