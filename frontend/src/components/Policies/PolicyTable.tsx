import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Typography,
  Box,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import { Delete as DeleteIcon, Check as CheckIcon } from '@mui/icons-material';

interface Policy {
  check_id: string;
  name: string;
  platform: string;
  severity: string;
  built_in: boolean;
  category?: string;
  file_path?: string;
}

interface PolicyTableProps {
  policies: Policy[];
  loading: boolean;
  onDelete: (checkId: string, platform: string) => void;
}

const PolicyTable: React.FC<PolicyTableProps> = ({ policies, loading, onDelete }) => {
  const getPlatformColor = (platform: string) => {
    switch (platform) {
      case 'terraform':
        return 'primary';
      case 'kubernetes':
        return 'secondary';
      case 'dockerfile':
        return 'success';
      default:
        return 'default';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (policies.length === 0) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          No policies found
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Check ID</TableCell>
            <TableCell>Name</TableCell>
            <TableCell>Platform</TableCell>
            <TableCell>Severity</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Category</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {policies.map((policy) => (
            <TableRow key={policy.check_id} hover>
              <TableCell>
                <Typography variant="body2" fontWeight="bold" fontFamily="monospace">
                  {policy.check_id}
                </Typography>
              </TableCell>
              <TableCell>
                <Tooltip title={policy.name}>
                  <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                    {policy.name}
                  </Typography>
                </Tooltip>
              </TableCell>
              <TableCell>
                <Chip
                  label={policy.platform}
                  color={getPlatformColor(policy.platform)}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Chip
                  label={policy.severity.toUpperCase()}
                  color={getSeverityColor(policy.severity)}
                  size="small"
                />
              </TableCell>
              <TableCell>
                {policy.built_in ? (
                  <Chip
                    icon={<CheckIcon />}
                    label="Built-in"
                    color="default"
                    size="small"
                    variant="outlined"
                  />
                ) : (
                  <Chip label="Custom" color="primary" size="small" />
                )}
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="text.secondary">
                  {policy.category || '-'}
                </Typography>
              </TableCell>
              <TableCell align="right">
                {!policy.built_in && (
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => onDelete(policy.check_id, policy.platform)}
                  >
                    <DeleteIcon />
                  </IconButton>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default PolicyTable;
