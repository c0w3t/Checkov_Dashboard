import React, { useState, useEffect } from 'react';
import { Box, Grid, CircularProgress, Typography } from '@mui/material';
import {
  Folder,
  Security,
  Warning,
  CheckCircle
} from '@mui/icons-material';
import StatsCard from '../components/Dashboard/StatsCard';
import SeverityChart from '../components/Dashboard/SeverityChart';
import VulnerabilityByProject from '../components/Dashboard/VulnerabilityByProject';
import RecentScans from '../components/Dashboard/RecentScans';
import { dashboardApi } from '../services/api';
import { DashboardStats } from '../types';

const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await dashboardApi.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!stats) {
    return <Box>Failed to load dashboard data</Box>;
  }

  const totalVulnerabilities = Object.values(stats.vulnerabilities).reduce((a, b) => a + b, 0);

  return (
    <Box sx={{ display: 'flex', gap: 3, height: 'calc(100vh - 100px)' }}>
      {/* Center Column - Main Content */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 3, minWidth: 0 }}>
        {/* Header */}
        <Box>
          <Typography variant="h4" fontWeight="800" sx={{ mb: 1, color: '#1a202c', letterSpacing: '-0.5px' }}>
            Security Dashboard
          </Typography>
          <Typography variant="body1" sx={{ color: '#718096', fontSize: '0.938rem' }}>
            Overview of your infrastructure security status
          </Typography>
        </Box>

        {/* Stats Cards */}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard
              title="Total Projects"
              value={stats.projects.total_projects}
              icon={<Folder />}
              gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard
              title="Total Scans"
              value={stats.scans.total_scans}
              icon={<Security />}
              gradient="linear-gradient(135deg, #06beb6 0%, #48b1bf 100%)"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard
              title="Vulnerabilities"
              value={totalVulnerabilities}
              icon={<Warning />}
              gradient="linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatsCard
              title="Pass Rate"
              value={`${stats.scans.average_pass_rate}%`}
              icon={<CheckCircle />}
              gradient="linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
            />
          </Grid>
        </Grid>

        {/* Recent Scans */}
        <Box sx={{ flex: 1, minHeight: 0 }}>
          <RecentScans scans={stats.recent_scans} />
        </Box>
      </Box>

      {/* Right Column - Charts */}
      <Box sx={{ width: 400, display: 'flex', flexDirection: 'column', gap: 3 }}>
        <Box sx={{ flex: 1 }}>
          <SeverityChart data={stats.vulnerabilities} />
        </Box>
        <Box sx={{ flex: 1 }}>
          <VulnerabilityByProject data={stats.vulnerabilities_by_project} />
        </Box>
      </Box>
    </Box>
  );
};

export default DashboardPage;
