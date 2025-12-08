import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  Divider,
  CircularProgress
} from '@mui/material';
import { GetApp } from '@mui/icons-material';
import { scansApi, vulnerabilitiesApi, reportsApi } from '../../services/api';
import { Scan, Vulnerability } from '../../types';
import VulnerabilityList from '../Vulnerabilities/VulnerabilityList';

const ScanDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [scan, setScan] = useState<Scan | null>(null);
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      loadScanDetail(parseInt(id));
    }
  }, [id]);

  const loadScanDetail = async (scanId: number) => {
    try {
      const [scanResponse, vulnResponse] = await Promise.all([
        scansApi.getById(scanId),
        vulnerabilitiesApi.getAll({ scan_id: scanId })
      ]);
      setScan(scanResponse.data);
      setVulnerabilities(vulnResponse.data);
    } catch (error) {
      console.error('Failed to load scan details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!scan) return;
    try {
      const response = await reportsApi.generatePDF(scan.id);
      
      // Handle download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `scan_${scan.id}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download report:', error);
      alert('Failed to generate PDF report. Please try again.');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!scan) {
    return <Typography>Scan not found</Typography>;
  }

  const passRate = scan.total_checks > 0 
    ? ((scan.passed_checks / scan.total_checks) * 100).toFixed(1)
    : 0;

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h4">Scan #{scan.id}</Typography>
            <Button
              variant="contained"
              color="primary"
              startIcon={<GetApp />}
              onClick={handleDownloadReport}
            >
              Download PDF Report
            </Button>
          </Box>

          <Chip 
            label={scan.status} 
            color={scan.status === 'completed' ? 'success' : 'warning'}
            sx={{ mb: 2 }}
          />

          <Divider sx={{ my: 2 }} />

          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" color="textSecondary">
                Started At
              </Typography>
              <Typography variant="body1">
                {new Date(scan.started_at).toLocaleString()}
              </Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" color="textSecondary">
                Completed At
              </Typography>
              <Typography variant="body1">
                {scan.completed_at 
                  ? new Date(scan.completed_at).toLocaleString()
                  : 'In progress...'}
              </Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" color="textSecondary">
                Pass Rate
              </Typography>
              <Typography variant="h5" color={parseFloat(passRate as string) >= 80 ? 'success.main' : 'warning.main'}>
                {passRate}%
              </Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" color="textSecondary">
                Total Checks
              </Typography>
              <Typography variant="h5">
                {scan.total_checks}
              </Typography>
            </Grid>
          </Grid>

          <Box mt={3}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Box textAlign="center" p={2} bgcolor="success.light" borderRadius={1}>
                  <Typography variant="h4" color="success.dark">
                    {scan.passed_checks}
                  </Typography>
                  <Typography variant="subtitle2">Passed</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box textAlign="center" p={2} bgcolor="error.light" borderRadius={1}>
                  <Typography variant="h4" color="error.dark">
                    {scan.failed_checks}
                  </Typography>
                  <Typography variant="subtitle2">Failed</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box textAlign="center" p={2} bgcolor="grey.300" borderRadius={1}>
                  <Typography variant="h4">
                    {scan.skipped_checks}
                  </Typography>
                  <Typography variant="subtitle2">Skipped</Typography>
                </Box>
              </Grid>
            </Grid>
          </Box>

          {scan.error_message && (
            <Box mt={2} p={2} bgcolor="error.light" borderRadius={1}>
              <Typography variant="subtitle2" color="error.dark">
                Error: {scan.error_message}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      <Typography variant="h5" sx={{ mb: 2 }}>
        Vulnerabilities
      </Typography>
      <VulnerabilityList vulnerabilities={vulnerabilities} />
    </Box>
  );
};

export default ScanDetail;
