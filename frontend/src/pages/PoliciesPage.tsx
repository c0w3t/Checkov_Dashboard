import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Tabs,
  Tab,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Chip,
  IconButton,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  ArrowBack as ArrowBackIcon,
  Security as SecurityIcon,
  AutoAwesome as AutoAwesomeIcon,
} from '@mui/icons-material';
import axios from 'axios';
import PolicyTable from '../components/Policies/PolicyTable';
import CreatePolicyDialog from '../components/Policies/CreatePolicyDialog';
import AIPolicyGenerator from '../components/AIPolicyGenerator';
import { SUPPORTED_FRAMEWORKS } from '../constants/frameworks';

interface Policy {
  check_id: string;
  name: string;
  platform: string;
  severity: string;
  built_in: boolean;
  category?: string;
  file_path?: string;
}

interface PlatformStats {
  platform: string;
  label: string;
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

const PoliciesPage: React.FC = () => {
  const [tab, setTab] = useState(0);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [aiGeneratorOpen, setAiGeneratorOpen] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);

  // Calculate platform statistics - separate built-in and custom
  const platformStats = useMemo(() => {
    const statsMap = new Map<string, PlatformStats & { builtIn: number; custom: number }>();
    
    let filteredPolicies = [...policies];
    
    // Filter by tab
    if (tab === 1) {
      filteredPolicies = filteredPolicies.filter((p) => p.built_in);
    } else if (tab === 2) {
      filteredPolicies = filteredPolicies.filter((p) => !p.built_in);
    }

    filteredPolicies.forEach((policy) => {
      const platform = policy.platform;
      if (!statsMap.has(platform)) {
        const framework = SUPPORTED_FRAMEWORKS.find(f => f.value === platform);
        statsMap.set(platform, {
          platform,
          label: framework?.label || platform,
          total: 0,
          critical: 0,
          high: 0,
          medium: 0,
          low: 0,
          builtIn: 0,
          custom: 0,
        });
      }

      const stats = statsMap.get(platform)!;
      stats.total++;
      
      if (policy.built_in) {
        stats.builtIn++;
      } else {
        stats.custom++;
      }
      
      const severity = policy.severity?.toLowerCase();
      if (severity === 'critical') stats.critical++;
      else if (severity === 'high') stats.high++;
      else if (severity === 'medium') stats.medium++;
      else if (severity === 'low') stats.low++;
    });

    return Array.from(statsMap.values()).sort((a, b) => b.total - a.total);
  }, [policies, tab]);

  // Filtered policies for detail view
  const filteredPolicies = useMemo(() => {
    if (!selectedPlatform) return [];
    
    let filtered = policies.filter(p => p.platform === selectedPlatform);

    // Filter by tab
    if (tab === 1) {
      filtered = filtered.filter((p) => p.built_in);
    } else if (tab === 2) {
      filtered = filtered.filter((p) => !p.built_in);
    }

    // Filter by search term
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.check_id.toLowerCase().includes(searchLower) ||
          p.name.toLowerCase().includes(searchLower)
      );
    }

    // Filter by severity
    if (severityFilter !== 'all') {
      filtered = filtered.filter((p) => p.severity && p.severity.toLowerCase() === severityFilter);
    }

