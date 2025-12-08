import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Add as AddIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import PolicyConfigList from '../components/Policies/PolicyConfigList';
import PolicyConfigDialog from '../components/Policies/PolicyConfigDialog';
import { policiesApi } from '../services/api';
import { PolicyConfig } from '../types';
import { SUPPORTED_FRAMEWORKS } from '../constants/frameworks';

const PolicyConfigPage: React.FC = () => {
  const [policies, setPolicies] = useState<PolicyConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyConfig | null>(null);
  
  // Filters
  const [filterType, setFilterType] = useState<string>('');
  const [filterEnabled, setFilterEnabled] = useState<string>('');
  const [filterProjectId, setFilterProjectId] = useState<string>('');

  const loadPolicies = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params: any = {};
      if (filterType) params.policy_type = filterType;
      if (filterEnabled !== '') params.enabled = filterEnabled === 'true';
      if (filterProjectId) params.project_id = parseInt(filterProjectId);
      
      const response = await policiesApi.getAll(params);
      setPolicies(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load policies');
      console.error('Error loading policies:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, [filterType, filterEnabled, filterProjectId]);

  const handleAdd = () => {
    setSelectedPolicy(null);
    setDialogOpen(true);
  };

  const handleEdit = (policy: PolicyConfig) => {
    setSelectedPolicy(policy);
    setDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this policy configuration?')) {
      return;
    }

    try {
      await policiesApi.delete(id);
      await loadPolicies();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete policy');
      console.error('Error deleting policy:', err);
    }
  };

  const handleToggle = async (id: number, enabled: boolean) => {
    try {
      await policiesApi.update(id, { enabled });
      await loadPolicies();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update policy');
      console.error('Error updating policy:', err);
    }
  };

  const handleSave = async (data: any) => {
    try {
      if (selectedPolicy) {
        await policiesApi.update(selectedPolicy.id, data);
      } else {
        await policiesApi.create(data);
      }
      setDialogOpen(false);
      await loadPolicies();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save policy');
      console.error('Error saving policy:', err);
    }
  };

  const handleClearFilters = () => {
    setFilterType('');
    setFilterEnabled('');
    setFilterProjectId('');
  };

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Policy Configuration
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadPolicies}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAdd}
          >
            Add Policy
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Filters
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Policy Type</InputLabel>
              <Select
                value={filterType}
                label="Policy Type"
                onChange={(e) => setFilterType(e.target.value)}
              >
                <MenuItem value="">
                  <em>All</em>
                </MenuItem>
                {SUPPORTED_FRAMEWORKS.map(fw => (
                  <MenuItem key={fw.value} value={fw.value}>{fw.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={filterEnabled}
                label="Status"
                onChange={(e) => setFilterEnabled(e.target.value)}
              >
                <MenuItem value="">
                  <em>All</em>
                </MenuItem>
                <MenuItem value="true">Enabled</MenuItem>
                <MenuItem value="false">Disabled</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              label="Project ID"
              value={filterProjectId}
              onChange={(e) => setFilterProjectId(e.target.value)}
              type="number"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              onClick={handleClearFilters}
              sx={{ height: '40px' }}
            >
              Clear Filters
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Policy List */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <PolicyConfigList
          policies={policies}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onToggle={handleToggle}
        />
      )}

      {/* Add/Edit Dialog */}
      <PolicyConfigDialog
        open={dialogOpen}
        policy={selectedPolicy}
        onClose={() => setDialogOpen(false)}
        onSave={handleSave}
      />
    </Box>
  );
};

export default PolicyConfigPage;
