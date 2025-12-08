import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Switch,
  Chip,
  Box,
  Typography,
  Tooltip,
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { PolicyConfig } from '../../types';

interface PolicyConfigListProps {
  policies: PolicyConfig[];
  onEdit: (policy: PolicyConfig) => void;
  onDelete: (id: number) => void;
  onToggle: (id: number, enabled: boolean) => void;
}

const PolicyConfigList: React.FC<PolicyConfigListProps> = ({
  policies,
  onEdit,
  onDelete,
  onToggle,
}) => {
  const getPolicyTypeColor = (type: string) => {
    switch (type) {
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

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'success';
      case 'info':
        return 'default';
      default:
        return 'default';
    }
  };

  if (policies.length === 0) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          No policy configurations found
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Add a new policy configuration to get started
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Check ID</TableCell>
            <TableCell>Policy Type</TableCell>
            <TableCell>Project ID</TableCell>
            <TableCell>Severity Override</TableCell>
            <TableCell>Custom Message</TableCell>
            <TableCell>Enabled</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {policies.map((policy) => (
            <TableRow key={policy.id}>
              <TableCell>
                <Typography variant="body2" fontWeight="bold">
                  {policy.check_id}
                </Typography>
              </TableCell>
              <TableCell>
                <Chip
                  label={policy.policy_type}
                  color={getPolicyTypeColor(policy.policy_type)}
                  size="small"
                />
              </TableCell>
              <TableCell>
                {policy.project_id ? (
                  <Chip label={`#${policy.project_id}`} size="small" />
                ) : (
                  <Chip label="Global" variant="outlined" size="small" />
                )}
              </TableCell>
              <TableCell>
                {policy.severity_override ? (
                  <Chip
                    label={policy.severity_override.toUpperCase()}
                    color={getSeverityColor(policy.severity_override)}
                    size="small"
                  />
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    -
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                {policy.custom_message ? (
                  <Tooltip title={policy.custom_message}>
                    <Typography
                      variant="body2"
                      noWrap
                      sx={{ maxWidth: 200 }}
                    >
                      {policy.custom_message}
                    </Typography>
                  </Tooltip>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    -
                  </Typography>
                )}
              </TableCell>
              <TableCell>
                <Switch
                  checked={policy.enabled}
                  onChange={(e) => onToggle(policy.id, e.target.checked)}
                  color="primary"
                />
              </TableCell>
              <TableCell align="right">
                <IconButton
                  size="small"
                  onClick={() => onEdit(policy)}
                  color="primary"
                >
                  <EditIcon />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={() => onDelete(policy.id)}
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default PolicyConfigList;