    return filtered;
  }, [policies, selectedPlatform, tab, searchTerm, severityFilter]);

  // Memoize counts for tabs
  const builtInCount = useMemo(() => policies.filter((p) => p.built_in).length, [policies]);
  const customCount = useMemo(() => policies.filter((p) => !p.built_in).length, [policies]);

  const fetchPolicies = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      // Load both built-in and custom policies
      const [builtInRes, customRes] = await Promise.all([
        axios.get('http://localhost:8000/api/policies/built-in'),
        axios.get('http://localhost:8000/api/policies/custom').catch(() => ({ data: [] }))
      ]);
      setPolicies([...builtInRes.data, ...customRes.data]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load policies');
      console.error('Error loading policies:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPolicies();
  }, [fetchPolicies]);

  const handleDeletePolicy = useCallback(async (checkId: string, platform: string) => {
    if (!window.confirm(`Are you sure you want to delete policy ${checkId}?`)) {
      return;
    }

    try {
      await axios.delete(`http://localhost:8000/api/policies/custom/${checkId}?platform=${platform}`);
      fetchPolicies();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete policy');
    }
  }, [fetchPolicies]);

  const handleCreatePolicy = useCallback(async (policyData: any) => {
    try {
      await axios.post('http://localhost:8000/api/policies/custom/create', policyData);
      setCreateDialogOpen(false);
      fetchPolicies();
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to create policy');
    }
  }, [fetchPolicies]);

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {selectedPlatform && (
            <IconButton onClick={() => {
              setSelectedPlatform(null);
              setSearchTerm('');
              setSeverityFilter('all');
            }}>
              <ArrowBackIcon />
            </IconButton>
          )}
          <Typography variant="h4" fontWeight="bold">
            {selectedPlatform 
              ? SUPPORTED_FRAMEWORKS.find(f => f.value === selectedPlatform)?.label || selectedPlatform
              : 'Security Policies'}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<AutoAwesomeIcon />}
            onClick={() => setAiGeneratorOpen(true)}
            color="secondary"
          >
            AI Generate Policy
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Custom Policy
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3 }}>
        <Tabs value={tab} onChange={(_, newValue) => {
          setTab(newValue);
          setSelectedPlatform(null);
        }} sx={{ mb: 3 }}>
          <Tab label={`All (${policies.length})`} />
          <Tab label={`Built-in (${builtInCount})`} />
          <Tab label={`Custom (${customCount})`} />
        </Tabs>

        {!selectedPlatform ? (
          // Overview: Show platform cards
          <Grid container spacing={3}>
            {platformStats.map((stats) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={stats.platform}>
                <Card>
                  <CardActionArea onClick={() => setSelectedPlatform(stats.platform)}>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <SecurityIcon color="primary" sx={{ mr: 1 }} />
                        <Typography variant="h6" fontWeight="bold">
                          {stats.label}
                        </Typography>
                      </Box>
                      
                      <Typography variant="h3" color="primary" sx={{ mb: 2 }}>
                        {stats.total}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1.5 }}>
                        {stats.builtIn > 0 && (
                          <Chip 
                            label={`Built-in: ${stats.builtIn}`} 
                            size="small" 
                            variant="outlined"
                            color="primary"
                          />
                        )}
                        {stats.custom > 0 && (
                          <Chip 
                            label={`Custom: ${stats.custom}`} 
                            size="small" 
                            variant="outlined"
                            color="secondary"
                          />
                        )}
                      </Box>
                      
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {stats.critical > 0 && (
                          <Chip 
                            label={`Critical: ${stats.critical}`} 
                            size="small" 
                            color="error"
                          />
                        )}
                        {stats.high > 0 && (
                          <Chip 
                            label={`High: ${stats.high}`} 
                            size="small" 
                            color="warning"
                          />
                        )}
                        {stats.medium > 0 && (
                          <Chip 
                            label={`Medium: ${stats.medium}`} 
                            size="small" 
                            color="info"
                          />
                        )}
                        {stats.low > 0 && (
                          <Chip 
                            label={`Low: ${stats.low}`} 
                            size="small" 
                            color="success"
                          />
                        )}
                      </Box>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : (
          // Detail: Show policies for selected platform
          <Box>
            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <TextField
                placeholder="Search by ID or name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                sx={{ flex: 1 }}
              />

              <FormControl sx={{ minWidth: 150 }}>
                <InputLabel>Severity</InputLabel>
                <Select
                  value={severityFilter}
                  label="Severity"
                  onChange={(e) => setSeverityFilter(e.target.value)}
                >
                  <MenuItem value="all">All Severities</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="info">Info</MenuItem>
                </Select>
              </FormControl>
            </Box>

            <PolicyTable
              policies={filteredPolicies}
              loading={loading}
              onDelete={handleDeletePolicy}
            />
          </Box>
        )}
      </Paper>

      <CreatePolicyDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSave={handleCreatePolicy}
      />

      <AIPolicyGenerator
        open={aiGeneratorOpen}
        onClose={() => setAiGeneratorOpen(false)}
        onPolicyGenerated={() => {
          setAiGeneratorOpen(false);
          fetchPolicies();
        }}
      />
    </Box>
  );
};

export default PoliciesPage;
