import React from 'react';
import {
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText,
  ListItemButton,
  Divider,
  Box
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Folder as FolderIcon,
  Security as SecurityIcon,
  Assignment as AssignmentIcon,
  Settings as SettingsIcon,
  Policy as PolicyIcon
  , Notifications as NotificationsIcon
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Projects', icon: <FolderIcon />, path: '/projects' },
  { text: 'Scans', icon: <SecurityIcon />, path: '/scans' },
  { text: 'Reports', icon: <AssignmentIcon />, path: '/reports' },
  { text: 'Policies', icon: <PolicyIcon />, path: '/policies' },
  { text: 'Notifications', icon: <NotificationsIcon />, path: '/notifications' },
];

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  return (
    <Box
      sx={{
        width: '100%',
        height: '100vh',
        backgroundColor: '#2d3436',
        color: '#e2e8f0',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        zIndex: 1201,
        overflow: 'visible',
      }}
    >
      <Box sx={{ pt: 12, pb: 3, borderBottom: '1px solid rgba(255,255,255,0.1)', display: 'flex', flexDirection: 'column', alignItems: 'center', minHeight: 100, background: 'inherit' }}>
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            fontWeight: 800,
            fontSize: '1.5rem',
            boxShadow: '0 2px 8px 0 rgba(102,126,234,0.15)',
            marginTop: 0,
          }}
        >
          C
        </Box>
         {/* Bỏ chữ Checkov, chỉ giữ logo */}
      </Box>
      
      <Box sx={{ flex: 1, overflow: 'auto', py: 2 }}>
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => handleNavigation(item.path)}
                sx={{
                  mx: 1.5,
                  borderRadius: 2,
                  '&.Mui-selected': {
                    backgroundColor: '#667eea',
                    '&:hover': {
                      backgroundColor: '#5568d3',
                    },
                  },
                  '&:hover': {
                    backgroundColor: 'rgba(255,255,255,0.05)',
                  },
                }}
              >
                <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text}
                  primaryTypographyProps={{
                    fontSize: '0.9375rem',
                    fontWeight: 600,
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
        <Divider sx={{ my: 2, borderColor: 'rgba(255,255,255,0.1)' }} />
        <List>
          <ListItem disablePadding>
            <ListItemButton 
              onClick={() => handleNavigation('/settings')}
              sx={{
                mx: 1.5,
                borderRadius: 2,
                '&:hover': {
                  backgroundColor: 'rgba(255,255,255,0.05)',
                },
              }}
            >
              <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                <SettingsIcon />
              </ListItemIcon>
              <ListItemText 
                primary="Settings"
                primaryTypographyProps={{
                  fontSize: '0.875rem',
                  fontWeight: 500,
                }}
              />
            </ListItemButton>
          </ListItem>
        </List>
      </Box>
    </Box>
  );
};

export default Sidebar;
