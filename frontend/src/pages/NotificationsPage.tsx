import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Divider,
  MenuItem,
  TextField,
  Chip,
  CircularProgress,
} from '@mui/material';
import { projectsApi, notificationsApi } from '../services/api';
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

interface NotificationItem {
  id: number;
  project_id: number;
  scan_id?: number | null;
  notification_type: string; // e.g., scan_completed, summary, failed
  subject: string;
  recipients: string[];
  sent_at: string; // ISO datetime from backend
  status: string; // sent|failed|queued
  critical_count?: number;
  high_count?: number;
  fixed_count?: number;
  new_count?: number;
}

const statusColorMap: Record<string, 'success' | 'default' | 'warning' | 'error'> = {
  success: 'success',
  info: 'default',
  warning: 'warning',
  error: 'error',
};

const NotificationsPage: React.FC = () => {
  const [projects, setProjects] = useState<Array<{ id: number; name: string }>>([]);
  const [projectId, setProjectId] = useState<number | ''>('');
  const [useGlobal, setUseGlobal] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [items, setItems] = useState<NotificationItem[]>([]);

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const res = await projectsApi.getAll();
        const list = (res.data || []).map((p: any) => ({ id: p.id, name: p.name }));
        setProjects(list);
        if (list.length > 0) {
          setProjectId(list[0].id);
        }
      } catch (e) {
        // ignore
      }
    };
    loadProjects();
  }, []);

  useEffect(() => {
    const loadNotifications = async () => {
      if (!useGlobal && !projectId) return;
      setLoading(true);
      try {
        const res = useGlobal
          ? await notificationsApi.getGlobalHistory(100)
          : await notificationsApi.getHistory(projectId as number, 100);
        const history = res.data || [];
        setItems(history);
      } catch (e) {
        setItems([]);
      } finally {
        setLoading(false);
      }
    };
    loadNotifications();
  }, [projectId, useGlobal]);

  const projectName = (pid?: number) => projects.find(p => p.id === pid)?.name || 'Unknown project';

  return (
    <Box>
      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
        <NotificationsNoneIcon color="primary" />
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Notifications
        </Typography>
      </Stack>

      <Card sx={{ mb: 3, borderRadius: 3, boxShadow: '0 6px 16px rgba(102,126,234,0.15)' }}>
        <CardContent>
          <Stack direction="row" spacing={2} alignItems="center">
            <TextField
              select
              size="small"
              label="Scope"
              value={useGlobal ? 'all' : 'project'}
              onChange={(e) => setUseGlobal(e.target.value === 'all')}
              sx={{ minWidth: 180 }}
            >
              <MenuItem value="all">All projects</MenuItem>
              <MenuItem value="project">Specific project</MenuItem>
            </TextField>
            <TextField
              select
              size="small"
              label="Project"
              value={projectId}
              onChange={(e) => setProjectId(Number(e.target.value))}
              sx={{ minWidth: 240 }}
              disabled={useGlobal}
            >
              {projects.map((p) => (
                <MenuItem key={p.id} value={p.id}>
                  {p.name}
                </MenuItem>
              ))}
            </TextField>
          </Stack>
        </CardContent>
      </Card>

      <Card sx={{ borderRadius: 3, boxShadow: '0 8px 24px rgba(118,75,162,0.12)' }}>
        <CardContent sx={{ pt: 1 }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress size={24} />
            </Box>
          ) : items.length === 0 ? (
            <Stack direction="row" spacing={1} alignItems="center" color="text.secondary">
              <InfoOutlinedIcon fontSize="small" />
              <Typography>No notifications yet.</Typography>
            </Stack>
          ) : (
            <Stack divider={<Divider flexItem sx={{ borderColor: '#eee' }} />} spacing={2}>
              {items.map((n, idx) => (
                <Box key={n.id ?? idx} sx={{ p: 1 }}>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    {n.status === 'sent' ? (
                      <CheckCircleIcon sx={{ color: '#38b2ac' }} fontSize="small" />
                    ) : n.status === 'failed' ? (
                      <ErrorOutlineIcon sx={{ color: '#e53e3e' }} fontSize="small" />
                    ) : (
                      <InfoOutlinedIcon sx={{ color: '#667eea' }} fontSize="small" />
                    )}
                    <Typography sx={{ fontWeight: 600 }}>
                      {n.subject || 'Notification'}
                    </Typography>
                    {n.notification_type && (
                      <Chip
                        size="small"
                        label={n.notification_type}
                        sx={{
                          bgcolor:
                            n.notification_type === 'scan_completed' ? 'rgba(102,126,234,0.15)'
                            : n.notification_type === 'push_success' ? 'rgba(56,178,172,0.15)'
                            : n.notification_type === 'push_failed' ? 'rgba(229,62,62,0.15)'
                            : n.notification_type === 'files_uploaded' ? 'rgba(246,173,85,0.15)'
                            : n.notification_type === 'file_changed' ? 'rgba(237,100,166,0.15)'
                            : 'rgba(160,174,192,0.20)',
                          border: '1px solid rgba(255,255,255,0.2)'
                        }}
                        variant="filled"
                      />
                    )}
                    <Chip size="small" label={projectName(n.project_id)} sx={{ bgcolor: 'rgba(118,75,162,0.12)' }} />
                    <Box sx={{ flexGrow: 1 }} />
                    <Typography variant="body2" color="text.secondary">
                      {n.sent_at
                        ? new Intl.DateTimeFormat('vi-VN', {
                            year: 'numeric', month: '2-digit', day: '2-digit',
                            hour: '2-digit', minute: '2-digit', second: '2-digit',
                            hour12: false, timeZone: 'Asia/Ho_Chi_Minh'
                          }).format(new Date(n.sent_at))
                        : ''}
                    </Typography>
                  </Stack>
                </Box>
              ))}
            </Stack>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default NotificationsPage;
