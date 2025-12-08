import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Tabs,
  Tab,
  Typography,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Grid,
  Chip,
  Alert,
  Snackbar,
  Card,
  CardContent,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Email as EmailIcon,
  Send as SendIcon,
  Add as AddIcon,
  Notifications as NotificationsIcon,
} from '@mui/icons-material';
import { notificationsApi, projectsApi } from '../services/api';
import { Project } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

interface NotificationSettings {
  id?: number;
  project_id: number;
  critical_recipients: string[];
  summary_recipients: string[];
  weekly_recipients: string[];
  critical_immediate_enabled: boolean;
  scan_summary_enabled: boolean;
  weekly_summary_enabled: boolean;
  scan_failed_enabled: boolean;
  critical_threshold: number;
  high_threshold: number;
  fixed_threshold: number;
  summary_send_when: string;
  summary_include_fixed: boolean;
  summary_include_new: boolean;
  summary_include_still_open: boolean;
  weekly_day: string;
  weekly_time: string;
  weekly_include_trends: boolean;
  digest_mode: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string;
  quiet_hours_end: string;
}

const SettingsPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  // Email input states
  const [newCriticalEmail, setNewCriticalEmail] = useState('');
  const [newSummaryEmail, setNewSummaryEmail] = useState('');

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadNotificationSettings(selectedProjectId);
    }
  }, [selectedProjectId]);

  const loadProjects = async () => {
    try {
      const response = await projectsApi.getAll();
      setProjects(response.data);
      if (response.data.length > 0 && !selectedProjectId) {
        setSelectedProjectId(response.data[0].id);
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
      showSnackbar('Failed to load projects', 'error');
    }
  };

  const loadNotificationSettings = async (projectId: number) => {
    setLoading(true);
    try {
      const response = await notificationsApi.getSettings(projectId);
      setSettings(response.data);
    } catch (error) {
      console.error('Failed to load settings:', error);
      showSnackbar('Failed to load notification settings', 'error');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    if (!selectedProjectId || !settings) return;

    setLoading(true);
    try {
      await notificationsApi.updateSettings(selectedProjectId, settings);
      showSnackbar('Settings saved successfully!', 'success');
    } catch (error) {
      console.error('Failed to save settings:', error);
      showSnackbar('Failed to save settings', 'error');
    } finally {
      setLoading(false);
    }
  };

  const sendTestEmail = async (type: 'critical' | 'summary') => {
    if (!selectedProjectId) return;

    setLoading(true);
    try {
      await notificationsApi.sendTest(selectedProjectId, type);
      showSnackbar(`Test ${type} email sent successfully!`, 'success');
    } catch (error: any) {
      console.error('Failed to send test email:', error);
      const message = error.response?.data?.detail || 'Failed to send test email';
      showSnackbar(message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleAddEmail = (type: 'critical' | 'summary') => {
    if (!settings) return;

    let email = '';
    let field: keyof Pick<NotificationSettings, 'critical_recipients' | 'summary_recipients'>;

    if (type === 'critical') {
      email = newCriticalEmail;
      field = 'critical_recipients';
      setNewCriticalEmail('');
    } else {
      email = newSummaryEmail;
      field = 'summary_recipients';
      setNewSummaryEmail('');
    }

    if (!email || !email.includes('@')) {
      showSnackbar('Please enter a valid email address', 'error');
      return;
    }

    if (settings[field].includes(email)) {
      showSnackbar('Email already added', 'error');
      return;
    }

    setSettings({
      ...settings,
      [field]: [...settings[field], email],
    });
  };

  const handleRemoveEmail = (type: keyof Pick<NotificationSettings, 'critical_recipients' | 'summary_recipients'>, email: string) => {
    if (!settings) return;

    setSettings({
      ...settings,
      [type]: settings[type].filter(e => e !== email),
    });
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (!settings) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Loading settings...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
        Settings
      </Typography>

      {/* Project Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <FormControl fullWidth>
            <InputLabel>Select Project</InputLabel>
            <Select
              value={selectedProjectId || ''}
              onChange={(e) => setSelectedProjectId(Number(e.target.value))}
              label="Select Project"
            >
              {projects.map((project) => (
                <MenuItem key={project.id} value={project.id}>
                  {project.name} ({project.framework})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </CardContent>
      </Card>

      <Paper sx={{ width: '100%' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="settings tabs">
          <Tab icon={<EmailIcon />} label="Email Notifications" />
          <Tab icon={<NotificationsIcon />} label="Notification Rules" />
        </Tabs>

        {/* Email Notifications Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            {/* Critical Recipients */}
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    🔴 Critical Alert Recipients
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Receive immediate alerts for CRITICAL vulnerabilities and scan failures
                  </Typography>

                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <TextField
                      fullWidth
                      size="small"
                      placeholder="email@example.com"
                      value={newCriticalEmail}
                      onChange={(e) => setNewCriticalEmail(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddEmail('critical')}
                    />
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={() => handleAddEmail('critical')}
                    >
                      Add
                    </Button>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {settings.critical_recipients.map((email) => (
                      <Chip
                        key={email}
                        label={email}
                        onDelete={() => handleRemoveEmail('critical_recipients', email)}
                        color="error"
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Summary Recipients */}
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    📊 Scan Summary Recipients
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Receive detailed summaries after each scan (Fixed/New/Still Open)
                  </Typography>

                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <TextField
                      fullWidth
                      size="small"
                      placeholder="email@example.com"
                      value={newSummaryEmail}
                      onChange={(e) => setNewSummaryEmail(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddEmail('summary')}
                    />
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={() => handleAddEmail('summary')}
                    >
                      Add
                    </Button>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {settings.summary_recipients.map((email) => (
                      <Chip
                        key={email}
                        label={email}
                        onDelete={() => handleRemoveEmail('summary_recipients', email)}
                        color="primary"
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Test Buttons */}
            <Grid item xs={12}>
              <Card variant="outlined" sx={{ bgcolor: '#f5f7fa' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    🧪 Test Email Notifications
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Send test emails to verify your configuration
                  </Typography>

                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<SendIcon />}
                      onClick={() => sendTestEmail('critical')}
                      disabled={loading || settings.critical_recipients.length === 0}
                    >
                      Test Critical Alert
                    </Button>
                    <Button
                      variant="outlined"
                      color="primary"
                      startIcon={<SendIcon />}
                      onClick={() => sendTestEmail('summary')}
                      disabled={loading || settings.summary_recipients.length === 0}
                    >
                      Test Scan Summary
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Notification Rules Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            {/* Enable/Disable Notifications */}
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Toggle Notifications
                  </Typography>
                  <Divider sx={{ my: 2 }} />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.critical_immediate_enabled}
                        onChange={(e) =>
                          setSettings({ ...settings, critical_immediate_enabled: e.target.checked })
                        }
                      />
                    }
                    label="🔴 Critical Immediate Alerts"
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 5, mb: 2 }}>
                    Send immediate alerts when CRITICAL vulnerabilities are detected
                  </Typography>

                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.scan_summary_enabled}
                        onChange={(e) =>
                          setSettings({ ...settings, scan_summary_enabled: e.target.checked })
                        }
                      />
                    }
                    label="📊 Scan Summaries"
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 5, mb: 2 }}>
                    Send detailed summary after each scan completes
                  </Typography>

                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.scan_failed_enabled}
                        onChange={(e) =>
                          setSettings({ ...settings, scan_failed_enabled: e.target.checked })
                        }
                      />
                    }
                    label="❌ Scan Failure Alerts"
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 5 }}>
                    Send alerts when scans fail
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Thresholds */}
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Notification Thresholds
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Set minimum counts to trigger notifications
                  </Typography>
                  <Divider sx={{ my: 2 }} />

                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        type="number"
                        label="Critical Threshold"
                        value={settings.critical_threshold}
                        onChange={(e) =>
                          setSettings({ ...settings, critical_threshold: parseInt(e.target.value) || 1 })
                        }
                        helperText="Min CRITICAL vulns to alert"
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        type="number"
                        label="High Threshold"
                        value={settings.high_threshold}
                        onChange={(e) =>
                          setSettings({ ...settings, high_threshold: parseInt(e.target.value) || 5 })
                        }
                        helperText="Min HIGH vulns to alert"
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        type="number"
                        label="Fixed Threshold"
                        value={settings.fixed_threshold}
                        onChange={(e) =>
                          setSettings({ ...settings, fixed_threshold: parseInt(e.target.value) || 1 })
                        }
                        helperText="Min fixed vulns to include"
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* Summary Options */}
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Scan Summary Options
                  </Typography>
                  <Divider sx={{ my: 2 }} />

                  <FormControl fullWidth sx={{ mb: 3 }}>
                    <InputLabel>Send Summary When</InputLabel>
                    <Select
                      value={settings.summary_send_when}
                      label="Send Summary When"
                      onChange={(e) =>
                        setSettings({ ...settings, summary_send_when: e.target.value })
                      }
                    >
                      <MenuItem value="has_changes">Has Changes (Fixed or New)</MenuItem>
                      <MenuItem value="always">Always (After Every Scan)</MenuItem>
                      <MenuItem value="has_critical_high">Has Critical or High Issues</MenuItem>
                    </Select>
                  </FormControl>

                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.summary_include_fixed}
                        onChange={(e) =>
                          setSettings({ ...settings, summary_include_fixed: e.target.checked })
                        }
                      />
                    }
                    label="Include Fixed Vulnerabilities"
                  />
                  <br />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.summary_include_new}
                        onChange={(e) =>
                          setSettings({ ...settings, summary_include_new: e.target.checked })
                        }
                      />
                    }
                    label="Include New Vulnerabilities"
                  />
                  <br />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.summary_include_still_open}
                        onChange={(e) =>
                          setSettings({ ...settings, summary_include_still_open: e.target.checked })
                        }
                      />
                    }
                    label="Include Still-Open Vulnerabilities"
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Save Button */}
        <Box sx={{ p: 3, borderTop: 1, borderColor: 'divider', bgcolor: '#f5f7fa' }}>
          <Button
            variant="contained"
            size="large"
            onClick={saveSettings}
            disabled={loading}
            sx={{ minWidth: 200 }}
          >
            {loading ? 'Saving...' : 'Save Settings'}
          </Button>
        </Box>
      </Paper>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SettingsPage;
