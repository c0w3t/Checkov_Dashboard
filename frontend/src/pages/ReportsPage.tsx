import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip
} from '@mui/material';
import { GetApp } from '@mui/icons-material';
import { scansApi, reportsApi } from '../services/api';
import { Scan } from '../types';

const ReportsPage: React.FC = () => {
  const [scans, setScans] = useState<Scan[]>([]);

  useEffect(() => {
    loadScans();
  }, []);

  const loadScans = async () => {
    try {
      const response = await scansApi.getAll();
      setScans(response.data.filter(s => s.status === 'completed'));
    } catch (error) {
      console.error('Failed to load scans:', error);
    }
  };

  const handleDownload = async (scanId: number) => {
    try {
      const response = await reportsApi.generatePDF(scanId);

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `scan_${scanId}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download report:', error);
      alert('Failed to generate PDF report. Please try again.');
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Reports</Typography>
      </Box>

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Export Options
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Generate comprehensive security reports in multiple formats
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Compliance Reports
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Track compliance with security policies over time
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Trend Analysis
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Analyze security trends and improvements
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h5" mb={2}>
        Available Reports
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Scan ID</TableCell>
              <TableCell>Project ID</TableCell>
              <TableCell>Completed</TableCell>
              <TableCell>Pass Rate</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {scans.map((scan) => {
              const passRate = scan.total_checks > 0
                ? ((scan.passed_checks / scan.total_checks) * 100).toFixed(1)
                : 0;

              return (
                <TableRow key={scan.id}>
                  <TableCell>#{scan.id}</TableCell>
                  <TableCell>{scan.project_id}</TableCell>
                  <TableCell>
                    {scan.completed_at
                      ? new Date(scan.completed_at).toLocaleString()
                      : 'N/A'}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={`${passRate}%`}
                      color={parseFloat(passRate as string) >= 80 ? 'success' : 'warning'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="contained"
                      color="primary"
                      size="small"
                      startIcon={<GetApp />}
                      onClick={() => handleDownload(scan.id)}
                    >
                      Download PDF
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default ReportsPage;
