import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  LinearProgress,
  Box,
  Typography
} from '@mui/material';
import { Visibility, GetApp } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { Scan } from '../../types';
import { formatDistanceToNow } from 'date-fns';

interface ScanHistoryProps {
  scans: Scan[];
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'failed':
      return 'error';
    case 'running':
      return 'info';
    case 'pending':
      return 'warning';
    default:
      return 'default';
  }
};

const ScanHistory: React.FC<ScanHistoryProps> = ({ scans }) => {
  const navigate = useNavigate();
  
  const calculatePassRate = (scan: Scan): number => {
    if (scan.total_checks === 0) return 0;
    return parseFloat(((scan.passed_checks / scan.total_checks) * 100).toFixed(1));
  };

  const handleViewScan = (scanId: number) => {
    navigate(`/scans/${scanId}`);
  };

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Scan ID</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Started</TableCell>
            <TableCell>Duration</TableCell>
            <TableCell>Pass Rate</TableCell>
            <TableCell>Checks</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {scans.map((scan) => (
            <TableRow key={scan.id}>
              <TableCell>#{scan.id}</TableCell>
              <TableCell>
                <Chip
                  label={scan.status}
                  color={getStatusColor(scan.status) as any}
                  size="small"
                />
              </TableCell>
              <TableCell>{scan.scan_type}</TableCell>
              <TableCell>
                {formatDistanceToNow(new Date(scan.started_at + 'Z'), { addSuffix: true })}
              </TableCell>
              <TableCell>
                {scan.completed_at
                  ? `${Math.round((new Date(scan.completed_at).getTime() - 
                      new Date(scan.started_at).getTime()) / 1000)}s`
                  : 'In progress...'}
              </TableCell>
              <TableCell>
                <Box display="flex" alignItems="center" gap={1}>
                  <LinearProgress
                    variant="determinate"
                    value={calculatePassRate(scan)}
                    sx={{ width: 100, height: 8, borderRadius: 4 }}
                    color={calculatePassRate(scan) >= 80 ? 'success' : 'warning'}
                  />
                  <Typography variant="body2">
                    {calculatePassRate(scan)}%
                  </Typography>
                </Box>
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="success.main">
                  ✓ {scan.passed_checks}
                </Typography>
                <Typography variant="body2" color="error.main">
                  ✗ {scan.failed_checks}
                </Typography>
              </TableCell>
              <TableCell>
                <IconButton size="small" onClick={() => handleViewScan(scan.id)}>
                  <Visibility />
                </IconButton>
                <IconButton size="small">
                  <GetApp />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default ScanHistory;
